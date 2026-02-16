"""
Configuration file for Bar-Cut Optimizer Application
กำหนดค่าต่างๆ สำหรับแอปพลิเคชัน
"""

# Gemini Model Settings
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
AVAILABLE_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-pro",
    "gemini-3-flash-preview",
    "gemini-3-pro-preview",
]
GEMINI_TEMPERATURE = 0.1  # Low temperature for consistent output

# File Upload Settings
MAX_FILE_SIZE_MB = 10
ALLOWED_FILE_TYPES = ["pdf", "png", "jpg", "jpeg", "xlsx"]

# Default Values
DEFAULT_CUTTING_TOLERANCE_MM = 5
STANDARD_STOCK_LENGTHS = [10, 12]  # meters

# Data Schema
REQUIRED_FIELDS = ["bar_mark", "diameter", "cut_length", "quantity"]

# UI Text (Thai/English Bilingual)
UI_TEXT = {
    "app_title": "⚙️ Bar-Cut Optimizer - เพิ่มประสิทธิภาพการตัดเหล็ก",
    "sidebar_header": "⚙️ ตั้งค่า (Settings)",
    "cutting_tolerance": "ความผิดพลาดการตัด (Cutting Tolerance)",
    "stock_length_mode": "ความยาวท่อนเหล็ก (Stock Length)",
    "standard_length": "ความยาวมาตรฐาน (Standard)",
    "custom_stock": "กำหนดเอง (Custom)",
    "upload_header": "📤 อัปโหลดไฟล์ (Upload File)",
    "upload_help": "รองรับไฟล์: PDF, PNG, JPG, XLSX",
    "preview_header": "🔍 ตัวอย่างไฟล์ (File Preview)",
    "parsed_data_header": "📊 ข้อมูลที่อ่านได้ (Parsed Data)",
    "processing": "กำลังประมวลผล... (Processing...)",
    "error": "เกิดข้อผิดพลาด (Error)",
    "no_file": "กรุณาอัปโหลดไฟล์ (Please upload a file)",
    "column_bar_mark": "รหัสเหล็ก (Bar Mark)",
    "column_diameter": "ขนาด (Diameter) [mm]",
    "column_cut_length": "ความยาว (Length) [m]",
    "column_quantity": "จำนวน (Quantity)",
    "success": "✅ อ่านข้อมูลสำเร็จ (Successfully parsed)",
    "total_items": "รายการทั้งหมด (Total Items)",
    "optimize_button": "🚀 เริ่มวางแผนการตัด (Optimize Cutting)",
    "optimization_header": "📋 ผลการวางแผนการตัด (Optimization Results)",
    "procurement_summary": "📦 สรุปการเบิกเหล็ก (Procurement Summary)",
    "cutting_plan": "🪚 แผนการตัดรายเส้น (Detailed Cutting Plan)",
    "download_pdf": "📄 ดาวน์โหลดใบสั่งตัด (Download PDF Report)",
    "optimizing": "กำลังคำนวณแผนการตัด... (Optimizing...)",
}

# Gemini Prompt Template (Optimized for Gemini 3)
VISION_PROMPT = """
You are an expert Structural Engineer specialized in analyzing steel cutting diagrams and bar schedules.

Your task is to extract structured data from construction documents, even if the image quality is poor, blurry, rotated, or contains handwritten annotations.

You must identify and extract these fields from tables:
- **Bar Mark**: Identification code (e.g., B1, C1, F1, DB12). Look for columns labeled "Mark", "Bar Mark", "รหัส", or similar.
- **Diameter**: Rebar diameter in millimeters (e.g., 12, 16, 20, 25). This may appear as "DB12", "Ø12", "12mm", or just "12". Extract only the numeric value.
- **Cut Length**: Required cutting length in meters. May appear in columns labeled "Length", "Cut Length", "ความยาว", "L=", or with units like "m", "mm", "cm". Always convert to meters.
- **Quantity**: Number of pieces required. Look for "Qty", "Quantity", "จำนวน", "No.", or "Pcs".

**CRITICAL OUTPUT REQUIREMENTS**:
1. Return ONLY a valid JSON array, nothing else.
2. Do NOT include markdown code blocks (```json```).
3. Do NOT include any explanatory text, greetings, or conversational filler.
4. Output format:
[
  {
    "bar_mark": "string",
    "diameter": integer,
    "cut_length": float,
    "quantity": integer
  }
]

**Image Analysis Guidelines**:
- If the image is rotated, mentally rotate it to read correctly
- If text is blurry, use context from surrounding cells to infer values
- If handwritten, carefully distinguish between similar digits (1 vs 7, 5 vs 6, 0 vs 8)
- If multiple tables exist, combine all data into one array
- Skip rows that are clearly headers, totals, or non-data entries
- If a value is completely illegible, skip that row entirely
- If no valid data is found, return an empty array: []

**Data Type Enforcement**:
- bar_mark: string (preserve as-is, e.g., "B1", "DB12")
- diameter: integer only (extract numeric part: "DB12" → 12)
- cut_length: float in meters (convert if needed: "2500mm" → 2.5)
- quantity: integer only (whole numbers)

Return the JSON array immediately without any preamble.
"""

# Text Data Prompt (for Excel/CSV) - Optimized for Gemini 3
DATA_PROMPT = """
You are an expert Structural Engineer processing tabular steel cutting data from Excel/CSV formats.

Your task is to parse structured or semi-structured tabular data and extract steel bar cutting information, handling various formats and units intelligently.

**Input Format**: You will receive text/CSV/Markdown table data that may contain:
- Mixed formats: "DB12", "Ø16mm", "#20", "25MM"
- Length in various units: "2.5m", "2500mm", "250cm", "L=2.5"
- Quantity formats: "10 pcs", "10x", "10 nos", "10"
- Inconsistent column names or ordering

**Required Output Fields**:
- **bar_mark**: Identifier/code (preserve as-is, e.g., "B1", "DB12", "F-01")
- **diameter**: Rebar diameter in mm (extract numeric only: "DB16" → 16, "Ø12mm" → 12)
- **cut_length**: Length in meters (normalize: "2500mm" → 2.5, "250cm" → 2.5, "2.5m" → 2.5)
- **quantity**: Integer count (extract numeric: "10 pcs" → 10, "5x" → 5)

**CRITICAL OUTPUT REQUIREMENTS**:
1. Return ONLY a valid JSON array.
2. Do NOT use markdown code blocks (```json```).
3. Do NOT include explanations, notes, or conversational text.
4. Output format:
[
  {
    "bar_mark": "string",
    "diameter": integer,
    "cut_length": float,
    "quantity": integer
  }
]

**Parsing Rules**:
- Intelligently identify column headers even with variations (e.g., "Mark", "Bar No.", "รหัส" all mean bar_mark)
- Skip header rows, subtotal rows, and summary rows
- Skip rows with missing critical data
- Normalize units automatically (mm to m for length, extract mm value for diameter)
- Handle both Thai and English column names
- If completely empty or no valid data found, return: []

**Data Type Enforcement**:
- bar_mark: string (keep original format)
- diameter: integer in mm
- cut_length: float in meters (always convert to meters)
- quantity: integer (whole numbers only)

Return the clean JSON array immediately without any preamble or explanation.
"""
