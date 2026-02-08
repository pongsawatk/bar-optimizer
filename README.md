# Bar-Cut Optimizer

โปรแกรมเพิ่มประสิทธิภาพการตัดเหล็กเส้น (Bar Cutting Optimizer)

## คุณสมบัติ (Features)

- อัปโหลดไฟล์ PDF, รูปภาพ หรือ Excel ที่มีตารางข้อมูลการสั่งตัดเหล็ก
- ใช้ AI (Gemini Vision) อ่านและแปลงข้อมูลจากไฟล์อัตโนมัติ
- รองรับภาษาไทยและอังกฤษ

## การติดตั้ง (Installation)

### 1. สร้าง Virtual Environment
```bash
cd bar-cut-optimizer
python -m venv venv
venv\Scripts\activate  # Windows
# หรือ source venv/bin/activate  # Mac/Linux
```

### 2. ติดตั้ง Dependencies
```bash
pip install -r requirements.txt
```

### 3. ตั้งค่า Gemini API Key

1. รับ API Key จาก [Google AI Studio](https://aistudio.google.com/app/apikey)
2. คัดลอกไฟล์ `.env.example` เป็น `.env`
3. เพิ่ม API Key ในไฟล์ `.env`:
```
GEMINI_API_KEY=your_api_key_here
```

## การใช้งาน (Usage)

เปิดโปรแกรมด้วยคำสั่ง:
```bash
streamlit run app.py
```

แล้วเปิดเบราว์เซอร์ที่ http://localhost:8501

## โครงสร้างข้อมูล (Data Schema)

โปรแกรมจะแปลงข้อมูลเป็น JSON format:
```json
[
  {
    "bar_mark": "F1-1",
    "diameter": 16,
    "cut_length": 2.50,
    "quantity": 20
  }
]
```

- **bar_mark**: รหัสหรือชื่อเหล็ก
- **diameter**: ขนาดเส้นผ่านศูนย์กลาง (มม.)
- **cut_length**: ความยาวที่ต้องตัด (เมตร)
- **quantity**: จำนวนท่อน

## เทคโนโลยีที่ใช้ (Technologies)

- **Streamlit**: Web framework
- **Google Gemini**: AI Vision สำหรับอ่านตาราง
- **Pandas**: จัดการข้อมูล Excel
- **PyMuPDF**: แปลง PDF เป็นรูปภาพ
