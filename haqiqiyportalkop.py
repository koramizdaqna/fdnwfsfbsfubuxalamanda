# -*- coding: utf-8 -*-
import asyncio, csv, os, sys, requests, traceback, json
from urllib.parse import unquote
from licensing.methods import Helpers
from termcolor import colored
from telethon import utils, TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.account import UpdateStatusRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import RequestAppWebViewRequest
from telethon.tl.types import InputUser, InputBotAppShortName
from datetime import datetime, timezone, timedelta
import aiohttp
import aiohttp_proxy

# ========== TELEGRAM API ==========
api_id = 22962676
api_hash = '543e9a4d695fe8c6aa4075c9525f7c57'

# ========== LITSENZIYA ==========
url = "https://raw.githubusercontent.com/Enshteyn40/crdevice/refs/heads/main/portalhaqiqiy.csv"
machine_code = Helpers.GetMachineCode(v=2)
if machine_code not in requests.get(url).text.splitlines():
    print(colored(f"{machine_code}", "magenta"))
    print(colored("Kodni aktivlashtirish uchun @Enshteyn40 ga murojat qiling", "magenta"))
    sys.exit()
print(colored("✅ Kod aktiv. Oxirgi yangilanish: 16.07.2025 04:23 AM", "magenta"))

# ========== UTIL ==========
def ensure_csv(filepath):
    if not os.path.isfile(filepath):
        with open(filepath, 'w', encoding='utf-8'):
            pass

def t_time(iso: str) -> str:
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return dt.astimezone(timezone(timedelta(hours=5))).strftime("%Y-%m-%d %H:%M:%S")

def extract_giveaway_code(giveawayid: str) -> str:
    if '_' in giveawayid:
        parts = giveawayid.split('_')
        for p in parts:
            if '-' in p:
                return p
    return giveawayid

def load_accounts(json_path: str):
    """
    accounts.json formati:
    [
      {"phone": "99890xxxxxxx", "string": "<TELETHON_STRING_SESSION>"},
      {"phone": "99893yyyyyyy", "string": "<STRING>"},
      ...
    ]
    Yoki dict ko'rinishida: {"99890...": "<STRING>", "99893...": "<STRING>"}
    """
    if not os.path.isfile(json_path):
        sys.exit("❌ accounts.json topilmadi.")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    accounts = []
    if isinstance(data, list):
        for i, item in enumerate(data, 1):
            if not isinstance(item, dict) or "phone" not in item or "string" not in item:
                sys.exit(f"❌ accounts.json {i}-element formati noto‘g‘ri. Kerakli kalitlar: phone, string")
            phone = str(item["phone"]).strip()
            sess  = str(item["string"]).strip()
            if not phone or not sess:
                sys.exit(f"❌ accounts.json {i}-elementida bo‘sh phone/string bor.")
            accounts.append((phone, sess))
    elif isinstance(data, dict):
        for phone, sess in data.items():
            phone = str(phone).strip()
            sess  = str(sess).strip()
            if not phone or not sess:
                sys.exit("❌ accounts.json da bo‘sh phone/string bor.")
            accounts.append((phone, sess))
    else:
        sys.exit("❌ accounts.json noto‘g‘ri format. List yoki dict bo‘lishi kerak.")
    return accounts

# ========== YO‘L/PAPKA ==========
giv_path = '/storage/emulated/0/giv' if os.path.exists('/storage/emulated/0/giv') else r'C:\join'
if not os.path.exists(giv_path):
    sys.exit("❌ Papka topilmadi")

log_dir = os.path.join(giv_path, "haqiqiyportal")
os.makedirs(log_dir, exist_ok=True)

# ========== PROXY O‘QISH ==========
file_path_1 = r"C:\join\proxy.csv"
file_path_2 = r"/storage/emulated/0/giv/proxy.csv"

if os.path.exists(file_path_1):
    with open(file_path_1, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        ROTATED_PROXY = next(reader)[0]
elif os.path.exists(file_path_2):
    with open(file_path_2, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        ROTATED_PROXY = next(reader)[0]
else:
    raise FileNotFoundError("Hech qaysi proxy.csv fayli topilmadi.")

PROXY = ROTATED_PROXY

# ========== GIVEAWAY RO‘YXATI ==========
portal_csv = os.path.join(giv_path, 'HAQIQIYPORTAL.csv')
ensure_csv(portal_csv)

giv_ids_ozim = []
with open(portal_csv, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    for row in reader:
        if not row:
            continue
        gid, mode = row[0].strip(), row[1].strip() if len(row) > 1 else 'refsiz'
        gid = extract_giveaway_code(gid)
        giv_ids_ozim.append((gid, mode))

print(colored(f"✅ HAQIQIYPORTAL.csv — {len(giv_ids_ozim)} ta ID o‘qildi", "blue"))

# ========== BATCH SIZE ==========
portal_soni_csv = os.path.join(giv_path, 'HAQIQIYPORTALsoni.csv')
ensure_csv(portal_soni_csv)

with open(portal_soni_csv, 'r', encoding='utf-8') as f:
    rows = [r for r in csv.reader(f) if r]

if not rows:
    sys.exit("❌ HAQIQIYPORTALsoni.csv bo‘sh.")
try:
    batch_size = int(rows[0][0])
    if batch_size <= 0:
        raise ValueError
    print(colored(f"✅ Bir vaqtda ishlaydigan raqamlar: {batch_size}", "blue"))
except ValueError:
    sys.exit("❌ HAQIQIYPORTALsoni.csv ichidagi qiymat musbat butun son bo‘lishi kerak.")

# ========== ACCOUNTS.JSON ==========
ACCOUNTS_JSON = "accounts.json"
accounts = load_accounts(ACCOUNTS_JSON)
print(colored(f"📱 Akkountlar: {len(accounts)}", "blue"))

# mode=son bo‘yicha refer guruhlashni saqlash
group_tracker = {}  # {giveaway_code: {group_idx: me.id}}

async def process_account(phone: str, session_str: str, idx: int):
    try:
        print(colored(f"[{idx}] Login (StringSession): {phone}", "green"))

        # StringSession bilan TelegramClient
        client = TelegramClient(StringSession(session_str), api_id, api_hash)
        await client.connect()

        # StringSession noto‘g‘ri/yaroqsiz bo‘lsa authorized False bo‘ladi
        if not await client.is_user_authorized():
            print(colored(f"[{idx}] ❌ StringSession yaroqsiz yoki muddati o‘tgan!", "red"))
            await client.disconnect()
            return

        await client(UpdateStatusRequest(offline=False))

        for giveaway_code, mode in giv_ids_ozim:
            csv_path = os.path.join(log_dir, f"{giveaway_code}.csv")
            skipped_phones = set()

            if os.path.isfile(csv_path):
                with open(csv_path, 'r', encoding='utf-8') as f:
                    skipped_phones = {row[0] for i, row in enumerate(csv.reader(f)) if i > 0 and row}

            if phone in skipped_phones:
                print(colored(f"[{idx}] 🔷 {phone} allaqachon {giveaway_code} uchun qatnashgan, SKIP", "yellow"))
                continue

            # start_param tayyorlash
            if mode == 'refsiz':
                start_param = giveaway_code
            elif mode == 'all':
                all_ref_path = os.path.join(giv_path, 'haqiqiyportalhammagaref.csv')

                if not os.path.isfile(all_ref_path):
                    with open(all_ref_path, 'w', encoding='utf-8'):
                        pass
                    sys.exit(colored("❌ haqiqiyportalhammagaref.csv yaratildi, ammo bo‘sh. To‘ldirib qayta ishga tushiring!", "red"))

                with open(all_ref_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()

                if not first_line:
                    sys.exit(colored("❌ haqiqiyportalhammagaref.csv bo‘sh! To‘ldirib qayta ishga tushiring.", "red"))

                all_user_id = first_line
                print(colored(f"📄 haqiqiyportalhammagaref.csv dan o‘qildi: {all_user_id}", "cyan"))

                start_param = f"gwr_{giveaway_code}_{all_user_id}"
            else:
                # agar mode son bo‘lsa — n/ guruh
                try:
                    n = int(mode)
                    group_idx = (idx - 1) // n

                    if giveaway_code not in group_tracker:
                        group_tracker[giveaway_code] = {}

                    if group_idx not in group_tracker[giveaway_code]:
                        # faqat birinchi marta shu guruhga user id olamiz
                        me = await client.get_me()
                        group_tracker[giveaway_code][group_idx] = me.id

                    current_me_id = group_tracker[giveaway_code][group_idx]
                    start_param = f"gwr_{giveaway_code}_{current_me_id}"
                except ValueError:
                    # mode noma'lum — default
                    start_param = giveaway_code

            print(colored(f"[{idx}] start_param={start_param} (mode={mode})", "cyan"))

            # bot entity/app
            bot_entity = await client.get_entity("@portals_market_bot")
            bot = InputUser(user_id=bot_entity.id, access_hash=bot_entity.access_hash)
            bot_app = InputBotAppShortName(bot_id=bot, short_name="market")

            web_view = await client(RequestAppWebViewRequest(
                peer=bot,
                app=bot_app,
                platform="android",
                write_allowed=True,
                start_param=start_param
            ))

            auth_url = web_view.url.replace('tgWebAppVersion=7.0', 'tgWebAppVersion=8.0')
            init_data = unquote(auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])

            conn = aiohttp_proxy.ProxyConnector.from_url(PROXY)
            async with aiohttp.ClientSession(connector=conn) as http_client:
                headers = {
                    "accept": "application/json",
                    "authorization": f'tma {init_data}',
                    "referer": f"https://portal-market.com/giveaway/{giveaway_code}",
                    "user-agent": "Mozilla/5.0"
                }

                # ------ GET giveaway details ------
                async with http_client.get(
                    f"https://portal-market.com/api/giveaways/{giveaway_code}",
                    headers=headers, timeout=10
                ) as r:
                    if r.status != 200:
                        print(colored(f"[{giveaway_code}] ❌ Status: {r.status}", "red"))
                        continue
                    data = await r.json()

                d = data["details"]
                g = d["giveaway"]

                if g.get("status") != "active" or g.get("has_ended", False):
                    print(colored("⛔ Giveaway aktiv emas.", "red"))
                    continue

                # ------ GET requirements ------
                async with http_client.get(
                    f"https://portal-market.com/api/giveaways/{giveaway_code}/requirements",
                    headers=headers, timeout=10
                ) as r:
                    if r.status != 200:
                        print(colored(f"[{giveaway_code}] ❌ Status: {r.status}", "red"))
                        continue
                    req = await r.json()

                if req.get("is_already_participating"):
                    print(colored("ℹ️ Allaqachon qatnashgan!", "yellow"))
                else:
                    print(colored("🆕 Hali qatnashmagan!", "cyan"))
                    for ch in req["requirements"]["channels"]:
                        try:
                            await client(JoinChannelRequest(ch["username"]))
                            print(colored(f"➕ Kanal: {ch['username']}", "blue"))
                        except Exception as e:
                            print(colored(f"❌ Kanal xatolik: {e}", "red"))

                    # ------ POST join ------
                    async with http_client.post(
                        f"https://portal-market.com/api/giveaways/{giveaway_code}/join",
                        headers=headers, timeout=10
                    ) as r:
                        if r.status != 204:
                            print(colored(f"[{giveaway_code}] ❌ Status: {r.status}", "red"))
                        else:
                            print(colored("✅ Qatnashish so'rovi yuborildi", "green"))

                    # ------ Re-check requirements ------
                    async with http_client.get(
                        f"https://portal-market.com/api/giveaways/{giveaway_code}/requirements",
                        headers=headers, timeout=10
                    ) as r:
                        if r.status == 200:
                            req_a = await r.json()
                            if req_a.get("is_already_participating", False):
                                print(colored("🎉 Muvaffaqiyatli qatnashdi!", "green"))
                                first_row_needed = not os.path.isfile(csv_path)
                                with open(csv_path, 'a', newline='', encoding='utf-8') as f:
                                    writer = csv.writer(f)
                                    if first_row_needed:
                                        channels = ", ".join(c["username"] for c in req["requirements"]["channels"])
                                        writer.writerow([f"Tugash: {t_time(g['ends_at'])}", f"Kanallar: {channels}"])
                                    writer.writerow([phone])
                        else:
                            print(colored("⚠️ Qatnashganini tekshirishda xatolik", "yellow"))

        await client.disconnect()

    except Exception as e:
        traceback.print_exc()
        print(colored(f"[{idx}] Xatolik: {e}", "red"))

async def main():
    batch = []
    for idx, (phone, session_str) in enumerate(accounts, 1):
        batch.append(process_account(phone, session_str, idx))
        if len(batch) >= batch_size:
            await asyncio.gather(*batch)
            batch = []
    if batch:
        await asyncio.gather(*batch)

if __name__ == '__main__':
    asyncio.run(main())
