# -*- coding: utf-8 -*-
import os
import csv
import subprocess
import time
import requests
import re
from urllib.parse import unquote
from licensing.methods import Helpers
from telethon.sync import TelegramClient
from telethon import types, utils, errors
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.account import UpdateStatusRequest
from telethon.tl.functions.messages import ImportChatInviteRequest, RequestAppWebViewRequest
from telethon.tl.types import InputBotAppShortName, InputUser
import cloudscraper

# --- Rangli chiqish uchun funksiya ---
def color(text, color_code):
    return f"\033[{color_code}m{text}\033[0m"

# --- Fayl manzillari ---
phone_path = r"/storage/emulated/0/giv/captcha2.csv"
pc_path = r"C:\\join\\captcha2.csv"
captcha_api_key = None

# --- Mashina kodini olish ---
if os.path.exists(phone_path):
    print(color("Telefon fayli topildi!", "92"))
    machine_code = Helpers.GetMachineCode(v=2)
    with open(phone_path, 'r') as f:
        captcha_api_key = next(csv.reader(f))[0]

elif os.path.exists(pc_path):
    print(color("Kompyuter fayli topildi!", "94"))
    def get_hardware_id():
        result = subprocess.check_output('wmic csproduct get uuid').decode()
        return result.split('\n')[1].strip()
    machine_code = get_hardware_id()
    with open(pc_path, 'r') as f:
        captcha_api_key = next(csv.reader(f))[0]
else:
    print(color("Hech qaysi fayl topilmadi!", "91"))
    exit()

# --- Ruxsat etilgan mashinalarni tekshirish ---
url = "https://raw.githubusercontent.com/Enshteyn40/crdevice/refs/heads/main/givshare.csv"
hash_values_list = requests.get(url).text.splitlines()
print(color(machine_code, "96"))

if machine_code not in hash_values_list:
    print(color("Sizda ruxsat yo'q.", "91"))
    exit()

print(color("Tabriklayman", "92"))

# --- Telegram raqamlar ---
with open('phone.csv', 'r') as f:
    phlist = [row[0] for row in csv.reader(f)]
print(color('Jami Nomerlar: ' + str(len(phlist)), "93"))

kutishaqti = int(input("⏱ Kutish vaqtini kiriting (sekund): "))
start_param = input("🔗 Ref ID kiriting: ")
nechatda = int(input("♻️ Nechtada referal almashtirilsin: "))
num_channels = int(input("📢 Ochiq kanal soni: "))
channels = [input(f"  ➤ Kanal {i+1} linki: ") for i in range(num_channels)]
num_channels1 = int(input("🔒 Yopiq kanal soni: "))
channels1 = [input(f"  ➤ Yopiq kanal {i+1} linki: ") for i in range(num_channels1)]

api_id = 22962676
api_hash = '543e9a4d695fe8c6aa4075c9525f7c57'

# --- Har bir raqam uchun ---
for indexx, phone_raw in enumerate(phlist, start=1):
    try:
        phone = utils.parse_phone(phone_raw)
        print(color(f"Login {phone}", "96"))

        client = TelegramClient(f"sessions/{phone}", api_id, api_hash)
        client.start(phone)
        client(UpdateStatusRequest(offline=False))
        print(color(f'Index : {indexx}', "97"))

        async def main():
            global start_param
            try:
                for link in channels:
                    try:
                        await client(JoinChannelRequest(link))
                        print(color(f"Kanalga muvaffaqiyatli qo'shildi {link}", "92"))
                    except errors.FloodWaitError:
                        pass
                for link in channels1:
                    try:
                        invite_hash = link.split("/")[-1]
                        await client(ImportChatInviteRequest(invite_hash))
                    except errors.FloodWaitError:
                        print(color("Kanal yoki guruhda bor ekan, o'tkazildi", "93"))
            except Exception:
                pass

            bot_entity = await client.get_entity("GiveShareBot")
            bot = InputUser(user_id=bot_entity.id, access_hash=bot_entity.access_hash)
            bot_app = InputBotAppShortName(bot_id=bot, short_name="app")
            await client.send_message(bot, "/start")
            print(color(f"Hozirgi ishlatilinayotgan referal ID: {start_param}", "95"))

            web_view = await client(RequestAppWebViewRequest(
                peer=bot,
                app=bot_app,
                platform="android",
                write_allowed=True,
                start_param=start_param
            ))

            auth_url = web_view.url
            time.sleep(kutishaqti)
            tg_web_data = unquote(auth_url.split('tgWebAppData=')[1].split('&')[0])
            me = await client.get_me()
            userid = me.id

            scraper = cloudscraper.create_scraper()
            ref_url = None
            try:
                response = scraper.post('https://api.giveawaybot.website/index',
                                        json={'initData': tg_web_data, 'param': start_param})
                response_json = response.json()

                user_data = response_json.get("user", {})
                raffle_data = response_json.get("raffle", {})
                raffleid = raffle_data.get("id", [])
                ref_url = user_data.get("ref_url")
                print(color("🔗 Topilgan ref_url:", "96"), ref_url)

                if not ref_url:
                    print(color("⚠️ ref_url topilmadi, check() orqali urinamiz", "93"))
                    scraper.post('https://api.giveawaybot.website/index',
                                 json={'initData': tg_web_data, 'param': start_param})
                    scraper.post('https://api.giveshare.ru/member/make',
                                 json={'initData': tg_web_data, 'param': start_param, 'token': ""})
                    lesponse = scraper.post('https://api.giveawaybot.website/member/check',
                                            json={'initData': tg_web_data, 'raffle': raffleid, 'user_id': userid})
                    ref_url = lesponse.json().get("ref_url")
                    print(color("🧩 Fallback ref_url:", "96"), ref_url)

            except Exception as e:
                print(color("❌ ref_url olishda xatolik:", "91"), e)

            if ref_url:
                match = re.search(r'startapp=([^&]+)', ref_url)
                if match:
                    startapp_value = match.group(1)
                    if indexx % nechatda == 0:
                        start_param = startapp_value
                        print(color(f"Yangi refid: {start_param}", "92"))
                else:
                    print(color("startapp= dan keyingi qiymat topilmadi", "93"))
            else:
                print(color("ref_url topilmadi", "91"))
            time.sleep(2)

        with client:
            client.loop.run_until_complete(main())
    except Exception as e:
        print(color("error:", "91"), e)
        continue
