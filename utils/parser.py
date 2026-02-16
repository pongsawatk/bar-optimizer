"""
Parser Module - Data Extraction from Files
โมดูลสำหรับแปลงข้อมูลจากไฟล์ต่างๆ (PDF, Images, Excel)
Optimized for Gemini 3 with system instructions and native JSON output.
"""

import json
import io
import re
from typing import List, Dict, Any, Optional
import pandas as pd
from PIL import Image
import fitz  # PyMuPDF
import google.generativeai as genai
from config import (
    DEFAULT_GEMINI_MODEL,
    GEMINI_TEMPERATURE,
    VISION_PROMPT,
    DATA_PROMPT,
    REQUIRED_FIELDS
)

# System instruction for Gemini 3 - sets the expert persona globally
SYSTEM_INSTRUCTION = """You are an expert Structural Engineer specialized in analyzing steel cutting diagrams, bar schedules, and rebar data.

Core principles:
- You extract steel bar cutting data with precision and domain expertise.
- You always return valid JSON arrays and nothing else.
- You never include markdown formatting, code blocks, explanations, or conversational text.
- You handle blurry, rotated, or low-quality images by using engineering context to infer values.
- You normalize all units: diameter in mm (integer), length in meters (float), quantity as integer.
- You skip invalid, incomplete, or header/summary rows automatically."""


class FileParser:
    """
    File Parser Class for extracting bar cutting data
    คลาสสำหรับแปลงข้อมูลการตัดเหล็กจากไฟล์
    """
    
    def __init__(self, api_key: str, model_name: str = DEFAULT_GEMINI_MODEL):
        """
        Initialize parser with Gemini API key and system instruction.
        
        Args:
            api_key: Google Gemini API key
            model_name: Name of the Gemini model to use
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name,
            system_instruction=SYSTEM_INSTRUCTION,
        )
    
    def parse_file(self, file, file_type: str) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Parse uploaded file and extract bar cutting data
        แปลงไฟล์และสกัดข้อมูลการตัดเหล็ก
        
        Args:
            file: Uploaded file object from Streamlit
            file_type: File extension (pdf, png, jpg, xlsx)
            
        Returns:
            tuple: (parsed_data_list, error_message)
        """
        try:
            if file_type in ['pdf']:
                return self._parse_pdf(file)
            elif file_type in ['png', 'jpg', 'jpeg']:
                return self._parse_image(file)
            elif file_type in ['xlsx']:
                return self._parse_excel(file)
            else:
                return [], f"ไฟล์ประเภท {file_type} ไม่รองรับ (Unsupported file type)"
                
        except Exception as e:
            return [], f"เกิดข้อผิดพลาด (Error): {str(e)}"
    
    def _parse_pdf(self, file) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Convert PDF to images and parse with Vision model
        แปลง PDF เป็นรูปภาพและใช้ Vision model อ่าน
        """
        try:
            # Read PDF
            pdf_bytes = file.read()
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            all_data = []
            
            # Process each page
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                
                # Convert page to image
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x scale for better quality
                img_bytes = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_bytes))
                
                # Parse image with Vision model
                page_data, error = self._parse_image_with_vision(image)
                
                if error:
                    return [], error
                
                all_data.extend(page_data)
            
            pdf_document.close()
            return all_data, None
            
        except Exception as e:
            return [], f"เกิดข้อผิดพลาดในการอ่าน PDF (PDF Error): {str(e)}"
    
    def _parse_image(self, file) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Parse image file with Vision model
        อ่านไฟล์รูปภาพด้วย Vision model
        """
        try:
            image = Image.open(file)
            return self._parse_image_with_vision(image)
            
        except Exception as e:
            return [], f"เกิดข้อผิดพลาดในการอ่านรูปภาพ (Image Error): {str(e)}"
    
    def _parse_image_with_vision(self, image: Image.Image) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Use Gemini Vision to extract data from image.
        Leverages system_instruction for persona and response_mime_type for clean JSON.
        """
        try:
            response = self.model.generate_content(
                [VISION_PROMPT, image],
                generation_config=genai.types.GenerationConfig(
                    temperature=GEMINI_TEMPERATURE,
                    response_mime_type="application/json",
                )
            )
            
            return self._extract_json_from_response(response)
            
        except json.JSONDecodeError as e:
            return [], f"ไม่สามารถแปลง JSON ได้ (JSON Error): {str(e)}"
        except Exception as e:
            return [], f"เกิดข้อผิดพลาดจาก Vision API (Vision API Error): {str(e)}"
    
    def _parse_excel(self, file) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Parse Excel file with Gemini LLM
        อ่านไฟล์ Excel ด้วย Gemini LLM
        """
        try:
            # Read Excel file
            df = pd.read_excel(file)
            
            # Convert to CSV string for LLM
            csv_data = df.to_csv(index=False)
            
            # Call Gemini
            return self._parse_text_with_llm(csv_data)
            
        except Exception as e:
            return [], f"เกิดข้อผิดพลาดในการอ่าน Excel (Excel Error): {str(e)}"

    def _parse_text_with_llm(self, text_data: str) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Use Gemini to extract data from text (CSV/Markdown).
        Leverages system_instruction for persona and response_mime_type for clean JSON.
        """
        try:
            response = self.model.generate_content(
                [DATA_PROMPT, text_data],
                generation_config=genai.types.GenerationConfig(
                    temperature=GEMINI_TEMPERATURE,
                    response_mime_type="application/json",
                )
            )
            
            return self._extract_json_from_response(response)
            
        except Exception as e:
             return [], f"เกิดข้อผิดพลาดจาก AI (AI Error): {str(e)}"

    def _extract_json_from_response(self, response) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Extract and validate JSON from Gemini response.
        With response_mime_type="application/json", the model returns clean JSON natively.
        Fallback stripping is kept for robustness but should rarely be needed.
        """
        try:
            response_text = response.text.strip()
            
            # Fallback: strip markdown code blocks if model still wraps them
            if response_text.startswith("```"):
                response_text = re.sub(
                    r"^```(?:json)?\s*\n?", "", response_text
                )
                response_text = re.sub(r"\n?```\s*$", "", response_text)
                response_text = response_text.strip()
            
            # Parse JSON
            data = json.loads(response_text)
            
            # Ensure top-level is a list
            if isinstance(data, dict):
                # Handle case where model wraps array in an object, e.g. {"items": [...]}
                for key in ("items", "data", "bars", "results"):
                    if key in data and isinstance(data[key], list):
                        data = data[key]
                        break
                else:
                    return [], "ข้อมูลที่ได้ไม่ใช่ array (Data is not an array)"
            
            if not isinstance(data, list):
                return [], "ข้อมูลที่ได้ไม่ใช่ array (Data is not an array)"
            
            # Validate each item
            validated_data = [
                item for item in data if self._validate_item(item)
            ]
            
            return validated_data, None
            
        except json.JSONDecodeError as e:
            return [], f"ไม่สามารถแปลง JSON ได้ (JSON Error): {str(e)}"
        except Exception as e:
            return [], f"เกิดข้อผิดพลาดในการประมวลผล (Processing Error): {str(e)}"
    
    def _find_excel_columns(self, df: pd.DataFrame) -> Optional[Dict[str, str]]:
        """
        Find matching columns in Excel file
        หาคอลัมน์ที่ตรงกับข้อมูลในไฟล์ Excel
        """
        columns = [col.lower() for col in df.columns]
        mapping = {}
        
        # Keywords for each field
        keywords = {
            "bar_mark": ["mark", "bar", "รหัส", "เหล็ก", "bar_mark"],
            "diameter": ["diameter", "dia", "ขนาด", "เส้นผ่าน", "db", "ø"],
            "cut_length": ["length", "cut", "ความยาว", "ตัด", "l"],
            "quantity": ["quantity", "qty", "จำนวน", "no", "q"]
        }
        
        # Find matching columns
        for field, field_keywords in keywords.items():
            for col_idx, col_name in enumerate(columns):
                if any(keyword in col_name for keyword in field_keywords):
                    mapping[field] = df.columns[col_idx]
                    break
        
        # Return mapping only if all fields are found
        if len(mapping) == len(REQUIRED_FIELDS):
            return mapping
        
        return None
    
    def _validate_item(self, item: Dict[str, Any]) -> bool:
        """
        Validate data item
        ตรวจสอบความถูกต้องของข้อมูล
        """
        try:
            # Check required fields
            for field in REQUIRED_FIELDS:
                if field not in item:
                    return False
            
            # Check data types
            if not isinstance(item["bar_mark"], str) or not item["bar_mark"]:
                return False
            
            if not isinstance(item["diameter"], int) or item["diameter"] <= 0:
                return False
            
            if not isinstance(item["cut_length"], (int, float)) or item["cut_length"] <= 0:
                return False
            
            if not isinstance(item["quantity"], int) or item["quantity"] <= 0:
                return False
            
            return True
            
        except Exception:
            return False


def create_dataframe(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert parsed data to Pandas DataFrame
    แปลงข้อมูลเป็น Pandas DataFrame
    
    Args:
        data: List of parsed bar cutting data
        
    Returns:
        pd.DataFrame: Formatted dataframe
    """
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    
    # Reorder columns
    df = df[REQUIRED_FIELDS]
    
    return df
