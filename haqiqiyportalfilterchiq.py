import asyncio
from telethon import TelegramClient, utils
from telethon.tl.functions.account import UpdateStatusRequest
import csv, os
from datetime import datetime
import pytz

from telethon.tl.functions.channels import LeaveChannelRequest
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty

from telethon.tl.functions.channels import LeaveChannelRequest

async def leave_channels(client, channels_to_leave):
    """
    channels_to_leave: {username: tugash_vaqti}
    """
    print("📤 Kanallardan chiqish boshlandi...")

    for username, tugash_vaqti in channels_to_leave.items():
        username_clean = username.lstrip("@")
        try:
            await client(LeaveChannelRequest(channel=username_clean))
            print(f"🚪 Chiqdi: @{username_clean} (Tugash: {tugash_vaqti})")
        except Exception as e:
            print(f"❌ Xatolik: {e} — @{username_clean} (Tugash: {tugash_vaqti})")

    print("🎉 Chiqish tugadi.")




def get_channels_to_leave(folder):
    """
    tugagan csv fayllardan faqat username’lar va tugash vaqtini chiqaradi
    """
    toshkent = pytz.timezone("Asia/Tashkent")
    today = datetime.now(toshkent)

    channels_done = dict()
    channels_not_done = set()
    files_to_delete = []

    for filename in os.listdir(folder):
        if filename.endswith(".csv"):
            path = os.path.join(folder, filename)
            with open(path, encoding="utf-8") as f:
                first_line = f.readline().strip()
                if ",Kanallar:" in first_line or ",\"Kanallar:" in first_line:
                    if ",\"Kanallar:" in first_line:
                        end_part, channel_part = first_line.split(",\"Kanallar:")
                    else:
                        end_part, channel_part = first_line.split(",Kanallar:")

                    end_str = end_part.replace("Tugash: ", "").strip()
                    channel_str = channel_part.replace('"', '').strip()
                else:
                    end_str = first_line.replace("Tugash: ", "").strip()
                    second_line = f.readline().strip()
                    if second_line.startswith("Kanallar:") or second_line.startswith("\"Kanallar:"):
                        channel_str = second_line.replace("Kanallar:", "").replace('"', '').strip()
                    else:
                        print(f"⚠️ Kanal topilmadi: {filename}")
                        continue

                end_time = datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")
                end_time = toshkent.localize(end_time)

                channels = [c.strip() for c in channel_str.split(",")]

                if end_time < today:
                    for c in channels:
                        channels_done[c.lower()] = end_str
                    files_to_delete.append(path)
                else:
                    channels_not_done.update([c.lower() for c in channels])

    # Faqat tugagan va boshqa faylda yo‘q bo‘lganlar
    result = {
        c: time for c, time in channels_done.items()
        if c not in channels_not_done
    }

    print(f"\n✅ Tugagan kanallar soni: {len(result)}")
    return result, files_to_delete


async def main():
    import os
    folder_1 = r"C:\join\haqiqiyportal"
    folder_2 = r"/storage/emulated/0/giv/haqiqiyportal"

    if os.path.exists(folder_1):
        folder = folder_1
    elif os.path.exists(folder_2):
        folder = folder_2
    else:
        raise FileNotFoundError("Hech qaysi 'haqiqiyportal' papkasi topilmadi.")

    print(f"📁 Foydalanilayotgan folder: {folder}")

    phonecsv = "adhamjon.csv"

    result, files_to_delete = get_channels_to_leave(folder)

    with open(phonecsv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        phlist = [row[0] for row in reader]

    print(f'📱 {len(phlist)} ta raqam topildi.')

    for index, phone_raw in enumerate(phlist):
        try:
            phone = utils.parse_phone(phone_raw)
            print(f'\n{index + 1}-akkaunt: {phone}')

            client = TelegramClient(f"adhamjon/{phone}", 22962676, '543e9a4d695fe8c6aa4075c9525f7c57')
            await client.connect()

            if not await client.is_user_authorized():
                print(f"[{index + 1}] ❌ Sessiya yo‘q!")
                await client.disconnect()
                continue

            await client.start()
            await client(UpdateStatusRequest(offline=False))

            await leave_channels(client, result)
            await client.disconnect()

        except Exception as e:
            print(f"❌ Xatolik: {e} — akkaunt {index + 1}")
            continue

    # fayllarni o‘chirish
    for file_path in files_to_delete:
        try:
            os.remove(file_path)
            print(f"🗑️ O‘chirildi: {os.path.basename(file_path)}")
        except Exception as e:
            print(f"❌ O‘chirib bo‘lmadi: {os.path.basename(file_path)} — {e}")


if __name__ == "__main__":
    asyncio.run(main())
