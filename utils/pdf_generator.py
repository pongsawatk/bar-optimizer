"""
PDF Generator Module - Report Generation
โมดูลสำหรับสร้างรายงานแผนการตัดเป็นไฟล์ PDF (Cloud Compatible Version)
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os
from io import BytesIO

def register_thai_font():
    """
    Register Thai font for PDF generation (Cross-platform support)
    ค้นหาฟอนต์ THSarabunNew.ttf ในโปรเจกต์ เพื่อให้ทำงานได้ทั้งบน Windows และ Cloud
    """
    try:
        # หาตำแหน่งไฟล์ปัจจุบัน (utils/pdf_generator.py)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # ลองหาฟอนต์ที่ Root Directory (ขึ้นไป 1 ชั้นจาก utils)
        font_path_root = os.path.join(current_dir, '..', 'THSarabunNew.ttf')
        
        # ลองหาฟอนต์ในโฟลเดอร์ utils (เผื่อคนวางไว้ที่นี่)
        font_path_local = os.path.join(current_dir, 'THSarabunNew.ttf')
        
        if os.path.exists(font_path_root):
            pdfmetrics.registerFont(TTFont('THSarabunNew', font_path_root))
            return 'THSarabunNew'
        elif os.path.exists(font_path_local):
            pdfmetrics.registerFont(TTFont('THSarabunNew', font_path_local))
            return 'THSarabunNew'
            
    except Exception as e:
        print(f"Font registration warning: {e}")
    
    # ถ้าหาไม่เจอจริงๆ ให้ใช้ Helvetica (แต่อ่านไทยไม่ออก)
    return 'Helvetica'


def add_page_footer(canvas, doc, font_name='Helvetica'):
    """
    Add footer to each page with page numbers and branding
    """
    canvas.saveState()
    
    # Get page dimensions
    page_width, page_height = A4
    
    # Page number
    page_num = canvas.getPageNumber()
    page_text = f"Page {page_num}"
    canvas.setFont(font_name, 9)
    canvas.drawCentredString(page_width / 2, 15*mm, page_text)
    
    # Branding text
    branding = "Powered by Contech BU (Builk One Group) | Constructed for Free Use by Contractors & Engineers"
    canvas.setFont(font_name, 8)
    canvas.drawCentredString(page_width / 2, 10*mm, branding)
    
    canvas.restoreState()


def generate_cutting_report(
    procurement_summary,
    cutting_plan,
    total_waste,
    stock_length,
    cutting_tolerance,
    remnant_summary,
    total_weight,
    project_name="Bar Cutting Project",
    splicing_enabled=False,
    lap_factor=40
):
    """
    Generate PDF cutting report
    """
    buffer = BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=25*mm
    )
    
    # Register Thai font
    font_name = register_thai_font()
    
    # Create styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=20,
        textColor=colors.HexColor('#0072CE'), # Contech Blue
        spaceAfter=12,
        alignment=0
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=16,
        textColor=colors.HexColor('#0072CE'),
        spaceAfter=10,
        spaceBefore=10
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=12,
        leading=14
    )
    
    center_style = ParagraphStyle(
        'Center',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=11,
        alignment=1, # Center
        textColor=colors.black
    )
    
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=11,
        alignment=1, # Center
        textColor=colors.whitesmoke
    )
    
    # Helper functions
    def cell_center(text): return Paragraph(str(text), center_style)
    def cell_header(text): return Paragraph(str(text), header_style)
    
    # Build document content
    story = []
    
    # Title
    story.append(Paragraph(f"<b>Bar Cutting Optimization Report</b>", title_style))
    story.append(Paragraph(f"แผนการตัดเหล็กเส้น", normal_style))
    story.append(Spacer(1, 5*mm))
    
    # Project info
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    splicing_text = f"เปิดใช้งาน (Lap: {lap_factor}d)" if splicing_enabled else "ปิดใช้งาน (Disabled)"
    
    info_data = [
        ["Project / โครงการ:", Paragraph(str(project_name), normal_style)],
        ["Date / วันที่:", current_date],
        ["Stock Length / ความยาวท่อน:", f"{stock_length} m"],
        ["Cutting Tolerance / ค่าเผื่อใบตัด:", f"{cutting_tolerance} mm"],
        ["Splicing / การต่อเหล็ก:", splicing_text]
    ]
    
    info_table = Table(info_data, colWidths=[60*mm, 100*mm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#555555')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 10*mm))
    
    # Procurement Summary
    story.append(Paragraph("<b>Procurement Summary / สรุปการเบิกเหล็ก</b>", heading_style))
    
    summary_data = [[
        cell_header("Diameter<br/>(mm)"), 
        cell_header("Qty<br/>(bars)"), 
        cell_header("Total Len<br/>(m)"), 
        cell_header("Waste<br/>(m)"), 
        cell_header("Waste<br/>%"), 
        cell_header("Weight<br/>(kg)")
    ]]
    
    for item in procurement_summary:
        summary_data.append([
            cell_center(f"DB{item['diameter']}"),
            cell_center(str(item['quantity'])),
            cell_center(f"{item['total_length']:.2f}"),
            cell_center(f"{item['waste']:.2f}"),
            cell_center(f"{item['waste_percentage']:.1f}%"),
            cell_center(f"{item['total_weight']:.2f}")
        ])
    
    # Add total row
    total_bars = sum(item['quantity'] for item in procurement_summary)
    total_length = sum(item['total_length'] for item in procurement_summary)
    
    summary_data.append([
        cell_center("<b>Total / รวม</b>"),
        cell_center(f"<b>{total_bars}</b>"),
        cell_center(f"<b>{total_length:.2f}</b>"),
        cell_center(f"<b>{total_waste:.2f}</b>"),
        "",
        cell_center(f"<b>{total_weight:.2f}</b>")
    ])
    
    summary_table = Table(summary_data, colWidths=[25*mm, 30*mm, 30*mm, 25*mm, 25*mm, 25*mm], repeatRows=1)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0072CE')), # Blue Header
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E3F2FD')), # Light Blue Footer
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 10*mm))
    
    # Detailed Cutting Plan
    story.append(Paragraph("<b>Detailed Cutting Plan / แผนการตัดรายเส้น</b>", heading_style))
    
    # Group by diameter
    plan_by_diameter = {}
    for stock in cutting_plan:
        if stock.diameter not in plan_by_diameter:
            plan_by_diameter[stock.diameter] = []
        plan_by_diameter[stock.diameter].append(stock)
    
    for diameter in sorted(plan_by_diameter.keys()):
        stocks = plan_by_diameter[diameter]
        
        story.append(Paragraph(f"<b>Diameter DB{diameter} mm</b>", normal_style))
        story.append(Spacer(1, 2*mm))
        
        plan_data = [[
            cell_header("Stock #"), 
            cell_header("Bar Mark"), 
            cell_header("Length (m)"), 
            cell_header("Position"), 
            cell_header("Waste (m)"), 
            cell_header("Util %")
        ]]
        
        for stock in stocks:
            first_cut = True
            for cut in stock.cuts:
                if first_cut:
                    plan_data.append([
                        cell_center(str(stock.stock_id)),
                        cell_center(cut['bar_mark']),
                        cell_center(f"{cut['length']:.2f}"),
                        cell_center(f"{cut['start']:.2f} - {cut['end']:.2f}"),
                        cell_center(f"{stock.remaining:.2f}"),
                        cell_center(f"{stock.utilization:.1f}%")
                    ])
                    first_cut = False
                else:
                    plan_data.append([
                        "", # Same stock
                        cell_center(cut['bar_mark']),
                        cell_center(f"{cut['length']:.2f}"),
                        cell_center(f"{cut['start']:.2f} - {cut['end']:.2f}"),
                        "", ""
                    ])
        
        plan_table = Table(plan_data, colWidths=[18*mm, 35*mm, 25*mm, 40*mm, 25*mm, 25*mm], repeatRows=1)
        plan_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')), # Dark Header
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')])
        ]))
        story.append(plan_table)
        story.append(Spacer(1, 5*mm))
    
    # Remnant Summary (Using your Color Logic)
    story.append(Paragraph("<b>Remnant Summary / สรุปเศษเหล็กที่เหลือ</b>", heading_style))
    
    # Reusable remnants (Green)
    story.append(Paragraph("<b>Reusable Remnants (≥ 1.0m) / เศษใช้งานต่อได้</b>", normal_style))
    story.append(Spacer(1, 2*mm))
    
    if remnant_summary['reusable']:
        reusable_data = [[
            cell_header("Stock #"), cell_header("Diameter"), cell_header("Length (m)"), cell_header("Weight (kg)")
        ]]
        for rem in remnant_summary['reusable']:
            reusable_data.append([
                cell_center(str(rem['stock_id'])),
                cell_center(f"DB{rem['diameter']}"),
                cell_center(f"{rem['length']:.2f}"),
                cell_center(f"{rem['weight']:.2f}")
            ])
        
        reusable_table = Table(reusable_data, colWidths=[30*mm, 30*mm, 40*mm, 40*mm])
        reusable_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')), # Green
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(reusable_table)
        
        total_len = sum(rem['length'] for rem in remnant_summary['reusable'])
        total_w = sum(rem['weight'] for rem in remnant_summary['reusable'])
        story.append(Spacer(1, 2*mm))
        story.append(Paragraph(f"Total: {len(remnant_summary['reusable'])} pieces | {total_len:.2f} m | {total_w:.2f} kg", normal_style))
    else:
        story.append(Paragraph("No reusable remnants / ไม่มีเศษที่สามารถใช้ได้", normal_style))
    
    story.append(Spacer(1, 5*mm))
    
    # Scrap remnants (Orange)
    story.append(Paragraph("<b>Scrap Remnants (< 1.0m) / เศษทิ้ง</b>", normal_style))
    story.append(Spacer(1, 2*mm))
    
    if remnant_summary['scrap']:
        scrap_data = [[
            cell_header("Stock #"), cell_header("Diameter"), cell_header("Length (m)"), cell_header("Weight (kg)")
        ]]
        for rem in remnant_summary['scrap']:
            scrap_data.append([
                cell_center(str(rem['stock_id'])),
                cell_center(f"DB{rem['diameter']}"),
                cell_center(f"{rem['length']:.2f}"),
                cell_center(f"{rem['weight']:.2f}")
            ])
        
        scrap_table = Table(scrap_data, colWidths=[30*mm, 30*mm, 40*mm, 40*mm])
        scrap_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF9800')), # Orange
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(scrap_table)
        
        total_len = sum(rem['length'] for rem in remnant_summary['scrap'])
        total_w = sum(rem['weight'] for rem in remnant_summary['scrap'])
        story.append(Spacer(1, 2*mm))
        story.append(Paragraph(f"Total: {len(remnant_summary['scrap'])} pieces | {total_len:.2f} m | {total_w:.2f} kg", normal_style))
    else:
        story.append(Paragraph("No scrap remnants / ไม่มีเศษทิ้ง", normal_style))
    
    # Build PDF
    doc.build(story, 
              onFirstPage=lambda c, d: add_page_footer(c, d, font_name), 
              onLaterPages=lambda c, d: add_page_footer(c, d, font_name))
    
    buffer.seek(0)
    return buffer