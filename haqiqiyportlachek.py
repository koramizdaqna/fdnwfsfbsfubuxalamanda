import requests
from licensing.methods import Helpers
import csv
from urllib.parse import unquote
from datetime import datetime
import os
import asyncio
from telethon import utils, TelegramClient
from telethon.tl.functions.account import UpdateStatusRequest
from telethon.tl.types import InputUser
from telethon.tl.functions.messages import RequestAppWebViewRequest
from telethon.tl.types import InputBotAppShortName

def color(text, color_code):
    color_map = {
        "red": "91", "green": "92", "yellow": "93", "blue": "94",
        "magenta": "95", "cyan": "96", "white": "97", "bold_white": "1;97"
    }
    return f"\033[{color_map.get(color_code, '97')}m{text}\033[0m"

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

# 📄 Telefonlar ro‘yxati
with open('phone.csv', 'r') as f:
    phlist = [row[0] for row in csv.reader(f) if row]

if not phlist:
    print(color("📄 phone.csv bo'sh!", "red"))
    exit()

api_id = 22962676
api_hash = '543e9a4d695fe8c6aa4075c9525f7c57'

recipient_username = str(input("Yuboriladigan user kritiing: ( @cha siz) "))

async def process_phone(parsed_phone):
    print(color(f"📲 Foydalaniladigan raqam: {parsed_phone}", "green"))

    client = TelegramClient(f"sessions/{parsed_phone}", api_id, api_hash)
    await client.start(parsed_phone)
    await client(UpdateStatusRequest(offline=False))

    # 📟 bot va init_data olish
    bot_entity = await client.get_entity("@portals")
    bot = InputUser(user_id=bot_entity.id, access_hash=bot_entity.access_hash)
    bot_app = InputBotAppShortName(bot_id=bot, short_name="market")
    web_view = await client(RequestAppWebViewRequest(
        peer=bot, app=bot_app, platform="android",
        write_allowed=True, start_param="start"
    ))

    auth_url = web_view.url.replace('tgWebAppVersion=7.0', 'tgWebAppVersion=8.0')
    init_data = unquote(auth_url.split('tgWebAppData=', 1)[1].split('&tgWebAppVersion', 1)[0])

    headers = {
        "accept": "application/json",
        "authorization": f'tma {init_data}',
        "user-agent": "Mozilla/5.0"
    }

    # 🎨 NFT’larni olish
    r = requests.get(
        "https://portal-market.com/api/nfts/owned?offset=0&limit=500&status=unlisted&with_attributes=true",
        headers=headers,
        timeout=10
    )

    if r.status_code != 200:
        print(color(f"❌ Status: {r.status_code} - {r.text}", "red"))
        await client.disconnect()
        return

    data = r.json()
    nft_ids = []
    nft_names = []

    for nft in data.get("nfts", []):
        print(f"id: {nft['id']}")
        print(f"name: {nft['name']}")
        nft_ids.append(nft['id'])
        nft_names.append(nft['name'])

    print(f"total_count: {data.get('total_count', 0)}")

    if not nft_ids:
        print(color("🚫 NFT topilmadi!", "red"))
        await client.disconnect()
        return

    # 🎁 yuborish
    payload = {
        "nft_ids": nft_ids,
        "recipient": recipient_username,
        "anonymous": False
    }

    r = requests.post(
        "https://portals-market.com/api/nfts/transfer-gifts",
        headers=headers,
        json=payload,
        timeout=10
    )

    if r.status_code == 200:
        print(color(f"🎁 Barcha NFT yuborildi: {nft_ids}", "green"))
    else:
        print(color(f"❌ Yuborishda xatolik: {r.status_code} - {r.text}", "red"))

    await client.disconnect()

async def main():
    for phone in phlist:
        parsed_phone = utils.parse_phone(phone)
        try:
            await process_phone(parsed_phone)
        except Exception as e:
            print(color(f"⚠️ {phone} da xatolik: {e}", "red"))

asyncio.run(main())
