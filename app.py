"""
Bar-Cut Optimizer - Main Application
แอปพลิเคชันเพิ่มประสิทธิภาพการตัดเหล็กเส้น

This Streamlit app allows users to upload files (PDF, images, Excel) 
containing bar cutting requirements and automatically extracts the data 
using AI vision models.
"""

import streamlit as st
import os
from dotenv import load_dotenv
from PIL import Image
import pandas as pd
from io import BytesIO
from datetime import datetime

from config import (
    UI_TEXT,
    DEFAULT_CUTTING_TOLERANCE_MM,
    STANDARD_STOCK_LENGTHS,
    ALLOWED_FILE_TYPES,
    MAX_FILE_SIZE_MB,
    AVAILABLE_MODELS,
    DEFAULT_GEMINI_MODEL
)
from utils.parser import FileParser, create_dataframe
from utils.optimizer import optimize_cutting
from utils.pdf_generator import generate_cutting_report


# Load environment variables
load_dotenv()


def init_session_state():
    """Initialize Streamlit session state variables"""
    if 'parsed_data' not in st.session_state:
        st.session_state.parsed_data = None
    if 'uploaded_file_name' not in st.session_state:
        st.session_state.uploaded_file_name = None
    if 'optimization_result' not in st.session_state:
        st.session_state.optimization_result = None
    if 'stock_length' not in st.session_state:
        st.session_state.stock_length = 10
    if 'cutting_tolerance' not in st.session_state:
        st.session_state.cutting_tolerance = 5
    if 'enable_splicing' not in st.session_state:
        st.session_state.enable_splicing = False
    if 'lap_factor' not in st.session_state:
        st.session_state.lap_factor = 40


def display_file_preview(file, file_type: str):
    """
    Display preview of uploaded file
    แสดงตัวอย่างไฟล์ที่อัปโหลด
    """
    st.subheader(UI_TEXT["preview_header"])
    
    if file_type in ['png', 'jpg', 'jpeg']:
        # Display image
        image = Image.open(file)
        st.image(image, use_container_width=True)
        file.seek(0)  # Reset file pointer
        
    elif file_type == 'pdf':
        # Show PDF info
        st.info(f"📄 PDF File: {file.name}")
        st.caption("PDF จะถูกแปลงเป็นรูปภาพเพื่อประมวลผล (PDF will be converted to images for processing)")
        
    elif file_type == 'xlsx':
        # Show Excel preview
        try:
            df = pd.read_excel(file)
            st.dataframe(df.head(10), use_container_width=True)
            file.seek(0)  # Reset file pointer
        except Exception as e:
            st.error(f"ไม่สามารถแสดงตัวอย่าง Excel (Cannot preview Excel): {str(e)}")


def main():
    """Main application function"""
    
    # Page configuration
    st.set_page_config(
        page_title="Bar-Cut Optimizer",
        page_icon="🏗️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    init_session_state()
    
    # Custom CSS for Pure Light Mode & Glassmorphism
    st.markdown("""
    <style>
        /* Import Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Kanit:wght@300;400;600&display=swap');
        
        /* Global Font Settings */
        html, body, [data-testid="stSidebar"], .stApp {
            font-family: 'Kanit', 'Inter', sans-serif !important;
        }

        /* 1. Global Light Theme & Glass Effect */
        .stApp {
            background: linear-gradient(135deg, #F5F7FA 0%, #C3CFE2 100%);
            background-attachment: fixed; /* พื้นหลังไม่เลื่อนตาม */
        }
        
        /* 2. Sidebar Styling (Light Gray Theme) */
        section[data-testid="stSidebar"] {
            background-color: #EBEDF0 !important; /* สีเทาที่เข้มกว่า Main Area นิดหน่อย */
            border-right: 1px solid #D1D5DB;
        }
        /* ปรับสีตัวหนังสือใน Sidebar ให้เข้มชัด */
        section[data-testid="stSidebar"] * {
            color: #333333 !important;
        }
        /* ลดช่องว่าง Sidebar (Compact) */
        div[data-testid="stSidebarUserContent"] {
            padding-top: 0.5rem !important;
        }
        section[data-testid="stSidebar"] .stElementContainer {
            margin-bottom: -0.2rem;
        }

        /* 3. Main Content Glass Containers */
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
            background: rgba(255, 255, 255, 0.75); /* เพิ่มความทึบแสงให้อ่านง่ายขึ้น */
            backdrop-filter: blur(12px);
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.6);
        }

        /* 4. Header Redesign (Slim & Clean) */
        header[data-testid="stHeader"] {
            background: rgba(255, 255, 255, 0.95) !important;
            height: 3rem !important; /* ลดความสูง */
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        header[data-testid="stHeader"]::before {
           content: "⚙️ Bar-Cut Optimizer : วางแผนการตัดเหล็กจาก Bar Cutting List";
            position: absolute;
            left: 1rem;
            top: 50%;
            transform: translateY(-50%);
            font-family: 'Kanit', sans-serif;
            font-size: 1.1rem;
            font-weight: 600;
            color: #0072CE;
            z-index: 999;
        }
        
        /* Adjust Toolbar Position */
        [data-testid="stToolbar"] { 
            right: 1rem; 
            top: 0.5rem; 
        }

        /* 5. Sticky Footer (Powered by...) */
        .sticky-footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: rgba(255, 255, 255, 0.9);
            color: #555;
            text-align: center;
            padding: 10px 0;
            font-size: 0.8rem;
            border-top: 1px solid #ddd;
            z-index: 1000;
            backdrop-filter: blur(5px);
        }
        /* ดันเนื้อหาขึ้นเพื่อไม่ให้ Footer บัง */
        .main .block-container {
            padding-bottom: 60px;
            padding-top: 4rem; /* Give space for fixed header */
            max-width: 95% !important;
        }
        /* ซ่อน Footer เดิมของ Streamlit */
        footer {visibility: hidden;}
        
        /* 6. Component Styling Fixes */
        /* Primary Buttons */
        div.stButton > button:first-child {
            background-color: #0072CE;
            color: white;
            border-radius: 8px;
            border: none;
            padding: 0.5rem 1.5rem;
            font-weight: 500;
            box-shadow: 0 2px 6px rgba(0, 114, 206, 0.2);
            transition: all 0.2s ease;
        }
        div.stButton > button:first-child:hover {
            background-color: #0056a3;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 114, 206, 0.3);
        }
        
        /* Metrics & Cards */
        div[data-testid="stMetric"] {
            background-color: rgba(255, 255, 255, 0.85) !important;
            padding: 15px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            border: 1px solid rgba(255, 255, 255, 0.7);
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background: transparent;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: rgba(255, 255, 255, 0.6);
            border-radius: 8px 8px 0 0;
            padding: 8px 16px;
            font-size: 0.95rem;
            color: #333333;
        }
        .stTabs [aria-selected="true"] {
            background-color: #0072CE !important;
            color: white !important;
            box-shadow: 0 -2px 10px rgba(0, 114, 206, 0.15);
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Sticky Footer
    st.markdown("""
        <div class="sticky-footer">
            Powered by <b>Contech BU (Builk One Group)</b> | 🛠️ Constructed for Free Use by Contractors & Engineers
        </div>
    """, unsafe_allow_html=True)
    
    # App title removed (Handled by CSS Header)
    
    # Sidebar - Settings
    with st.sidebar:
        # Branding Section (Top of Sidebar)
        try:
            st.image("contech_logo.png", use_container_width=True)
        except FileNotFoundError:
            st.warning("ไม่พบไฟล์โลโก้ (contech_logo.png)")
        st.markdown("---")
        
        st.header(UI_TEXT["sidebar_header"])
        
        # Cutting tolerance input
        cutting_tolerance = st.number_input(
            label=UI_TEXT["cutting_tolerance"],
            min_value=0,
            max_value=20,
            value=DEFAULT_CUTTING_TOLERANCE_MM,
            step=1,
            help="ระยะเผื่อสำหรับใบตัด (Allowance for cutting blade)"
        )
        st.caption(f"ค่าปัจจุบัน (Current): {cutting_tolerance} mm")
        
        st.markdown("---")
        
        # Stock length mode
        st.subheader(UI_TEXT["stock_length_mode"])
        
        stock_mode = st.radio(
            label="เลือกโหมด (Select Mode)",
            options=["standard", "custom"],
            format_func=lambda x: UI_TEXT["standard_length"] if x == "standard" else UI_TEXT["custom_stock"],
            index=0,
            label_visibility="collapsed"
        )
        
        if stock_mode == "standard":
            # Standard length selection
            standard_length = st.selectbox(
                label="ความยาว (Length)",
                options=STANDARD_STOCK_LENGTHS,
                format_func=lambda x: f"{x} m",
                index=0
            )
            st.success(f"✅ ใช้ความยาว {standard_length} m")
            
        else:
            # Custom stock - placeholder
            st.info("🚧 ฟีเจอร์นี้กำลังพัฒนา (Feature in development)")
            st.caption("จะสามารถอัปโหลด CSV หรือใส่ตารางกำหนดเองได้ในอนาคต")
        
        st.markdown("---")
        
        # Splicing Configuration
        st.subheader("⚙️ ตั้งค่าการต่อเหล็ก (Splicing)")
        
        enable_splicing = st.checkbox(
            label="เปิดใช้งานคำนวณระยะทาบ (Enable Auto-Splicing)",
            value=st.session_state.enable_splicing,
            help="แยกเหล็กที่ยาวเกิน Stock Length อัตโนมัติ"
        )
        
        if enable_splicing:
            lap_factor = st.number_input(
                label="ระยะทาบ (Lap Length Factor)",
                min_value=30,
                max_value=60,
                value=st.session_state.lap_factor,
                step=5,
                help="ค่ามาตรฐานทั่วไป: 40d สำหรับเหล็กข้ออ้อย"
            )
            st.caption(f"หน่วย: เท่าของเส้นผ่าศูนย์กลาง ({lap_factor}d)")
            
            # Store in session state
            st.session_state.enable_splicing = enable_splicing
            st.session_state.lap_factor = lap_factor
        else:
            st.session_state.enable_splicing = False
        
        st.markdown("---")
        
        # Model Selection
        st.subheader("🤖 AI Model")
        selected_model = st.selectbox(
            label="เลือกโมเดล (Select Model)",
            options=AVAILABLE_MODELS,
            index=AVAILABLE_MODELS.index(DEFAULT_GEMINI_MODEL) if DEFAULT_GEMINI_MODEL in AVAILABLE_MODELS else 0
        )
        st.caption(f"Current: {selected_model}")
        
        st.markdown("---")
        
        # API Key status
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key and api_key != "your_gemini_api_key_here":
            st.success("🔑 API Key: ✅ Configured")
        else:
            st.error("🔑 API Key: ❌ ยังไม่ได้ตั้งค่า (Not configured)")
            st.caption("กรุณาตั้งค่า GEMINI_API_KEY ในไฟล์ .env")
    
    # Main area - File upload and preview
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header(UI_TEXT["upload_header"])
        
        # File uploader
        uploaded_file = st.file_uploader(
            label="อัปโหลดไฟล์ที่นี่ (Upload file here)",
            type=ALLOWED_FILE_TYPES,
            help=UI_TEXT["upload_help"],
            label_visibility="collapsed"
        )
        
        if uploaded_file:
            # Get file info
            file_size_mb = uploaded_file.size / (1024 * 1024)
            file_type = uploaded_file.name.split('.')[-1].lower()
            
            # Display file info
            st.info(f"📁 **ไฟล์ (File):** {uploaded_file.name}")
            st.caption(f"ขนาด (Size): {file_size_mb:.2f} MB | ประเภท (Type): {file_type.upper()}")
            
            # Check file size
            if file_size_mb > MAX_FILE_SIZE_MB:
                st.error(f"❌ ไฟล์ใหญ่เกินไป (File too large): {file_size_mb:.2f} MB > {MAX_FILE_SIZE_MB} MB")
                return
            
            # Process button
            if st.button("🚀 ประมวลผลไฟล์ (Process File)", type="primary", use_container_width=True):
                process_file(uploaded_file, file_type, selected_model)
    
    with col2:
        if uploaded_file:
            display_file_preview(uploaded_file, file_type)
    
    # Display parsed data
    if st.session_state.parsed_data is not None and len(st.session_state.parsed_data) > 0:
        st.markdown("---")
        st.header(UI_TEXT["parsed_data_header"])
        
        # Create dataframe
        df = create_dataframe(st.session_state.parsed_data)
        
        # Rename columns for display (bilingual)
        df_display = df.copy()
        df_display.columns = [
            UI_TEXT["column_bar_mark"],
            UI_TEXT["column_diameter"],
            UI_TEXT["column_cut_length"],
            UI_TEXT["column_quantity"]
        ]
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(UI_TEXT["total_items"], len(df))
        with col2:
            st.metric("ขนาดต่างๆ (Sizes)", df['diameter'].nunique())
        with col3:
            st.metric("จำนวนรวม (Total Qty)", df['quantity'].sum())
        with col4:
            total_length = (df['cut_length'] * df['quantity']).sum()
            st.metric("ความยาวรวม (Total Length)", f"{total_length:.2f} m")
        
        # Splicing info (if exists)
        if st.session_state.get('splicing_info') and st.session_state.enable_splicing:
            splicing_info = st.session_state.splicing_info
            if splicing_info['total_spliced'] > 0:
                st.warning(
                    f"⚠️ พบ {splicing_info['total_spliced']} รายการที่ยาวเกิน Stock Length "
                    f"→ แยกเป็น {splicing_info['additional_pieces']} ชิ้นเพิ่มเติม "
                    f"(รวม {splicing_info['final_count']} รายการหลังแยก)"
                )
                # Show spliced data instead
                df = pd.DataFrame(st.session_state.spliced_data)
                df_display = df.copy()
                if 'note' in df_display.columns:
                    df_display['note'] = df_display['note'].fillna('')
        
        # Display table
        st.dataframe(df_display, use_container_width=True, height=400)
        
        # Success message
        st.success(f"{UI_TEXT['success']} - {len(df)} รายการ (items)")
        
        # Download button for CSV
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 ดาวน์โหลด CSV (Download CSV)",
            data=csv,
            file_name="bar_cutting_data.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        # Optimization section
        st.markdown("---")
        st.header(UI_TEXT["optimization_header"])
        
        # Optimize button
        if st.button(UI_TEXT["optimize_button"], type="primary", use_container_width=True):
            with st.spinner(UI_TEXT["optimizing"]):
                # Get stock length from sidebar
                stock_length = standard_length if stock_mode == "standard" else 10
                
                # Store in session state for later use (PDF generation)
                st.session_state.stock_length = stock_length
                st.session_state.cutting_tolerance = cutting_tolerance
                
                # Apply splicing if enabled
                data_to_optimize = st.session_state.parsed_data
                if st.session_state.enable_splicing:
                    from utils.optimizer import apply_engineering_splicing
                    data_to_optimize, splicing_info = apply_engineering_splicing(
                        st.session_state.parsed_data,
                        stock_length,
                        st.session_state.lap_factor
                    )
                    st.session_state.splicing_info = splicing_info
                    st.session_state.spliced_data = data_to_optimize
                else:
                    st.session_state.splicing_info = None
                    st.session_state.spliced_data = None
                
                # Run optimization
                result = optimize_cutting(
                    data_to_optimize,
                    stock_length,
                    cutting_tolerance
                )
                st.session_state.optimization_result = result
                st.rerun()
        
        # Display optimization results
        if st.session_state.optimization_result is not None:
            result = st.session_state.optimization_result
            
            # Procurement Summary
            st.subheader(UI_TEXT["procurement_summary"])
            
            summary_df = pd.DataFrame(result.procurement_summary)
            summary_df.columns = [
                "ขนาด (Diameter) [mm]",
                "ความยาวท่อน (Stock) [m]",
                "จำนวนเส้น (Quantity)",
                "ความยาวรวม (Total) [m]",
                "เศษเหลือ (Waste) [m]",
                "% เศษ (Waste %)",
                "น้ำหนักรวม (Weight) [kg]"
            ]
            
            # Format columns
            summary_df["ขนาด (Diameter) [mm]"] = summary_df["ขนาด (Diameter) [mm]"].apply(lambda x: f"DB{x}")
            summary_df["ความยาวรวม (Total) [m]"] = summary_df["ความยาวรวม (Total) [m]"].apply(lambda x: f"{x:.2f}")
            summary_df["เศษเหลือ (Waste) [m]"] = summary_df["เศษเหลือ (Waste) [m]"].apply(lambda x: f"{x:.2f}")
            summary_df["% เศษ (Waste %)"] = summary_df["% เศษ (Waste %)"].apply(lambda x: f"{x:.1f}%")
            summary_df["น้ำหนักรวม (Weight) [kg]"] = summary_df["น้ำหนักรวม (Weight) [kg]"].apply(lambda x: f"{x:.2f}")
            
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("รวมจำนวนเส้น (Total Bars)", result.total_stock_used)
            with col2:
                st.metric("เศษรวม (Total Waste)", f"{result.total_waste:.2f} m")
            with col3:
                total_length = sum(item['total_length'] for item in result.procurement_summary)
                waste_pct = (result.total_waste / total_length * 100) if total_length > 0 else 0
                st.metric("% เศษโดยเฉลี่ย (Avg Waste %)", f"{waste_pct:.1f}%")
            with col4:
                st.metric("น้ำหนักรวม (Total Weight)", f"{result.total_weight:.2f} kg")
            
            st.markdown("---")
            
            # Remnant Summary
            st.subheader("🔄 สรุปเศษเหล็กที่เหลือ (Remnant Summary)")
            
            remnant_col1, remnant_col2 = st.columns(2)
            
            with remnant_col1:
                st.write("**♻️ เศษใช้งานต่อได้ (Reusable) - ยาว ≥ 1.0m**")
                if result.remnant_summary['reusable']:
                    reusable_data = []
                    for rem in result.remnant_summary['reusable']:
                        reusable_data.append({
                            "เส้นที่": rem['stock_id'],
                            "ขนาด": f"DB{rem['diameter']}",
                            "ความยาว (m)": f"{rem['length']:.2f}",
                            "น้ำหนัก (kg)": f"{rem['weight']:.2f}"
                        })
                    reusable_df = pd.DataFrame(reusable_data)
                    st.dataframe(reusable_df, use_container_width=True, hide_index=True)
                    
                    total_reusable_length = sum(rem['length'] for rem in result.remnant_summary['reusable'])
                    total_reusable_weight = sum(rem['weight'] for rem in result.remnant_summary['reusable'])
                    st.success(f"รวม: {len(result.remnant_summary['reusable'])} ชิ้น | {total_reusable_length:.2f} m | {total_reusable_weight:.2f} kg")
                else:
                    st.info("ไม่มีเศษที่สามารถใช้ได้")
            
            with remnant_col2:
                st.write("**🗑️ เศษทิ้ง (Scrap) - ยาว < 1.0m**")
                if result.remnant_summary['scrap']:
                    scrap_data = []
                    for rem in result.remnant_summary['scrap']:
                        scrap_data.append({
                            "เส้นที่": rem['stock_id'],
                            "ขนาด": f"DB{rem['diameter']}",
                            "ความยาว (m)": f"{rem['length']:.2f}",
                            "น้ำหนัก (kg)": f"{rem['weight']:.2f}"
                        })
                    scrap_df = pd.DataFrame(scrap_data)
                    st.dataframe(scrap_df, use_container_width=True, hide_index=True)
                    
                    total_scrap_length = sum(rem['length'] for rem in result.remnant_summary['scrap'])
                    total_scrap_weight = sum(rem['weight'] for rem in result.remnant_summary['scrap'])
                    st.warning(f"รวม: {len(result.remnant_summary['scrap'])} ชิ้น | {total_scrap_length:.2f} m | {total_scrap_weight:.2f} kg")
                else:
                    st.info("ไม่มีเศษทิ้ง")
            
            st.markdown("---")
            
            # Detailed Cutting Plan
            st.subheader(UI_TEXT["cutting_plan"])
            
            # Group by diameter
            plan_by_diameter = {}
            for stock in result.cutting_plan:
                if stock.diameter not in plan_by_diameter:
                    plan_by_diameter[stock.diameter] = []
                plan_by_diameter[stock.diameter].append(stock)
            
            for diameter in sorted(plan_by_diameter.keys()):
                stocks = plan_by_diameter[diameter]
                st.write(f"### ขนาด DB{diameter} mm")
                
                # Create plan data
                plan_data = []
                for stock in stocks:
                    # Add each cut
                    for i, cut in enumerate(stock.cuts):
                        if i == 0:
                            plan_data.append({
                                "เส้นที่ (Stock #)": str(stock.stock_id),
                                "รหัสเหล็ก (Bar Mark)": cut['bar_mark'],
                                "ความยาว (Length) [m]": f"{cut['length']:.2f}",
                                "ตำแหน่ง (Position) [m]": f"{cut['start']:.2f} - {cut['end']:.2f}",
                                "เศษเหลือ (Waste) [m]": f"{stock.remaining:.2f}",
                                "% ใช้งาน (Utilization)": f"{stock.utilization:.1f}%"
                            })
                        else:
                            plan_data.append({
                                "เส้นที่ (Stock #)": "",
                                "รหัสเหล็ก (Bar Mark)": cut['bar_mark'],
                                "ความยาว (Length) [m]": f"{cut['length']:.2f}",
                                "ตำแหน่ง (Position) [m]": f"{cut['start']:.2f} - {cut['end']:.2f}",
                                "เศษเหลือ (Waste) [m]": "",
                                "% ใช้งาน (Utilization)": ""
                            })
                
                plan_df = pd.DataFrame(plan_data)
                st.dataframe(plan_df, use_container_width=True, hide_index=True)
                
                # Visual bars
                st.write("**แผนภาพการใช้งาน (Utilization Visualization)**")
                for stock in stocks:
                    # Create visual bar
                    utilized = ((stock.stock_length - stock.remaining) / stock.stock_length) * 100
                    waste = (stock.remaining / stock.stock_length) * 100
                    
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.progress(utilized / 100, text=f"เส้นที่ {stock.stock_id}: {utilized:.1f}% ใช้งาน, {waste:.1f}% เศษ")
                    with col2:
                        st.caption(f"{stock.remaining:.2f}m waste")
                
                st.markdown("---")
            
            # PDF Download
            st.subheader(UI_TEXT["download_pdf"])
            
            if st.button("🔄 สร้าง PDF Report", use_container_width=True):
                with st.spinner("กำลังสร้างรายงาน... (Generating report...)"):
                    try:
                        pdf_buffer = generate_cutting_report(
                            result.procurement_summary,
                            result.cutting_plan,
                            result.total_waste,
                            st.session_state.stock_length,
                            st.session_state.cutting_tolerance,
                            result.remnant_summary,
                            result.total_weight,
                            project_name=f"Project - {st.session_state.uploaded_file_name or 'Unknown'}",
                            splicing_enabled=st.session_state.enable_splicing,
                            lap_factor=st.session_state.lap_factor
                        )
                        
                        st.download_button(
                            label="📥 ดาวน์โหลด PDF",
                            data=pdf_buffer,
                            file_name=f"cutting_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                        st.success("✅ สร้างรายงานสำเร็จ!")
                    except Exception as e:
                        st.error(f"เกิดข้อผิดพลาดในการสร้าง PDF: {str(e)}")
    
    # Footer with branding
    st.markdown("""
        <div class="footer">
            <p>Powered by <strong>Contech BU (Builk One Group)</strong> | 🛠️ Constructed for Free Use by Contractors & Engineers</p>
        </div>
    """, unsafe_allow_html=True)


def process_file(file, file_type: str, model_name: str):
    """
    Process uploaded file and extract data
    ประมวลผลไฟล์และสกัดข้อมูล
    """
    # Check API key
    import streamlit as st
# ดึงค่าจาก secrets.toml
api_key = st.secrets["GEMINI_API_KEY"]
    if not api_key or api_key == "your_gemini_api_key_here":
        st.error("❌ กรุณาตั้งค่า GEMINI_API_KEY ในไฟล์ .env (Please configure GEMINI_API_KEY in .env file)")
        st.info("📖 อ่านวิธีตั้งค่าได้ที่ README.md")
        return
    
    # Show processing indicator
    with st.spinner(f"{UI_TEXT['processing']} using {model_name}"):
        try:
            # Create parser
            parser = FileParser(api_key, model_name)
            
            # Parse file
            data, error = parser.parse_file(file, file_type)
            
            if error:
                st.error(f"{UI_TEXT['error']}: {error}")
                return
            
            if not data:
                st.warning("⚠️ ไม่พบข้อมูล (No data found)")
                return
            
            # Save to session state
            st.session_state.parsed_data = data
            st.session_state.uploaded_file_name = file.name
            
            # Success - will be displayed in main area
            st.rerun()
            
        except Exception as e:
            st.error(f"{UI_TEXT['error']}: {str(e)}")


if __name__ == "__main__":
    main()
