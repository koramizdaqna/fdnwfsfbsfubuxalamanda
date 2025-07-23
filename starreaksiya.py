# from telethon.sync import TelegramClient
# from licensing.models import *
# from licensing.methods import Key, Helpers
# from telethon.sync import TelegramClient
# print("Tabriklayman")
# from telethon.sync import TelegramClient
# import csv
# from telethon.tl.types import MessageActionGiftCode
# from telethon import utils
# from telethon.sync import TelegramClient
# from telethon.sync import TelegramClient
# from telethon import functions, types
# from telethon.tl.functions.account import UpdateStatusRequest
# phonecsv = "phone"
# with open(f'{phonecsv}.csv', 'r') as f:
#     phlist = [row[0] for row in csv.reader(f)]
# print('Jami📝: ' + str(len(phlist)))
# kanal = str(input("REaksiya bosiladigan kanal linkini kiriting: "))
# iduzex = int(input("REaksiya bosiladigan post: "))
# qowiwjm = 0
# qowiwjm2 = int(str(len(phlist)))
# indexx = 0
# for deltaxd in phlist[qowiwjm:qowiwjm2]:
#     indexx += 1
#     phone = utils.parse_phone(deltaxd)
#     print(f"Login {phone}")
#     api_id = 6810439
#     api_hash = '66ac3b67cce1771ce129819a42efe02e'
#     client = TelegramClient(f"sessions/{phone}", api_id, api_hash)
#     client.start(phone)
#     client(UpdateStatusRequest(offline=False))
#     print(f'Index : {indexx}')
#     try:
#         result = client(functions.payments.GetStarGiftsRequest(
#             hash=0
#         ))
#         print(result)
#         user = client.get_me()
#         user_info = client.get_entity()
#         print(f"Foydalanuvchi: {user_info.username}")
#         input()
#         print(f"STARS BALANSI ------ {result.balance}")
        
#         sonlar = result.balance
#         try:
#             if sonlar > 0:
#                 result = client(functions.messages.SendPaidReactionRequest(
#                     peer=kanal,
#                     msg_id=iduzex,
#                     count=sonlar,
#                     random_id = int(time.time()) * 2**32,
#                     private=False
#                 ))
#                 print(result.stringify())
#         except Exception as a:
#             print(f"Xatolik - {a}")
#             continue
#     except Exception as e:
#         print(f"Error: {e}")
#         continue
                    


# -*- coding: utf-8 -*-
import requests
from licensing.methods import Helpers
from time import time
import csv
import random
import asyncio

from telethon import utils, functions, types
from telethon.tl.functions.account import UpdateStatusRequest
from telethon.tl.functions.messages import SendPaidReactionRequest
from telethon.sync import TelegramClient

# 🔷 Aktivatsiya tekshirish
url = "https://raw.githubusercontent.com/Enshteyn40/crdevice/refs/heads/main/startreaksiya.py"
response = requests.get(url)
lines = response.text.splitlines()
hash_values_list = [line.strip() for line in lines]


def GetMachineCode():
    return Helpers.GetMachineCode(v=2)


machine_code = GetMachineCode()
print(machine_code)


async def main():
    if machine_code not in hash_values_list:
        print("🚫 Noaniq device. @enshteyn40 ga murojat qiling.")
        return

    print("✅ Aktivatsiya muvaffaqiyatli!")

    phonecsv = "phone"
    with open(f'{phonecsv}.csv', 'r') as f:
        phlist = [row[0] for row in csv.reader(f)]

    print(f'📄 Jami akkount: {len(phlist)}')

    # 🔗 Target sozlamalar
    TARGET_CHAT = str(input("Reaksiya bosiladigan kanalni kirgizing: -> "))
    # TARGET_CHAT = 'https://t.me/enshteyn40codes'
    # TARGET_MESSAGE_ID = 424
    TARGET_MESSAGE_ID = int(input("Reaksiya bosiladigan post id (raqamda): -> "))

    for indexx, deltaxd in enumerate(phlist, start=1):
        phone = utils.parse_phone(deltaxd)
        print(f"\n📲 [{indexx}] Login: {phone}")

        api_id = 6810439
        api_hash = '66ac3b67cce1771ce129819a42efe02e'

        async with TelegramClient(f"sessions/{phone}", api_id, api_hash) as client:
            if not await client.is_user_authorized():
                print(f"🚫 Raqam ro'yxatdan o'tmagan yoki sessiya yo'q: {phone}")
                continue

            await client(UpdateStatusRequest(offline=False))

            try:
                me = await client.get_me()
                stars_obj = (await client(functions.payments.GetStarsStatusRequest(peer=me))).balance
                # StarsAmount bo‘lsa — .amount ni o‘qi, aks holda oddiy int sifatida ol
                if hasattr(stars_obj, "amount"):
                    stars = stars_obj.amount
                else:
                    stars = int(stars_obj)

                print(f"⭐ Stars balansi: {stars}")

                if stars > 0:
                    peer = await client.get_entity(TARGET_CHAT)
                    random_id = int(time()) * 2**32

                    result = await client(SendPaidReactionRequest(
                        peer=peer,
                        msg_id=TARGET_MESSAGE_ID,
                        count=stars,
                        private=types.PaidReactionPrivacyDefault(),
                        random_id=random_id
                    ))
                    print(f"✅ {phone} => {stars}⭐ reaction yuborildi")
                else:
                    print(f"⚠️ {phone} da stars yo'q")


            except Exception as e:
                print(f"❌ Xatolik: {e}")

    print("\n🎉 Barcha reactionlar yuborildi!")


if __name__ == "__main__":
    asyncio.run(main())
