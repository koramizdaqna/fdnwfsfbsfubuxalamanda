import os
import csv
import csv
from telethon.sync import TelegramClient
from licensing.models import *s
from licensing.methods import Key, Helpers
phone_path = r"/storage/emulated/0/giv/captcha2.csv"
pc_path = r"C:\join\captcha2.csv"

captcha_api_key = None

if os.path.exists(phone_path):
    print("Telefon fayli topildi!")
    def GetMachineCode():
        machine_code = Helpers.GetMachineCode(v=2)
        return machine_code

    machine_code = GetMachineCode()
    with open(phone_path, 'r') as f:
        reader = csv.reader(f)
        captcha_api_key = next(reader)[0]
    
elif os.path.exists(pc_path):
    print("Kompyuter fayli topildi!")
    import subprocess
    def get_hardware_id():
        hardware_id = str(subprocess.check_output('wmic csproduct get uuid')).split('\\r\\n')[1].strip('\\r').strip()
        return hardware_id

    machine_code = get_hardware_id()
    with open(pc_path, 'r') as f:
        reader = csv.reader(f)
        captcha_api_key = next(reader)[0]
else:
    print("Hech qaysi fayl topilmadi!")
# -*- coding: utf-8 -*-
import requests
from licensing.methods import Helpers

# GitHub repository URL
url = "https://raw.githubusercontent.com/Enshteyn40/crdevice/refs/heads/main/givshare.csv"

# URL'dan CSV faylni yuklab olish
response = requests.get(url)

# Ma'lumotlarni qatorlarga ajratish
lines = response.text.splitlines()

# Olingan qatorlarni tozalash
hash_values_list = [line.strip() for line in lines]
print(machine_code)

# Mashina kodini tekshirish
if machine_code in hash_values_list:
    print("Tabriklayman")
    from telethon.sync import TelegramClient
    
    from urllib.parse import unquote
    from telethon.tl.functions.messages import ImportChatInviteRequest
    import cloudscraper
    import time
    from telethon import types, utils, errors
    from telethon.tl.functions.messages import RequestAppWebViewRequest
    from telethon.tl.types import InputBotAppShortName, InputUser
    from telethon.sync import TelegramClient
    from telethon.tl.functions.channels import LeaveChannelRequest, JoinChannelRequest
    from telethon.tl.functions.account import UpdateStatusRequest
    phonecsv = "phone"
    with open(f'{phonecsv}.csv', 'r') as f:
        phlist = [row[0] for row in csv.reader(f)]
    print('Jami Nomerlar: ' + str(len(phlist)))
    qowiwjm = 0
    qowiwjm2 = int(str(len(phlist)))
    channels = []
    channels1 = []


    kutishaqti = int(input("kutish vaqtini kiriting: "))
    start_param = str(input("Ref id kiriting: ")) 
    nechatda  = int(input("Nechtada referal silka almashsin: "))
    # num_channels = int(input("Givning nechta ochiq kanali bor? ")) 
    # for i in range(num_channels):
    #     channel_link = input(f'Kanal linkini kiriting #{i + 1:}: ')
    #     channels.append(channel_link)
    # num_channels1 = int(input("Givning nechta yopiq kanali bor? "))     
    # for i in range(num_channels1):
    #     channel_link1 = input(f'Kanal linkini kiriting #{i + 1:}: ')
    #     channels1.append(channel_link1)  
    indexx = 0
    count = 0
    for deltaxd in phlist[qowiwjm:qowiwjm2]:
        try:
            indexx += 1
            phone = utils.parse_phone(deltaxd)
            print(f"Login {phone}")
            api_id = 22962676
            api_hash = '543e9a4d695fe8c6aa4075c9525f7c57'
            client = TelegramClient(f"sessions/{phone}", api_id, api_hash)
            client.start(phone)
            client(UpdateStatusRequest(offline=False))
            print(f'Index : {indexx}')
            async def main():
                global start_param
                try:
                    for channel_link in channels:
                        try:
                            await client(JoinChannelRequest(channel_link))
                        except errors.FloodWaitError as e:
                            print("")
                    for channel_link1 in channels1:
                        try:
                            await client(ImportChatInviteRequest(channel_link1))
                        except errors.FloodWaitError as e:
                            print("Kanal yoki guruhda  bor ekan keyingi kanallarga o'taman")       
                except Exception as e:
                        print("")
                bot_entity = await client.get_entity("GiveShareBot")
                bot = InputUser(user_id=bot_entity.id, access_hash=bot_entity.access_hash)
                bot_app = InputBotAppShortName(bot_id=bot, short_name="app")
                #print(bot_app)
                await client.send_message(bot, f"/start")
                print(f"Hozirgi ishlatilinayotgan referal ID: {start_param}")
                web_view = await client(
                    RequestAppWebViewRequest(
                        peer=bot,
                        app=bot_app,
                        platform="android",
                        write_allowed=True,
                        start_param=start_param
                    )
                )
                auth_url = web_view.url
                time.sleep(kutishaqti)
                tg_web_data = unquote(
                    string=auth_url.split('tgWebAppData=', maxsplit=1)[1].split('&tgWebAppVersion', maxsplit=1)[0])
                print(auth_url)
                me = await client.get_me()
                userid = me.id 
                scraper = cloudscraper.create_scraper()
                response = scraper.post('https://api.giveshare.ru/index',
                                        json={'initData': tg_web_data, 'param': start_param})
                response_json = response.json()
                
                # Tiket bor yoki yo‘qligini tekshirish
                user_data = response_json.get("user", {})
                tickets = user_data.get("tickets", [])
                raffle_data = response_json.get("raffle", {})
                raffleid = raffle_data.get("id", [])

                if tickets:
                    print("Tiketlar mavjud")
                    print("Bu givda qatnashan ekan")
                else:
                    print("Tiket yo‘q ekan")
                    channels_info = [(channel['name'], channel['link']) for channel in response_json['raffle']['channels']]
                    
                    # Har bir kanalga qo'shilish
                    for name, link in channels_info:
                        try:
                            if link.startswith('https://t.me/+'):
                                # Taklif havolasi orqali qo'shilish
                                chat_username = link.split('+')[-1]
                                await client(ImportChatInviteRequest(chat_username))
                            elif link.startswith('https://t.me/'):
                                # Username orqali qo'shilish
                                chat_username = link.split('/')[-1]
                                await client(JoinChannelRequest(chat_username))
                            else:
                                print(f"Notanish link format: {link}")
                            print(f"Muvaffaqiyatli qo'shildi: {name} - {link}")
                            time.sleep(1)
                        except Exception as e:
                            print(f"Xatolik kanalga qo'shilishda {link}: {e}")
                    
                    pesponse = scraper.post('https://api.giveshare.ru/member/make',
                                        json={'initData': tg_web_data, 'param': start_param, 'token':""})
                    lesponsse = scraper.post('https://api.giveshare.ru/member/check',
                                        json={'initData': tg_web_data, 'raffle': raffleid, 'user_id':userid})
                    lesponsse_json = lesponsse.json()

                    tickets = lesponsse_json.get("tickets", [])
                    if tickets:
                        ref_url = lesponsse_json.get("ref_url")  # To‘g‘rilangan qism
                        print(f"Givda muvvaffaqiyatli qatnashildi")
                        import re
                        if ref_url:
                            match = re.search(r'startapp=([^&]+)', ref_url)
                            if match:
                                startapp_value = match.group(1)
                            else:
                                print("startapp= dan keyingi qiymat topilmadi")
                        else:
                            print("ref_url topilmadi")
                        if indexx % nechatda == 0:
                            start_param = startapp_value
                            print(f"Yangi refid: {start_param}")
                    else:
                        ticket_number = None
                        print("Giveaway uchun tiket berilmadi")

                    
                    time.sleep(2)
            with client:
                client.loop.run_until_complete(main())
        except Exception as e:
            print("error:  ", e)
            continue
else:
    print("Kodni sotib olish uchun @Enshteyn40 ga murojat qiling")
                        
