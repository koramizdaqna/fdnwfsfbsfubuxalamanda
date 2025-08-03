import asyncio
import csv
import os
import re
import traceback
from telethon import utils
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.account import UpdateStatusRequest


import asyncio
import csv
import json
import requests
from licensing.methods import Helpers
from urllib.parse import unquote
from termcolor import colored
from telethon import utils
from telethon.sync import TelegramClient
from telethon.tl.functions.account import UpdateStatusRequest
from telethon.tl.types import InputUser, InputBotAppShortName
from telethon.tl.functions.messages import RequestAppWebViewRequest

url = "https://raw.githubusercontent.com/Enshteyn40/crdevice/refs/heads/main/pastamasta.csv"
machine_code = Helpers.GetMachineCode(v=2)
hash_values_list = requests.get(url).text.splitlines()

if machine_code not in hash_values_list:
    print(machine_code)
    print(colored("Kodni aktivlashtirish uchun @Enshteyn40 ga murojat qiling", "magenta"))
    exit()

print(colored("Oxirgi kod yangilangan vaqti: 03.08.2025 4:54 PM", "magenta"))

# 📋 Telefonlar ro'yxati
phonecsv = "phone"
with open(f"{phonecsv}.csv", 'r') as f:
    phlist = [row[0] for row in csv.reader(f)]

print(f"📱 Jami raqamlar: {len(phlist)}")

# 🔐 Telegram API
api_id = 22962676
api_hash = '543e9a4d695fe8c6aa4075c9525f7c57'

# 🎯 Boshlang‘ich start ID (doimiy)
start_id = str(input("Gividsini kiriting --: "))

son = int(input("Har nechtada referal almashsin --: "))
referral_id_list = []

CAPTCHA_MAP = {
    "сыр": "🧀", "бабочку": "🦋", "обезьяну": "🐵", "панду": "🐼", "звезду": "⭐", "пазл": "🧩",
    "пазла": "🧩", "лягушку": "🐸", "жабу": "🐸", "единорога": "🦄", "Кубик": "🎲", "пчелу": "🐝",
    "гриб": "🍄", "дельфина": "🐬", "кита": "🐋", "лису": "🦊", "мышь": "🐹", "паука": "🕷️",
    "яблоко": "🍎", "льва": "🦁", "дракона": "🐉", "хомяка": "🐹"
}

async def main():
    indexx = 0
    for phone in phlist:
        phone = utils.parse_phone(phone)
        indexx += 1
        print(f"\n📞 {indexx}. Raqam: {phone}")

        tg_client = TelegramClient(f'sessions/{phone}', api_id, api_hash)
        found_links = []
        final_referral_id = None

        try:
            await tg_client.connect()
            if not await tg_client.is_user_authorized():
                print("🚫 Sessiya yo‘q. O‘tkazib yuborildi.")
                continue

            await tg_client.start()
            await tg_client(UpdateStatusRequest(offline=False))

            async with tg_client:
                username = await tg_client.get_entity("@FastGiveawaysBot")

                if indexx % son == 0 and indexx > 0 and referral_id_list:
                    latest_ref = referral_id_list[-1]
                    print(f"🔁 Referral orqali /start yuborilmoqda: {latest_ref}")
                    await tg_client.send_message(username, f"/start {latest_ref}")

                # ↪️ Har qanday holatda /start qayta yuborilishi kerak
                while True:
                    await tg_client.send_message(username, f"/start {start_id}")
                    await asyncio.sleep(2)

                    m = await tg_client.get_messages(username, limit=1)
                    if not m:
                        print("❌ Javob kelmadi.")
                        break

                    msg_obj = m[0]
                    msg = msg_obj.message

                    # 🤖 Captcha
                    if "нужно убедиться, что вы не робот" in msg.lower():
                        print("🤖 Captcha topildi!")
                        emoji_to_click = None
                        for word in CAPTCHA_MAP:
                            if word in msg:
                                emoji_to_click = CAPTCHA_MAP[word]
                                break

                        if not emoji_to_click:
                            print("❌ Emoji topilmadi.")
                            break

                        print(f"🧠 Tanlanadigan emoji: {emoji_to_click}")
                        try:
                            await msg_obj.click(text=emoji_to_click)
                            print(f"✅ {emoji_to_click} bosildi!")
                            await asyncio.sleep(5)
                        except Exception as e:
                            print(f"❌ Tugma bosishda xatolik: {e}")
                        continue

                    # 📢 Obuna bo'lish kerak
                    elif "После подписки попробуйте снова" in msg:
                        print("📢 Obuna bo'lish talab qilinmoqda.")
                        found_links = []

                        # 1. Yashirin (entities ichidagi) linklarni ajratish
                        if msg_obj.entities:
                            for ent in msg_obj.entities:
                                if hasattr(ent, 'url') and ent.url:
                                    found_links.append(ent.url)
                                    print(f"🔗 Yashirin link: {ent.url}")

                        # 2. Ko‘rinadigan linklar (agar mavjud bo‘lsa)
                        visible_links = re.findall(r"https?://t\.me/[^\s\)\]]+", msg)
                        for link in visible_links:
                            if link not in found_links:
                                found_links.append(link)
                                print(f"🔗 Ochiq link: {link}")

                        if not found_links:
                            print("❌ Hech qanday link topilmadi.")
                            break

                        # 🔗 Kanallarga qo‘shilish
                        for link in found_links:
                            try:
                                if link.startswith("https://t.me/+"):
                                    chat_username = link.split("+")[-1]
                                    await tg_client(ImportChatInviteRequest(chat_username))
                                    print(f"✅ Yopiq kanalga qo‘shildi: {link}")
                                else:
                                    chat_username = link.split("/")[-1]
                                    await tg_client(JoinChannelRequest(chat_username))
                                    print(f"✅ Ochiq kanalga qo‘shildi: {link}")
                                await asyncio.sleep(2)
                            except Exception as e:
                                print(f"⚠️ Kanalga qo‘shilishda xatolik: {e}")
                        continue

                    # ✅ Ishtirok tasdiqlansa
                    elif "☑️ Вы участвуете!" in msg:
                        print("🎉 Ishtirok tasdiqlandi!")
                        match = re.search(r"t\.me/FastGiveawaysBot\?start=([a-zA-Z0-9_-]+)", msg)
                        if match:
                            final_referral_id = match.group(1)
                            referral_id_list.append(final_referral_id)

                        os.makedirs("fastgiveaway", exist_ok=True)
                        file_path = os.path.join("fastgiveaway", f"{start_id}.csv")
                        file_exists = os.path.exists(file_path)

                        with open(file_path, "a", newline='') as f:
                            writer = csv.writer(f)
                            if not file_exists:
                                writer.writerow(['phone', 'referral_id'])
                            writer.writerow([phone, final_referral_id or ""])

                        print(f"📥 Yozildi: {phone} → referral: {final_referral_id or 'NOMA’LUM'}")
                        break

                    else:
                        print("❗ Noma’lum javob:", msg)
                        break

        except Exception as e:
            traceback.print_exc()
            print(f"❌ Telefon: {phone} ishlamadi. Xato: {e}")

if __name__ == "__main__":
    asyncio.run(main())
