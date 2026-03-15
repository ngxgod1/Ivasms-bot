import asyncio
import websockets
import json
import requests
import re
import time
from datetime import datetime
import phonenumbers
from phonenumbers import geocoder

# ===== CONFIGURATION =====
BOT_TOKEN = "8642429610:AAFFllSv1R4k7hP3f69jIm2a46eNw_LIlE0"
CHAT_ID = "-1003755474546"

# ===== CUSTOM EMOJI IDS (from bot.py) =====
CUSTOM_EMOJI = {
    "CHANNEL": "5471942661868898717",
    "NUMBER": "5470064017403825560",
    "LOCATION": "5469789676367794476",
    "COPY": "5330115548900501467",
    "WHATSAPP": "5334998226636390258",
    "TELEGRAM": "5330237710655306682",
    "INSTAGRAM": "5319160079465857105",
    "FACEBOOK": "5323261730283863478",
}

# IVA SMS WebSocket URL
WS_URL = "wss://ivas.tempnum.qzz.io:2087/socket.io/?token=eyJpdiI6Inh1WTlNVTRrT1l2WFRuOWVrV09ZVmc9PSIsInZhbHVlIjoieGFRcWdEWXVlWlN6RUJaazBxR0srSzI0UENFU08zMlNMNlRSbXhUQnlVNnBNS25IYmVaZW5TQXVubVpBOXdWRVNFY3JzY2E4SkdEeXRCZ0RmMWhiK2duR0VQc05OS3VWSURsR1pYb29sUU5vK0htUkZJS3IyRGluajQxNEoyak9uWTVIeENGT2RIR2I1SFdMdk1naHEwRDY5NTZuWktLZ3FYNDlHYVlDWHFHdmE0R3lUT2tFMjB6czcvN2h6SHo0UE1rZG9BSDJOVnJldUlDMDF4RGRjU2V1VUFGT1g3NzhzSSsxcm9rSXZBN2F4ZzNlMHNScnltRHRaUGp4TTM0dUo3WEF1Z1RTNng0Rk5qSGhGSEFMSGlocmM0Unc5NVVzREc2QSszc0FZUnhlVE1kelBESzJuUWxZRzVHNlp2elVqbWtqYTA3ZjN3ZnEydmtpdmRFVVZFK21pcUlkdWd4Vmo3L1M5RDZwRGtmbmV5T0FQbXd2a0xFNWxCdFdOOThOS1lodFdKcVRuRHJnZ1JnV1kzTkxtaW1NOWMyZ0paVjRDZndHSzFaYlJ0SFNmL1VRQVdDbTJrMlZoUkptaGZZS09Jd2h6STBDQ1JmY3lRZVF3WnRidXQ4TnhsTlU1YmEvbjFpRXlydG1lUGNKakozcEVyNnl2MHREU2NNRHNKVWNNdkZnVDBqbndnQ2xTdU1RbnVWNXJBPT0iLCJtYWMiOiJhMzhhZTFjMzZiNDM3ODc2YjNlOWUyZjcxMzZhYzg0YjJhMjA0MTQ5MjQwNTVhMzBhYjZkZjExZGE1YjlkYjJkIiwidGFnIjoiIn0%3D&user=febed320dee42f56634412749978c9f5&EIO=4&transport=websocket"

# Store sent OTPs to avoid duplicates
sent_otps = set()

def extract_otp(msg):
    """Extract OTP from message"""
    if not msg:
        return None
    
    # Pattern 1: 3-3 digits (e.g., 123-456)
    m = re.search(r"\d{3}-\d{3}", msg)
    if m: 
        return m.group().replace('-', '')
    
    # Pattern 2: 4-6 digits
    m = re.search(r"\b(\d{4,6})\b", msg)
    if m: 
        return m.group(1)
    
    # Pattern 3: code: 123456
    m = re.search(r"code[:\s]*(\d{4,6})", msg, re.IGNORECASE)
    if m: 
        return m.group(1)
    
    # Pattern 4: otp: 123456
    m = re.search(r"otp[:\s]*(\d{4,6})", msg, re.IGNORECASE)
    if m: 
        return m.group(1)
    
    return None

def mask_number(num):
    """Mask number (first 3 and last 3 digits show, middle XXXX)"""
    num = re.sub(r"\D", "", num)
    if len(num) < 6: 
        return num
    return f"{num[:3]}XXXX{num[-3:]}"

def detect_service(msg):
    """Detect service from message"""
    if not msg:
        return "OTP"
    
    m = msg.lower()
    if "whatsapp" in m: 
        return "WhatsApp"
    if "telegram" in m: 
        return "Telegram"
    if "facebook" in m: 
        return "Facebook"
    if "instagram" in m: 
        return "Instagram"
    if "google" in m: 
        return "Google"
    if "amazon" in m: 
        return "Amazon"
    if "twitter" in m or "x.com" in m:
        return "Twitter"
    return "OTP"

def get_country(number):
    """Get country name and flag from phone number"""
    try:
        # Clean number and add + if not present
        clean_num = number if number.startswith('+') else '+' + number
        num = phonenumbers.parse(clean_num)
        country = geocoder.description_for_number(num, "en")
        region = phonenumbers.region_code_for_number(num)
        # Convert region code to flag emoji
        flag = "".join(chr(127397 + ord(c)) for c in region)
        return country, flag
    except:
        return "Unknown", "🌍"

def send_message(country, flag, service, number, otp, fullmsg):
    """Send message to Telegram with custom emoji buttons (DIRECT API CALL)"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Format OTP for display (3-3 digits if 6-digit)
    otp_display = f"{otp[:3]}-{otp[3:]}" if len(otp) == 6 else otp
    
    # Get service emoji ID
    service_emoji_id = CUSTOM_EMOJI.get(service.upper(), CUSTOM_EMOJI["COPY"])
    
    # HTML formatted message
    text = f"""
<b>{flag} New {country} {service} OTP !</b>

<blockquote>
⏰ Time: {now}
🌍 Country: {country}
📲 Service: {service}
📞 Number: {number}
🔑 OTP: <code>{otp}</code>
</blockquote>

📩 <b>Full Message:</b>
<blockquote>{fullmsg}</blockquote>

━━━━━━━━━━━━━━
<b>Powered By LUCKY 👑</b>
"""

    # Telegram API URL
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": [
                [
                    {
                        "text": "🏛 Number",
                        "url": "https://t.me/NumOTPV2BOT",
                        "style": "danger",  # Red button
                        "icon_custom_emoji_id": CUSTOM_EMOJI["NUMBER"]
                    },
                    {
                        "text": "👾 Developer",
                        "url": "https://t.me/ngxgod1",
                        "style": "primary",  # Blue button
                        "icon_custom_emoji_id": CUSTOM_EMOJI["TELEGRAM"]
                    }
                ],
                [
                    {
                        "text": "📢 Channel",
                        "url": "https://t.me/TeamOFDark1",
                        "style": "success",  # Green button
                        "icon_custom_emoji_id": CUSTOM_EMOJI["CHANNEL"]
                    },
                    {
                        "text": f"🟢 {otp_display}",
                        "url": "https://t.me/forwardforme1",
                        "style": "danger",  # Red button
                        "icon_custom_emoji_id": CUSTOM_EMOJI["COPY"]
                    }
                ]
            ]
        }
    }

    try:
        # Send POST request to Telegram API
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ OTP Sent: {service} | {number} | {otp}")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

async def ping(ws, interval):
    """Send ping to keep connection alive"""
    while True:
        await asyncio.sleep(interval / 1000)  # Convert to seconds
        try:
            await ws.send("3")  # WebSocket ping
        except:
            break

async def start():
    """Main WebSocket connection handler"""
    while True:
        try:
            # Connect to IVA SMS WebSocket
            async with websockets.connect(WS_URL, ping_interval=None) as ws:
                print("✅ Connected to IVA SMS")
                
                # Receive initial message with ping interval
                msg = await ws.recv()
                interval = 25000  # Default 25 seconds
                
                if msg.startswith("0{"):
                    data = json.loads(msg[1:])
                    interval = data.get("pingInterval", 25000)
                
                # Send socket.io connection message
                await ws.send("40/livesms,")
                
                # Start ping task
                asyncio.create_task(ping(ws, interval))
                
                # Main message loop
                while True:
                    data = await ws.recv()
                    
                    # Check for SMS messages
                    if data.startswith("42/livesms,"):
                        try:
                            # Parse JSON payload
                            payload = json.loads(data[data.find("["):])
                            sms = payload[1]
                            
                            message = sms.get("message", "")
                            number = sms.get("recipient", "")
                            
                            if not message or not number:
                                continue
                            
                            # Extract OTP
                            otp = extract_otp(message)
                            if not otp:
                                continue
                            
                            # Check for duplicates
                            if otp in sent_otps:
                                continue
                            sent_otps.add(otp)
                            
                            # Keep set size manageable
                            if len(sent_otps) > 1000:
                                sent_otps.clear()
                            
                            # Process message
                            service = detect_service(message)
                            country, flag = get_country(number)
                            masked = mask_number(number)
                            
                            # Send to Telegram
                            send_message(country, flag, service, masked, otp, message)
                            
                        except Exception as e:
                            print(f"❌ Error processing message: {e}")
                        
        except Exception as e:
            print(f"❌ Connection lost: {e} - Reconnecting in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    print("="*60)
    print("🚀 LUCKY IVA SMS BOT - FINAL VERSION")
    print("="*60)
    print(f"📢 Bot Token: {BOT_TOKEN[:10]}...")
    print(f"📢 Chat ID: {CHAT_ID}")
    print("="*60)
    print("✅ Custom Emoji + Coloured Buttons Enabled")
    print("✅ Direct API Call Mode")
    print("="*60)
    
    # Start the bot
    asyncio.run(start())
