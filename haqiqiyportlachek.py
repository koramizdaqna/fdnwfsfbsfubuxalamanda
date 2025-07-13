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
import os
import asyncio
from telethon import utils, TelegramClient

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

with open('phone.csv', 'r') as f:
    phlist = [row[0] for row in csv.reader(f) if row]

if not phlist:
    print(color("📄 phone.csv bo'sh!", "red"))
    exit()

api_id = 22962676
api_hash = '543e9a4d695fe8c6aa4075c9525f7c57'

winners_filename = "portalhaqiqiyyutgani.csv"

if not os.path.exists(winners_filename):
    with open(winners_filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Phone", "Jami Floor Price", "NFT Nomi/Nomlari"])

async def process_phone(parsed_phone):
    print(color(f"📲 Foydalaniladigan raqam: {parsed_phone}", "green"))

    client = TelegramClient(f"sessions/{parsed_phone}", api_id, api_hash)
    await client.start(parsed_phone)
    await client(UpdateStatusRequest(offline=False))

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
    r = requests.get(
        "https://portals-market.com/api/nfts/owned?offset=0&limit=2000&status=unlisted",
        headers=headers,
        timeout=10
    )

    if r.status_code != 200:
        print(color(f"❌ Status: {r.status_code}", "red"))
        return

    data = r.json()
    count = data.get("total_count", 0)

    if count == 0:
        print("🎁 Giftlar soni: 0")
    else:
        nft_names = []
        floor_total = 0.0

        print("🎁 NFTlar:")
        for nft in data.get("nfts", []):
            name = nft.get("name", "Noma'lum")
            floor_price = nft.get("floor_price")
            nft_names.append(name)

            try:
                if floor_price is not None:
                    floor_total += float(floor_price)
            except Exception as e:
                print(color(f"⚠️ Floor price konvertatsiyada xatolik: {e}", "red"))

            print(f"📦 {name} — Floor price: {floor_price}")

        print(f"🎁 Jami giftlar: {count}")
        print(f"💰 Jami floor price: {floor_total}")
        print(f"📜 NFTlar: {', '.join(nft_names)}")

        # Yutgan raqamlarni batafsil yozib qo'yish
        with open(winners_filename, "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([parsed_phone, floor_total, ", ".join(nft_names)])

    await client.disconnect()

async def main():
    for phone in phlist:
        parsed_phone = utils.parse_phone(phone)
        try:
            await process_phone(parsed_phone)
        except Exception as e:
            print(color(f"⚠️ {phone} da xatolik: {e}", "red"))

asyncio.run(main())
