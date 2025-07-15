# -*- coding: utf-8 -*-
import asyncio, csv, os, sys, requests, traceback
from urllib.parse import unquote
from licensing.methods import Helpers
from termcolor import colored
from telethon import utils, TelegramClient
from telethon.tl.functions.account import UpdateStatusRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import RequestAppWebViewRequest
from telethon.tl.types import InputUser, InputBotAppShortName
from datetime import datetime, timezone, timedelta

api_id = 22962676
api_hash = '543e9a4d695fe8c6aa4075c9525f7c57'

url = "https://raw.githubusercontent.com/Enshteyn40/crdevice/refs/heads/main/portalhaqiqiy.csv"
machine_code = Helpers.GetMachineCode(v=2)
if machine_code not in requests.get(url).text.splitlines():
    print(colored(f"{machine_code}", "magenta"))
    print(colored("Kodni aktivlashtirish uchun @Enshteyn40 ga murojat qiling", "magenta"))
    sys.exit()
print(colored("✅ Kod aktiv. Oxirgi yangilanish: 13.07.2025", "magenta"))

def ensure_csv(filepath):
    if not os.path.isfile(filepath):
        with open(filepath, 'w', encoding='utf-8'): pass

giv_path = '/storage/emulated/0/giv' if os.path.exists('/storage/emulated/0/giv') else 'C:\\join'
if not os.path.exists(giv_path): sys.exit("❌ Papka topilmadi")

log_dir = os.path.join(giv_path, "haqiqiyportal")
os.makedirs(log_dir, exist_ok=True)

def extract_giveaway_code(giveawayid: str) -> str:
    if '_' in giveawayid:
        parts = giveawayid.split('_')
        for p in parts:
            if '-' in p:
                return p
    return giveawayid

def t_time(iso):
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return dt.astimezone(timezone(timedelta(hours=5))).strftime("%Y-%m-%d %H:%M:%S")

portal_csv = os.path.join(giv_path, 'HAQIQIYPORTAL.csv')
ensure_csv(portal_csv)

giv_ids_ozim = []
with open(portal_csv, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    for row in reader:
        if not row: continue
        gid, mode = row[0].strip(), row[1].strip() if len(row) > 1 else 'refsiz'
        gid = extract_giveaway_code(gid)
        giv_ids_ozim.append((gid, mode))

print(colored(f"✅ HAQIQIYPORTAL.csv — {len(giv_ids_ozim)} ta ID o‘qildi", "blue"))

portal_soni_csv = os.path.join(giv_path, 'HAQIQIYPORTALsoni.csv')
ensure_csv(portal_soni_csv)

with open(portal_soni_csv, 'r', encoding='utf-8') as f:
    rows = [r for r in csv.reader(f) if r]

if not rows: sys.exit("❌ HAQIQIYPORTALsoni.csv bo‘sh.")
try:
    batch_size = int(rows[0][0])
    print(colored(f"✅ Bir vaqtda ishlaydigan raqamlar: {batch_size}", "blue"))
except ValueError:
    sys.exit("❌ HAQIQIYPORTALsoni.csv ichidagi qiymat raqam emas.")

with open('phone.csv', 'r') as f:
    phones = [r[0] for r in csv.reader(f) if r]

print(colored(f"📱 Telefonlar: {len(phones)}", "blue"))

group_tracker = {}

async def process_phone(phone, idx):
    try:
        print(colored(f"[{idx}] Login: {phone}", "green"))
        parsed_phone = utils.parse_phone(phone)
        client = TelegramClient(f"sessions/{parsed_phone}", api_id, api_hash)
        await client.start(phone=parsed_phone)

        if not await client.is_user_authorized():
            print(colored(f"[{idx}] ❌ Sessiya yo‘q!", "red"))
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

            if mode == 'refsiz':
                start_param = giveaway_code
            elif mode == 'all':
                start_param = giveaway_code
            else:
                try:
                    n = int(mode)
                    group_idx = (idx - 1) // n
                    if giveaway_code not in group_tracker or group_tracker[giveaway_code][0] != group_idx:
                        me = await client.get_me()
                        group_tracker[giveaway_code] = (group_idx, me.id)
                    current_me_id = group_tracker[giveaway_code][1]
                    start_param = f"gwr_{giveaway_code}_{current_me_id}"
                except ValueError:
                    start_param = giveaway_code

            print(colored(f"[{idx}] start_param={start_param} (mode={mode})", "cyan"))

            bot_entity = await client.get_entity("@portals_market_bot")
            bot = InputUser(user_id=bot_entity.id, access_hash=bot_entity.access_hash)
            bot_app = InputBotAppShortName(bot_id=bot, short_name="market")
            web_view = await client(RequestAppWebViewRequest(
                peer=bot, app=bot_app, platform="android",
                write_allowed=True, start_param=start_param
            ))

            auth_url = web_view.url.replace('tgWebAppVersion=7.0', 'tgWebAppVersion=8.0')
            init_data = unquote(auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])

            headers = {
                "accept": "application/json",
                "authorization": f'tma {init_data}',
                "referer": f"https://portals-market.com/giveaway/{giveaway_code}",
                "user-agent": "Mozilla/5.0"
            }

            r = requests.get(f"https://portals-market.com/api/giveaways/{giveaway_code}", headers=headers, timeout=10)
            if r.status_code != 200:
                print(colored(f"[{giveaway_code}] ❌ Status: {r.status_code}", "red"))
                continue

            data = r.json()
            d = data["details"]
            g = d["giveaway"]

            if g.get("status") != "active" or g.get("has_ended", False):
                print(colored("⛔ Giveaway aktiv emas.", "red"))
                continue

            r = requests.get(f"https://portals-market.com/api/giveaways/{giveaway_code}/requirements", headers=headers, timeout=10)
            if r.status_code != 200:
                print(colored(f"[{giveaway_code}] ❌ Status: {r.status_code}", "red"))
                continue

            req = r.json()

            if req["is_already_participating"]:
                print(colored("ℹ️ Allaqachon qatnashgan!", "yellow"))
            else:
                print(colored("🆕 Hali qatnashmagan!", "cyan"))
                for ch in req["requirements"]["channels"]:
                    try:
                        await client(JoinChannelRequest(ch["username"]))
                        print(colored(f"➕ Kanal: {ch['username']}", "blue"))
                    except Exception as e:
                        print(colored(f"❌ Kanal xatolik: {e}", "red"))

                requests.post(f"https://portals-market.com/api/giveaways/{giveaway_code}/join", headers=headers, timeout=10)

                req_after = requests.get(f"https://portals-market.com/api/giveaways/{giveaway_code}/requirements", headers=headers, timeout=10)
                if req_after.status_code == 200:
                    req_a = req_after.json()
                    if req_a.get("is_already_participating", False):
                        print(colored("🎉 Muvaffaqiyatli qatnashdi!", "green"))
                        first_row_needed = not os.path.isfile(csv_path)
                        with open(csv_path, 'a', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            if first_row_needed:
                                channels = ", ".join(c["username"] for c in req["requirements"]["channels"])
                                writer.writerow([f"Tugash: {t_time(g['ends_at'])}", f"Kanallar: {channels}"])
                            writer.writerow([phone])

        await client.disconnect()

    except Exception as e:
        traceback.print_exc()
        print(colored(f"[{idx}] Xatolik: {e}", "red"))

async def main():
    batch = []
    for idx, phone in enumerate(phones, 1):
        batch.append(process_phone(phone, idx))
        if len(batch) == batch_size:
            await asyncio.gather(*batch)
            batch = []

    if batch:
        await asyncio.gather(*batch)


if __name__ == '__main__':
    asyncio.run(main())
