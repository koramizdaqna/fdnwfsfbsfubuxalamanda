# -*- coding: utf-8 -*-
import asyncio, csv, os, sys, requests
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

# aktivatsiya tekshirish
url = "https://raw.githubusercontent.com/Enshteyn40/crdevice/refs/heads/main/portalhaqiqiy.csv"
machine_code = Helpers.GetMachineCode(v=2)
if machine_code not in requests.get(url).text.splitlines():
    print(colored(f"{machine_code}", "magenta"))
    print(colored(f"{machine_code} Kodni aktivlashtirish uchun @Enshteyn40 ga murojat qiling", "magenta"))
    sys.exit()

print(colored("✅ Kod aktiv. Oxirgi yangilanish: 23.05.2025 8:28 PM", "magenta"))

# 📄 fayllarni tekshirish va yaratish
def ensure_csv(filepath):
    """CSV fayl mavjud bo‘lmasa, bo‘sh yaratadi"""
    if not os.path.isfile(filepath):
        print(f"📄 {os.path.basename(filepath)} topilmadi, yaratildi.")
        with open(filepath, 'w', encoding='utf-8'): pass

# 📄 yo‘lni aniqlash
giv_path = '/storage/emulated/0/giv' if os.path.exists('/storage/emulated/0/giv') else 'C:\\join'
if not os.path.exists(giv_path): sys.exit("❌ Papka topilmadi")

# 📄 HAQIQIYPORTAL.csv
portal_csv = os.path.join(giv_path, 'HAQIQIYPORTAL.csv')
ensure_csv(portal_csv)

with open(portal_csv, 'r', encoding='utf-8') as f:
    giv_ids_ozim = [r[0] for r in csv.reader(f) if r]

print(colored(f"✅ HAQIQIYPORTAL.csv — {len(giv_ids_ozim)} ta id", "blue"))

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
        await client(UpdateStatusRequest(offline=False))

        for giveaway_code in giv_ids_ozim:
            bot_entity = await client.get_entity("@portals_market_bot")
            bot = InputUser(user_id=bot_entity.id, access_hash=bot_entity.access_hash)
            bot_app = InputBotAppShortName(bot_id=bot, short_name="market")
            web_view = await client(RequestAppWebViewRequest(
                peer=bot, app=bot_app, platform="android",
                write_allowed=True, start_param="1062643042"
            ))
            auth_url = web_view.url.replace('tgWebAppVersion=7.0', 'tgWebAppVersion=8.0')
            init_data = unquote(auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])

            headers = {
                "accept": "application/json",
                "authorization": f'tma {init_data}',
                "referer": f"https://portals-market.com/giveaway/{giveaway_code}",
                "user-agent": "Mozilla/5.0"
            }

            # 🔷 details
            r = requests.get(f"https://portals-market.com/api/giveaways/{giveaway_code}", headers=headers, timeout=10)
            if r.status_code != 200: continue
            d = r.json()["details"]
            g = d["giveaway"]

            if g.get("status") != "active" or g.get("has_ended", False):
                print(colored("⛔ Giveaway aktiv emas yoki tugagan.", "red"))
                continue

            print(colored(f"🎯 Giveaway: {g['id']}", "cyan"))
            print(colored(f"⏳ Tugash (Toshkent): {t_time(g['ends_at'])}", "blue"))
            print(colored(f"🎁 Giftlar: {len(d['prizes'])}", "blue"))
            print(colored(f"💰 Jami floor price: {round(sum(float(p['nft_floor_price']) for p in d['prizes']),2)}", "blue"))
            print(colored(f"👥 Qatnashchilar: {d['participants_count']}", "blue"))

            # 🔷 requirements
            r = requests.get(f"https://portals-market.com/api/giveaways/{giveaway_code}/requirements", headers=headers, timeout=10)
            if r.status_code != 200: continue
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

            # 🔷 join
            join_r = requests.post(f"https://portals-market.com/api/giveaways/{giveaway_code}/join", headers=headers, timeout=10)

            # 🔷 tekshiruvlar
            req_after = requests.get(f"https://portals-market.com/api/giveaways/{giveaway_code}/requirements", headers=headers, timeout=10)
            det_after = requests.get(f"https://portals-market.com/api/giveaways/{giveaway_code}", headers=headers, timeout=10)

            if req_after.status_code == 200:
                req_a = req_after.json()
                if req_a.get("is_already_participating", False):
                    print(colored("🎉 Muvaffaqiyatli qatnashdi!", "green"))
                else:
                    print(colored("⚠️ Hali ham qatnashmagan!", "red"))

            if det_after.status_code == 200:
                d = det_after.json()["details"]
                g = d["giveaway"]
                print(colored(f"🔄 Yangilangan:", "magenta"))
                print(colored(f"⏳ Tugash (Toshkent): {t_time(g['ends_at'])}", "blue"))
                print(colored(f"🎁 Giftlar: {len(d['prizes'])}", "blue"))
                print(colored(f"💰 Floor price: {round(sum(float(p['nft_floor_price']) for p in d['prizes']),2)}", "blue"))
                print(colored(f"👥 Qatnashchilar: {d['participants_count']}", "blue"))

        await client.disconnect()

    except Exception as e:
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
