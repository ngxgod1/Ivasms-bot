import asyncio
import websockets
import json
import re
import requests
import time
from datetime import datetime
import phonenumbers
from phonenumbers import geocoder

BOT_TOKEN = "8642429610:AAFFllSv1R4k7hP3f69jIm2a46eNw_LIlE0"
CHAT_ID = "-1003755474546"

WS_URL = "wss://ivas.tempnum.qzz.io:2087/socket.io/?token=eyJpdiI6Inh1WTlNVTRrT1l2WFRuOWVrV09ZVmc9PSIsInZhbHVlIjoieGFRcWdEWXVlWlN6RUJaazBxR0srSzI0UENFU08zMlNMNlRSbXhUQnlVNnBNS25IYmVaZW5TQXVubVpBOXdWRVNFY3JzY2E4SkdEeXRCZ0RmMWhiK2duR0VQc05OS3VWSURsR1pYb29sUU5vK0htUkZJS3IyRGluajQxNEoyak9uWTVIeENGT2RIR2I1SFdMdk1naHEwRDY5NTZuWktLZ3FYNDlHYVlDWHFHdmE0R3lUT2tFMjB6czcvN2h6SHo0UE1rZG9BSDJOVnJldUlDMDF4RGRjU2V1VUFGT1g3NzhzSSsxcm9rSXZBN2F4ZzNlMHNScnltRHRaUGp4TTM0dUo3WEF1Z1RTNng0Rk5qSGhGSEFMSGlocmM0Unc5NVVzREc2QSszc0FZUnhlVE1kelBESzJuUWxZRzVHNlp2elVqbWtqYTA3ZjN3ZnEydmtpdmRFVVZFK21pcUlkdWd4Vmo3L1M5RDZwRGtmbmV5T0FQbXd2a0xFNWxCdFdOOThOS1lodFdKcVRuRHJnZ1JnV1kzTkxtaW1NOWMyZ0paVjRDZndHSzFaYlJ0SFNmL1VRQVdDbTJrMlZoUkptaGZZS09Jd2h6STBDQ1JmY3lRZVF3WnRidXQ4TnhsTlU1YmEvbjFpRXlydG1lUGNKakozcEVyNnl2MHREU2NNRHNKVWNNdkZnVDBqbndnQ2xTdU1RbnVWNXJBPT0iLCJtYWMiOiJhMzhhZTFjMzZiNDM3ODc2YjNlOWUyZjcxMzZhYzg0YjJhMjA0MTQ5MjQwNTVhMzBhYjZkZjExZGE1YjlkYjJkIiwidGFnIjoiIn0%3D&user=febed320dee42f56634412749978c9f5&EIO=4&transport=websocket"

sent=set()


def extract_otp(msg):

    m=re.search(r"\d{3}-\d{3}",msg)
    if m:
        return m.group()

    m=re.search(r"\d{6}",msg)
    if m:
        return m.group()

    m=re.search(r"\d{4}",msg)
    if m:
        return m.group()

    return None


def mask(num):

    num=re.sub(r"\D","",num)

    if len(num)<6:
        return num

    return f"{num[:3]}XXXX{num[-3:]}"


def detect_service(msg):

    m=msg.lower()

    if "whatsapp" in m:
        return "🟢 WhatsApp"

    if "telegram" in m:
        return "✈️ Telegram"

    if "facebook" in m:
        return "📘 Facebook"

    if "google" in m:
        return "🔴 Google"

    return "📩 OTP"


def country(number):

    try:

        num=phonenumbers.parse("+"+number)

        c=geocoder.description_for_number(num,"en")

        region=phonenumbers.region_code_for_number(num)

        flag="".join(chr(127397+ord(x)) for x in region)

        return c,flag

    except:

        return "Unknown","🌍"


def send(country,flag,service,number,otp,msg):

    now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    text=f"""
<b>{flag} New {country} {service} OTP !</b>

<blockquote>
⏰ Time: {now}

🌍 Country: {country}

📲 Service: {service}

📞 Number: {number}

🔑 OTP: <code>{otp}</code>
</blockquote>

📩 <b>Full Message:</b>

<blockquote>{msg}</blockquote>

━━━━━━━━━━━━━━
<b>Powered By LUCKY 👑</b>
"""

    url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload={
        "chat_id":CHAT_ID,
        "text":text,
        "parse_mode":"HTML",
        "reply_markup":{
            "inline_keyboard":[

                [
                    {"text":"🏛 Number","url":"https://t.me/NumOTPV2BOT"},
                    {"text":"👾 Developer","url":"https://t.me/ngxgod1"}
                ],

                [
                    {"text":"📢 Channel","url":"https://t.me/TeamOFDark1"},
                    {"text":"🟢 OTP","url":"https://t.me/forwardforme1"}
                ]

            ]
        }
    }

    requests.post(url,json=payload)


async def ping(ws):

    while True:

        await asyncio.sleep(20)

        try:
            await ws.send("3")
        except:
            break


async def start():

    while True:

        try:

            async with websockets.connect(WS_URL,ping_interval=None) as ws:

                print("Connected IVAS")

                msg=await ws.recv()

                await ws.send("40/livesms,")

                asyncio.create_task(ping(ws))

                while True:

                    data=await ws.recv()

                    print("RAW:",data)

                    if "livesms" in data:

                        payload=json.loads(data[data.find("["):])

                        sms=payload[1]

                        message=sms.get("message","")
                        number=sms.get("recipient","")

                        otp=extract_otp(message)

                        if not otp:
                            continue

                        if otp in sent:
                            continue

                        sent.add(otp)

                        service=detect_service(message)

                        c,flag=country(number)

                        number=mask(number)

                        send(c,flag,service,number,otp,message)

                        print("OTP SENT")

        except Exception as e:

            print("Reconnect...",e)

            time.sleep(5)


asyncio.run(start())
