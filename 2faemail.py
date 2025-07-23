import asyncio
import csv
import os
import re
import imaplib
import email as e
from telethon.errors import CodeInvalidError
from telethon.sync import TelegramClient
from telethon.tl.functions.account import UpdateStatusRequest
from licensing.methods import Helpers

api_id = '22962676'
api_hash = '543e9a4d695fe8c6aa4075c9525f7c57'


def get_machine_code():
    return Helpers.GetMachineCode(v=2)


def load_phones(file_path):
    with open(file_path, 'r') as f:
        return [row[0] for row in csv.reader(f) if row]


def extract_code_from_text(text):
    match = re.search(r"\b\d{5,6}\b", text)
    if match:
        return match.group()
    return None


def get_latest_gmail_code(email_user, email_pass):
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(email_user, email_pass)
    mail.select("inbox")

    result, data = mail.search(None, "ALL")
    mail_ids = data[0].split()

    for i in reversed(mail_ids[-10:]):
        result, data = mail.fetch(i, "(RFC822)")
        raw_email = data[0][1]
        msg = e.message_from_bytes(raw_email)

        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    code = extract_code_from_text(body)
                    if code:
                        return code
        else:
            body = msg.get_payload(decode=True).decode()
            code = extract_code_from_text(body)
            if code:
                return code

    return None


def wait_for_new_code(email_user, email_pass, timeout=120):
    print("📨 Yangi kodni kutyapmiz...")
    old_code = get_latest_gmail_code(email_user, email_pass)
    for _ in range(timeout // 5):
        kod = get_latest_gmail_code(email_user, email_pass)
        if kod and kod != old_code:
            print(f"✅ Yangi kod topildi: {kod}")
            return kod
        asyncio.sleep(5)
    raise TimeoutError("⏳ Yangi kod topilmadi.")


async def process_accounts(phones, a, b, c, email, email_pass):
    print('📋 NOMERLAR:', len(phones))
    for indexx, phone_number in enumerate(phones, start=1):
        try:
            async with TelegramClient(f"sessions/{phone_number}", api_id, api_hash) as client:
                await client.start(phone_number)
                await client(UpdateStatusRequest(offline=False))
                print(f'\n📱 Raqam: {indexx} - {phone_number}')
                print("📨 Kod yuborish jarayoni boshlandi...")

                # edit_2fa chaqirilganda kod yuboriladi va avtomatik kutiladi
                await client.edit_2fa(
                    current_password=a,
                    new_password=b,
                    hint=c,
                    email=email,
                    email_code_callback=lambda _: wait_for_new_code(email, email_pass)
                )

                print("✅ 2FA muvaffaqiyatli o‘rnatildi.")
                await asyncio.sleep(3)

        except CodeInvalidError:
            print("❌ Noto‘g‘ri kod, qayta urinib ko‘ring.")
        except TimeoutError as te:
            print(te)
        except Exception as e:
            print(f"❌ Xato: {e}")


def main():
    print("🎉 Tabriklayman")
    print("👤 Yaratuvchi: @Enshteyn40")
    print("🔑 Mashina kodi:", get_machine_code())

    a = input("🔑 Eski parolni yozing: ")
    b = input("🆕 Yangi parolni yozing: ")
    c = input("ℹ️ Yordam so‘zni yozing: ")
    email = input("📧 Gmail manzilini yozing: ")
    email_pass = input("📧 Gmail App Password ni yozing: ")

    if not os.path.exists("phone.csv"):
        print("📄 phone.csv topilmadi!")
        return

    phones = load_phones("phone.csv")

    asyncio.run(process_accounts(phones, a, b, c, email, email_pass))


if __name__ == "__main__":
    main()
