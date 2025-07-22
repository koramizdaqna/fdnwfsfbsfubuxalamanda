# -*- coding: utf-8 -*-
import asyncio
import csv
import os
import sys
import requests
from datetime import datetime, timedelta, timezone
from licensing.methods import Helpers
from termcolor import colored
from telethon import utils, TelegramClient, functions
from telethon.tl.functions.account import UpdateStatusRequest

# 🔷 Aktivatsiya tekshirish
url = "https://raw.githubusercontent.com/Enshteyn40/crdevice/refs/heads/main/universal.csv"
machine_code = Helpers.GetMachineCode(v=2)
hash_values_list = requests.get(url).text.splitlines()

if machine_code not in hash_values_list:
    print(colored("Kodni aktivlashtirish uchun @Enshteyn40 ga murojat qiling", "magenta"))
    sys.exit()

print(colored("Oxirgi kod yangilangan vaqti: 23.05.2025 8:28 PM", "magenta"))

api_id = 22962676
api_hash = '543e9a4d695fe8c6aa4075c9525f7c57'

# 📄 Kanal faylini tekshirish
def ensure_path_and_file(path, filename):
    if not os.path.exists(path):
        os.makedirs(path)
    filepath = os.path.join(path, filename)
    if not os.path.isfile(filepath):
        with open(filepath, 'w', encoding='utf-8') as f:
            pass
        sys.exit(f"{filename} yaratildi. Uni to‘ldirib qayta ishga tushiring.")
    return filepath

# 🔷 GIV faylni aniqlash
giv_path = (
    '/storage/emulated/0/giv' if os.path.exists('/storage/emulated/0/giv')
    else 'C:\\join' if os.path.exists('C:\\join') else None
)
if not giv_path:
    sys.exit("Hech qanday mos papka topilmadi")

mrkt_file = ensure_path_and_file(giv_path, 'boosberadigankanallar.csv')
premium_channels = [row[0] for row in csv.reader(open(mrkt_file, 'r', encoding='utf-8')) if row]

# 📄 Telefon raqamlarini o‘qish
with open('adhamjon.csv', 'r') as f:
    phones = [row[0] for row in csv.reader(f)]

print(colored(f"Boost bor raqamlar: {len(phones)}", "blue"))

async def process_account(phone, index):
    try:
        print(colored(f"[{index}] Login: {phone}", "green"))
        parsed_phone = utils.parse_phone(phone)
        client = TelegramClient(f"adhamjon/{parsed_phone}", api_id, api_hash)
        await client.start(phone=parsed_phone)
        await client(UpdateStatusRequest(offline=False))

        for channel in premium_channels:
            result = await client(functions.premium.GetMyBoostsRequest())
            print(result)

            if not result.my_boosts:
                print(colored(f"[{index}] ❌ Hech qanday boost topilmadi", "yellow"))
                await client.disconnect()
                return

            # 🔷 Bo‘sh slotni topish
            boosts_sorted = sorted(result.my_boosts, key=lambda b: b.date)
            oldest_boost = None

            for b in boosts_sorted:
                if b.peer is None:
                    oldest_boost = b
                    break

            if not oldest_boost:
                print(colored(f"[{index}] 🔄 Bo‘sh boost slot topilmadi", "yellow"))
                continue  # keyingi kanalga o‘tadi

            oldest_slot = oldest_boost.slot
            print(f"✅ Eng eski bo‘sh slot: {oldest_slot}")

            try:
                result_boost = await client(functions.premium.ApplyBoostRequest(
                    peer=channel,
                    slots=[oldest_slot]
                ))
                print(f"🚀 Boost {oldest_slot} slotdan olib, {channel} kanalga berildi.")
            except Exception as e:
                print(colored(f"Boost berishda xatolik: {e}", "red"))

        await client.disconnect()

    except Exception as e:
        print(colored(f"[{index}] Xatolik: {e}", "red"))


async def main():
    batch_size = 1
    tasks = []
    for idx, phone in enumerate(phones, 1):
        tasks.append(process_account(phone, idx))
        if len(tasks) == batch_size:
            await asyncio.gather(*tasks)
            tasks = []
    if tasks:
        await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())
