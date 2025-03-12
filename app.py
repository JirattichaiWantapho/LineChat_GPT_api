import openai
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# API Keys
openai.api_key = os.getenv("OPENAI_API_KEY")
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")

app = Flask(__name__)

# FAQ Responses
faq_responses = {
    "ตั้งรหัสผ่าน": "รหัสผ่านต้องมีอย่างน้อย 8-16 ตัวอักษร และต้องมีตัวพิมพ์ใหญ่ ตัวพิมพ์เล็ก ตัวเลข และอักขระพิเศษ (!@#ฯลฯ)",
    "วิธีตั้งรหัสผ่าน": "การตั้งรหัสผ่านใหม่สามารถทำได้ในหน้า 'ตั้งรหัสผ่าน' บนเว็บไซต์ของเรา",
    "การสร้างรหัสผ่าน": "รหัสผ่านต้องมีความยาวระหว่าง 8-16 ตัวอักษร และต้องประกอบด้วยตัวพิมพ์ใหญ่ ตัวพิมพ์เล็ก ตัวเลข และอักขระพิเศษ",
    "เปลี่ยนรหัสผ่าน": "คุณสามารถเปลี่ยนรหัสผ่านได้ที่หน้า Change Password บนเว็บไซต์",
    "ลืมรหัสผ่าน": "คุณสามารถรีเซ็ตรหัสผ่านได้ที่ Reset Password บนเว็บไซต์ หรือ ติดต่อ IT Support",
    "VPN ใช้งานไม่ได้": "กรุณาตรวจสอบการเชื่อมต่ออินเทอร์เน็ต และลองรีสตาร์ทอุปกรณ์ของคุณ",
    "ขอสิทธิ์เข้าระบบ": "กรุณาส่งคำขอไปที่ Test@example.com พร้อมแจ้งเหตุผลและข้อมูลบัญชีของคุณ",
    "ติดต่อ IT Support": "คุณสามารถติดต่อ IT Support ได้ที่เบอร์ 02-123-4567 หรืออีเมล support@example.com",
    "การยืนยันตัวตนสองขั้นตอน": "ระบบรองรับการยืนยันตัวตนแบบสองขั้นตอน (2FA) ซึ่งสามารถตั้งค่าได้จากหน้า Profile Settings",
    "การล็อกอินผิดหลายครั้ง": "หากมีการพยายามล็อกอินผิดหลายครั้ง ระบบจะทำการล็อกบัญชีของคุณชั่วคราว และคุณจะต้องติดต่อ IT Support เพื่อขอปลดล็อก",
    "สวัสดี": "สวัสดีครับ อยากให้ช่วยเรื่องไหนบอกได้เลยครับ",
}

# ฟังก์ชันให้ AI วิเคราะห์ข้อความ
def detect_intent(user_message):
    # ปรับปรุง prompt ใหม่ให้มีคำอธิบายเพิ่มเติม
    prompt = f"""
    ผู้ใช้ส่งข้อความมาถามว่า: "{user_message}"
    ข้อความนี้เกี่ยวข้องกับหัวข้อใดต่อไปนี้มากที่สุด:
    
    1. ตั้งรหัสผ่าน
    2. วิธีตั้งรหัสผ่าน
    3. การสร้างรหัสผ่าน
    4. เปลี่ยนรหัสผ่าน
    5. ลืมรหัสผ่าน
    6. VPN ใช้งานไม่ได้
    7. ขอสิทธิ์เข้าระบบ
    8. ติดต่อ IT Support
    9. การยืนยันตัวตนสองขั้นตอน
    10. การล็อกอินผิดหลายครั้ง
    11. สวัสดี
    12. อื่นๆ (หากไม่มีหัวข้อที่ตรง)

    ตอบกลับเฉพาะ **ชื่อหัวข้อที่ตรงที่สุด** เช่น `"ตั้งรหัสผ่าน"` หรือ `"เปลี่ยนรหัสผ่าน"` เท่านั้น  
    ห้ามตอบอย่างอื่นที่นอกเหนือจาก 1 ใน 12 ตัวเลือกนี้  
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "คุณเป็นระบบจับคู่คำถามอัตโนมัติ"},
            {"role": "user", "content": prompt}
        ]
    )

    intent = response["choices"][0]["message"]["content"].strip()

    # ตรวจสอบ intent ว่าอยู่ใน faq_responses หรือไม่
    for key in faq_responses:
        if key.lower() in intent.lower():  # ตรวจสอบโดยไม่สนตัวพิมพ์ใหญ่-เล็ก
            if key == "สวัสดี":
                return faq_responses[key]

            return f"คุณหมายถึง '{key}' ใช่หรือไม่?\n\n{faq_responses[key]}"

    # กรณี AI ไม่สามารถวิเคราะห์ intent ได้
    return "ขออภัย ฉันไม่เข้าใจคำถามของคุณ กรุณาลองพิมพ์ใหม่ หรือ กดที่เมนูติดต่อแอดมิน"


# ฟังก์ชันส่งข้อความกลับ LINE
def reply_to_line(reply_token, message):
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    data = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": message}]
    }
    response = requests.post(url, headers=headers, json=data)
    print(response.status_code, response.text)  # Debug response


# รับ Webhook จาก LINE
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print(data)  # Debug JSON input

    if "events" in data and len(data["events"]) > 0:
        event = data["events"][0]
        user_message = event["message"]["text"]
        reply_token = event["replyToken"]

        ai_response = detect_intent(user_message)  # วิเคราะห์คำถาม
        reply_to_line(reply_token, ai_response)   # ตอบกลับไปยัง LINE

    return "OK", 200


# เพิ่มเส้นทางสำหรับหน้าแรก
@app.route("/")
def home():
    return "Hello, this is the home page!"


if __name__ == "__main__":
    app.run(port=5000, debug=True)
