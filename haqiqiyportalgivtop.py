# -*- coding: utf-8 -*-
import requests
from licensing.methods import Helpers
import csv
from urllib.parse import unquote
from telethon.sync import TelegramClient
from telethon.tl.functions.account import UpdateStatusRequest
from telethon.tl.types import InputUser
from telethon.tl.functions.messages import RequestAppWebViewRequest
from telethon.tl.types import InputBotAppShortName
from datetime import datetime

def color(text, color_code):
    color_map = {
        "red": "91", "green": "92", "yellow": "93", "blue": "94",
        "magenta": "95", "cyan": "96", "white": "97", "bold_white": "1;97"
    }
    return f"\033[{color_map.get(color_code,'97')}m{text}\033[0m"

def parse_time(iso_str):
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    return dt.strftime('%Y-%m-%d %H:%M:%S')

# 🔒 Aktivatsiya tekshirish
url = "https://raw.githubusercontent.com/Enshteyn40/crdevice/refs/heads/main/portalhaqiqiy.csv"
response = requests.get(url)
hash_values_list = [line.strip() for line in response.text.splitlines()]
machine_code = Helpers.GetMachineCode(v=2)
print(color(machine_code, "white"))

if machine_code not in hash_values_list:
    print(color("Kodni aktivlashtirish uchun @Enshteyn40 ga murojat qiling", "magenta"))
    exit()

print(color("✅ Oxirgi kod yangilangan vaqti: 14.06.2025 04:09 PM", "magenta"))

# 📌 Userdan boost, premium va kerakli sonni so‘rash
boost_input = input("Boostlik giveaway kerakmi? (ha/yoq): ").strip().lower()
premium_input = input("Premium giveaway kerakmi? (ha/yoq): ").strip().lower()
try:
    max_giveaways = int(input("Nechta giveaway qidiraylik? (son kiriting): ").strip())
except ValueError:
    print(color("❌ Raqam kiritilmadi!", "red"))
    exit()

want_boost = boost_input == 'ha'
want_premium = premium_input == 'ha'

print(color(f"Boost kerak: {want_boost}", "cyan"))
print(color(f"Premium kerak: {want_premium}", "cyan"))
print(color(f"Qidiriladigan giveawaylar soni: {max_giveaways}", "cyan"))

# 📱 1-chi raqamni olish
with open('phone.csv', 'r') as f:
    phlist = [row[0] for row in csv.reader(f) if row]

if not phlist:
    print(color("📄 phone.csv bo'sh!", "red"))
    exit()

phone = phlist[0]
print(color(f"📲 Foydalaniladigan raqam: {phone}", "green"))

api_id = 22962676
api_hash = '543e9a4d695fe8c6aa4075c9525f7c57'

client = TelegramClient(f"sessions/{phone}", api_id, api_hash)
client.start(phone)
client(UpdateStatusRequest(offline=False))

async def main():
    bot_entity = await client.get_entity("@portals")
    bot = InputUser(user_id=bot_entity.id, access_hash=bot_entity.access_hash)
    bot_app = InputBotAppShortName(bot_id=bot, short_name="market")
    web_view = await client(RequestAppWebViewRequest(
        peer=bot, app=bot_app, platform="android",
        write_allowed=True, start_param="start"
    ))

    auth_url = web_view.url.replace('tgWebAppVersion=7.0', 'tgWebAppVersion=8.0')
    init_data = unquote(auth_url.split('tgWebAppData=',1)[1].split('&tgWebAppVersion',1)[0])

    headers = {
        "accept": "application/json",
        "authorization": f'tma {init_data}',
        "user-agent": "Mozilla/5.0"
    }

    r = requests.get(f"https://portals-market.com/api/giveaways/?offset=0&limit=2000&status=active", headers=headers, timeout=10)
    if r.status_code != 200:
        print(color(f"❌ Status: {r.status_code}", "red"))
        return

    data = r.json()
    giveaways = data.get("giveaways", [])
    found_count = 0

    csv_filename = "portalhaqiqiygivlari.csv"
    with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "ID", "Participants", "Ends at", "Channels",
            "Prizes count", "Prize floor prices total"
        ])

        for g in giveaways:
            if g.get("status") != "active":
                continue

            if not want_boost and g.get("require_boost", False):
                continue
            if not want_premium and g.get("require_premium", False):
                continue

            found_count += 1

            gid = g.get("id")
            participants = g.get("participants_count", 0)
            ends_at = g.get("ends_at", "N/A")
            ends_at_parsed = parse_time(ends_at) if ends_at != "N/A" else "N/A"
            channels = [ch['username'] for ch in g.get("channels", [])]
            prizes_count = g.get("prizes_count", 0)
            floor_prices = [float(p['nft_floor_price']) for p in g.get("prizes", [])]
            floor_prices_total = round(sum(floor_prices), 2)

            # 📝 CSV ga yozish
            writer.writerow([
                gid,
                participants,
                ends_at_parsed,
                ", ".join(channels),
                prizes_count,
                floor_prices_total
            ])

            # Terminalga chiqarish
            print(color(f"🎯 ID: {gid}", "cyan"))
            print(f"👥 Participants: {participants}")
            print(f"⏳ Ends at: {ends_at_parsed}")
            print(f"📺 Channels: {channels}")
            print(f"🎁 Prizes count: {prizes_count}")
            print(f"💰 Prize floor prices total: {floor_prices_total}")
            print("-" * 50)

            if found_count >= max_giveaways:
                break

    print(color(f"🔷 Topilgan mos giveawaylar soni: {found_count}", "green"))
    print(color(f"📄 Giveawaylar saqlandi: {csv_filename}", "green"))

with client:
    client.loop.run_until_complete(main())
