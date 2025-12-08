# -*- coding: utf-8 -*-
import requests
from licensing.methods import Helpers
import json
from urllib.parse import unquote
from datetime import datetime
import os
import asyncio
from termcolor import colored  # ixtiyoriy: ekranga rangli chiqarish uchun
from telethon import TelegramClient, utils
from telethon.sessions import StringSession
from telethon.tl.functions.account import UpdateStatusRequest
from telethon.tl.types import InputUser
from telethon.tl.functions.messages import RequestAppWebViewRequest
from telethon.tl.types import InputBotAppShortName

# --------- Rangli konsol (ixtiyoriy) ---------
def color(text, color_code):
    color_map = {
        "red": "91", "green": "92", "yellow": "93", "blue": "94",
        "magenta": "95", "cyan": "96", "white": "97", "bold_white": "1;97"
    }
    return f"\033[{color_map.get(color_code, '97')}m{text}\033[0m"

# --------- Aktivatsiya tekshirish ---------
url = "https://raw.githubusercontent.com/Enshteyn40/crdevice/refs/heads/main/portalhaqiqiy.csv"
response = requests.get(url, timeout=15)
hash_values_list = [line.strip() for line in response.text.splitlines()]
machine_code = Helpers.GetMachineCode(v=2)
print(color(machine_code, "white"))

if machine_code not in hash_values_list:
    print(color("Kodni aktivlashtirish uchun @Enshteyn40 ga murojat qiling", "magenta"))
    raise SystemExit

print(color("✅ Oxirgi kod yangilangan vaqti: 14.06.2025 04:09 PM", "magenta"))

# --------- Telegram API ---------
api_id = 22962676
api_hash = '543e9a4d695fe8c6aa4075c9525f7c57'

# --------- accounts.json o‘qish ---------
ACCOUNTS_JSON = "accounts.json"

def load_accounts(json_path: str):
    """
    Qo‘llab-quvvatlanadigan formatlar:
    1) Dict: {"99890...": "<STRING_SESSION>", "99891...": "<STRING_SESSION>", ...}
    2) List: [{"phone":"99890...","string":"<STRING_SESSION>"}, ...]
    """
    if not os.path.isfile(json_path):
        raise SystemExit("❌ accounts.json topilmadi.")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    accounts = []
    if isinstance(data, dict):
        for phone, sess in data.items():
            phone = str(phone).strip()
            sess = str(sess).strip()
            if not phone or not sess:
                raise SystemExit("❌ accounts.json ichida bo‘sh phone/string bor.")
            accounts.append((phone, sess))
    elif isinstance(data, list):
        for i, item in enumerate(data, 1):
            if not isinstance(item, dict) or "phone" not in item or "string" not in item:
                raise SystemExit(f"❌ accounts.json {i}-element formati noto‘g‘ri. Kerakli kalitlar: phone, string")
            phone = str(item["phone"]).strip()
            sess  = str(item["string"]).strip()
            if not phone or not sess:
                raise SystemExit(f"❌ accounts.json {i}-elementida bo‘sh phone/string bor.")
            accounts.append((phone, sess))
    else:
        raise SystemExit("❌ accounts.json noto‘g‘ri format. Dict yoki List bo‘lishi kerak.")
    return accounts

accounts = load_accounts(ACCOUNTS_JSON)
print(color(f"📱 Akkountlar: {len(accounts)}", "blue"))

# --------- Qabul qiluvchi username ---------
recipient_username = str(input("Yuboriladigan user kiriting ( @sizmas, faqat username ): ")).strip()
if recipient_username.startswith("@"):
    recipient_username = recipient_username[1:]

# --------- Bitta akkauntni qayta ishlash ---------
async def process_account(phone: str, string_session: str, idx: int):
    print(color(f"[{idx}] 📲 Foydalaniladigan raqam: {phone}", "green"))

    client = TelegramClient(StringSession(string_session), api_id, api_hash)
    await client.connect()

    if not await client.is_user_authorized():
        print(color(f"[{idx}] ❌ StringSession yaroqsiz yoki muddati o‘tgan!", "red"))
        await client.disconnect()
        return

    await client(UpdateStatusRequest(offline=False))

    try:
        # Bot va init_data olish
        # Eslatma: original kodingizda "@portals" yozilgan. Market WebApp odatda "@portals_market_bot".
        bot_entity = await client.get_entity("@portals_market_bot")
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
            "authorization": f"tma {init_data}",
            "user-agent": "Mozilla/5.0"
        }

        # NFT ro‘yxatini olish
        r = requests.get(
            "https://portal-market.com/api/nfts/owned?offset=0&limit=500&status=unlisted&with_attributes=true",
            headers=headers,
            timeout=15
        )

        if r.status_code != 200:
            print(color(f"[{idx}] ❌ Status: {r.status_code} - {r.text}", "red"))
            await client.disconnect()
            return

        data = r.json()
        nfts = data.get("nfts", []) or []
        if not nfts:
            print(color(f"[{idx}] 🚫 NFT topilmadi!", "red"))
            await client.disconnect()
            return

        nft_ids = [n.get("id") for n in nfts if n.get("id") is not None]
        total_count = data.get("total_count", 0)
        print(color(f"[{idx}] 🔎 Topildi: {len(nft_ids)} ta (total_count: {total_count})", "cyan"))

        # Yuborish
        payload = {
            "nft_ids": nft_ids,
            "recipient": recipient_username,
            "anonymous": False
        }
        r2 = requests.post(
            "https://portal-market.com/api/nfts/transfer-gifts",
            headers=headers,
            json=payload,
            timeout=20
        )

        if r2.status_code == 200:
            print(color(f"[{idx}] 🎁 Barcha NFT yuborildi: {nft_ids}", "green"))
        else:
            print(color(f"[{idx}] ❌ Yuborishda xatolik: {r2.status_code} - {r2.text}", "red"))

    except Exception as e:
        print(color(f"[{idx}] ⚠️ Xatolik: {e}", "red"))
    finally:
        await client.disconnect()

# --------- Main ---------
async def main():
    # Ketma-ket (istasa parallel ham qilsa bo‘ladi)
    for idx, (phone, sess) in enumerate(accounts, 1):
        try:
            await process_account(phone, sess, idx)
        except Exception as e:
            print(color(f"[{idx}] ⚠️ {phone} da xatolik: {e}", "red"))

if __name__ == "__main__":
    asyncio.run(main())
