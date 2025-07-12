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

# Aktivatsiya tekshirish
url = "https://raw.githubusercontent.com/Enshteyn40/crdevice/refs/heads/main/portalhaqiqiy.csv"
machine_code = Helpers.GetMachineCode(v=2)
if machine_code not in requests.get(url).text.splitlines():
    print(colored(f"{machine_code}", "magenta"))
    print(colored("Kodni aktivlashtirish uchun @Enshteyn40 ga murojat qiling", "magenta"))
    sys.exit()
print(colored("✅ Kod aktiv. Oxirgi yangilanish: 13.07.2025", "magenta"))

# 📄 Fayllarni tekshirish va yaratish
def ensure_csv(filepath):
    if not os.path.isfile(filepath):
        print(f"📄 {os.path.basename(filepath)} topilmadi, yaratildi.")
        with open(filepath, 'w', encoding='utf-8'): pass

# 📄 Yo‘lni aniqlash
giv_path = '/storage/emulated/0/giv' if os.path.exists('/storage/emulated/0/giv') else 'C:\\join'
if not os.path.exists(giv_path): sys.exit("❌ Papka topilmadi")

# 📄 HAQIQIYPORTAL.csv
portal_csv = os.path.join(giv_path, 'HAQIQIYPORTAL.csv')
ensure_csv(portal_csv)
giv_ids_ozim = []
with open(portal_csv, 'r', encoding='utf-8') as f:
    for row in csv.reader(f):
        if not row: continue
        raw = row[0].strip()
        if not raw: continue

        # 🚀 Avval prefixlarni olib tashlash
        if raw.startswith("gwr_") or raw.startswith("gw_"):
            raw = raw.split("_", 1)[1]

        # 🚀 Endi xohlagan holda _ bo‘lsa — faqat 1-qismi olinadi
        if "_" in raw:
            real_id = raw.split("_", 1)[0]
        else:
            real_id = raw

        giv_ids_ozim.append(real_id)

print(colored(f"✅ HAQIQIYPORTAL.csv — {len(giv_ids_ozim)} ta ID o‘qildi", "blue"))

# 📄 HAQIQIYPORTALsoni.csv
portal_soni_csv = os.path.join(giv_path, 'HAQIQIYPORTALsoni.csv')
ensure_csv(portal_soni_csv)

with open(portal_soni_csv, 'r', encoding='utf-8') as f:
    rows = [r for r in csv.reader(f) if r]

if not rows:
    sys.exit("❌ HAQIQIYPORTALsoni.csv bo‘sh, raqam yo‘q.")

try:
    batch_size = int(rows[0][0])
    print(colored(f"✅ HAQIQIYPORTALsoni.csv — Bir vaqtda ishlaydigan raqamlar: {batch_size}", "blue"))
except ValueError:
    sys.exit("❌ HAQIQIYPORTALsoni.csv ichidagi qiymat raqam emas.")

with open('phone.csv', 'r') as f:
    phones = [r[0] for r in csv.reader(f) if r]

print(colored(f"📱 Telefonlar: {len(phones)}", "blue"))

def t_time(iso):
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return dt.astimezone(timezone(timedelta(hours=5))).strftime("%Y-%m-%d %H:%M:%S")

async def process_account(phone, idx):
    try:
        print(colored(f"[{idx}] Login: {phone}", "green"))
        parsed_phone = utils.parse_phone(phone)
        client = TelegramClient(f"sessions/{parsed_phone}", api_id, api_hash)
        await client.start(phone=parsed_phone)

        if not await client.is_user_authorized():
            print(colored(f"[{idx}] ❌ Sessiya yo‘q yoki login kerak!", "red"))
            await client.disconnect()
            return

        await client(UpdateStatusRequest(offline=False))

        for giveaway_code in giv_ids_ozim:
            bot_entity = await client.get_entity("@portals_market_bot")
            bot = InputUser(user_id=bot_entity.id, access_hash=bot_entity.access_hash)
            bot_app = InputBotAppShortName(bot_id=bot, short_name="market")
            web_view = await client(RequestAppWebViewRequest(
                peer=bot, app=bot_app, platform="android",
                write_allowed=True, start_param=giveaway_code
            ))
            auth_url = web_view.url.replace('tgWebAppVersion=7.0', 'tgWebAppVersion=8.0')
            init_data = unquote(auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])

            headers = {
                "accept": "application/json",
                "authorization": f'tma {init_data}',
                "referer": f"https://portals-market.com/giveaway/{giveaway_code}",
                "user-agent": "Mozilla/5.0"
            }

            # 📄 Giveaway details
            r = requests.get(f"https://portals-market.com/api/giveaways/{giveaway_code}", headers=headers, timeout=10)
            if r.status_code != 200:
                print(colored(f"[{giveaway_code}] ❌ Status: {r.status_code}", "red"))
                continue
            d = r.json()["details"]
            g = d["giveaway"]

            if g.get("status") != "active" or g.get("has_ended", False):
                print(colored("⛔ Giveaway aktiv emas yoki tugagan.", "red"))
                continue

            print(colored(f"🎯 Giveaway: {g['id']}", "cyan"))
            print(colored(f"⏳ Tugash (Toshkent): {t_time(g['ends_at'])}", "blue"))
            print(colored(f"🎁 Giftlar: {len(d['prizes'])}", "blue"))
            print(colored(f"💰 Floor price: {round(sum(float(p['nft_floor_price']) for p in d['prizes']),2)}", "blue"))
            print(colored(f"👥 Qatnashchilar: {d['participants_count']}", "blue"))

            # 📄 Requirements
            r = requests.get(f"https://portals-market.com/api/giveaways/{giveaway_code}/requirements", headers=headers, timeout=10)
            if r.status_code != 200: 
                print(colored(f"[{giveaway_code}] ❌ Status: {r.status_code}", "red"))
                print(colored("Giveaway skip qilinayabdi", "red"))
                continue
            req = r.json()

            if req["is_already_participating"]:
                print(colored("ℹ️ Allaqachon qatnashgan!", "yellow"))
            else:
                print(colored("🆕 Hali qatnashmagan!", "cyan"))

            # 📄 Kanallarga qo‘shilish
            for ch in req["requirements"]["channels"]:
                try:
                    await client(JoinChannelRequest(ch["username"]))
                    print(colored(f"➕ Kanal: {ch['username']}", "blue"))
                except Exception as e:
                    print(colored(f"❌ Kanal xatolik: {e}", "red"))

            # 📄 Join qilish
            requests.post(f"https://portals-market.com/api/giveaways/{giveaway_code}/join", headers=headers, timeout=10)

            # 📄 Tekshiruv
            req_after = requests.get(f"https://portals-market.com/api/giveaways/{giveaway_code}/requirements", headers=headers, timeout=10)
            if req_after.status_code == 200:
                req_a = req_after.json()
                if req_a.get("is_already_participating", False):
                    print(colored("🎉 Muvaffaqiyatli qatnashdi!", "green"))
                else:
                    print(colored("⚠️ Hali ham qatnashmagan!", "red"))

        await client.disconnect()

    except Exception as e:
        traceback.print_exc()
        print(colored(f"[{idx}] Xatolik: {e}", "red"))

async def main():
    batch = []
    for idx, phone in enumerate(phones, 1):
        batch.append(process_account(phone, idx))
        if len(batch) == batch_size:
            await asyncio.gather(*batch)
            batch = []
    if batch:
        await asyncio.gather(*batch)

if __name__ == '__main__':
    asyncio.run(main())
