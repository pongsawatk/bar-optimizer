"""
PDF Generator Module - Report Generation
โมดูลสำหรับสร้างรายงานแผนการตัดเป็นไฟล์ PDF
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


def register_thai_font():
    """Register Thai font for PDF generation"""
    # Try to use system fonts or fallback to default
    try:
        # Common Thai font locations on Windows
        font_paths = [
            r"C:\Windows\Fonts\THSarabunNew.ttf",
            r"C:\Windows\Fonts\tahoma.ttf",
            r"C:\Windows\Fonts\angsana.ttc"
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('THFont', font_path))
                return 'THFont'
    except:
        pass
    
    # Fallback to Helvetica (built-in, no Thai support)
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
    page_text = f"{page_num}"
    canvas.setFont(font_name, 8)
    canvas.drawCentredString(page_width / 2, 15*mm, page_text)
    
    # Branding text
    branding = "Powered by Contech BU (Builk One Group) | Constructed for Free Use by Contractors & Engineers"
    canvas.setFont(font_name, 7)
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
    
    Args:
        procurement_summary: List of procurement summary dicts
        cutting_plan: List of StockBar objects
        total_waste: Total waste in meters
        stock_length: Stock length used
        cutting_tolerance: Cutting tolerance in mm
        project_name: Project name for report header
        
    Returns:
        BytesIO buffer containing PDF
    """
    from io import BytesIO
    buffer = BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=25*mm  # Increased for footer
    )
    
    # Register Thai font
    font_name = register_thai_font()
    
    # Create styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=18,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=12
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=14,
        textColor=colors.HexColor('#2196F3'),
        spaceAfter=10,
        spaceBefore=10
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10
    )
    
    # Helper to create table cell with style
    def table_cell(text, style=normal_style):
        return Paragraph(str(text), style)
    
    # Helper for centered table cell
    center_style = ParagraphStyle(
        'Center',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=9,
        alignment=1, # Center
        textColor=colors.black
    )
    
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=9,
        alignment=1, # Center
        textColor=colors.whitesmoke
    )
    
    def cell_center(text):
        return Paragraph(str(text), center_style)
    
    def cell_header(text):
        return Paragraph(str(text), header_style)
    
    # Build document content
    story = []
    
    # Title
    story.append(Paragraph(f"<b>Bar Cutting Optimization Report</b><br/>แผนการตัดเหล็กเส้น", title_style))
    story.append(Spacer(1, 10*mm))
    
    # Project info
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    info_data = [
        ["Project / โครงการ:", project_name],
        ["Date / วันที่:", current_date],
        ["Stock Length / ความยาวท่อน:", f"{stock_length} m"],
        ["Cutting Tolerance / ค่าเผื่อใบตัด:", f"{cutting_tolerance} mm"],
        ["Splicing / การต่อเหล็ก:", f"เปิดใช้งาน (Lap: {lap_factor}d)" if splicing_enabled else "ปิดใช้งาน"]
    ]
    
    info_table = Table(info_data, colWidths=[60*mm, 100*mm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#555555')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 10*mm))
    
    # Procurement Summary
    story.append(Paragraph("<b>Procurement Summary / สรุปการเบิกเหล็ก</b>", heading_style))
    
    summary_data = [[
        cell_header("Diameter (mm)<br/>ขนาด"), 
        cell_header("Quantity (bars)<br/>จำนวนเส้น"), 
        cell_header("Total Length (m)<br/>ความยาวรวม"), 
        cell_header("Waste (m)<br/>เศษเหลือ"), 
        cell_header("Waste %<br/>% เศษ"), 
        cell_header("Weight (kg)<br/>น้ำหนัก")
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
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2196F3')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E3F2FD')),
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
        
        # Diameter header
        story.append(Paragraph(f"<b>Diameter DB{diameter} mm</b>", normal_style))
        story.append(Spacer(1, 3*mm))
        
        plan_data = [[
            cell_header("Stock #<br/>เส้นที่"), 
            cell_header("Bar Mark<br/>รหัสเหล็ก"), 
            cell_header("Length (m)<br/>ความยาว"), 
            cell_header("Position<br/>ตำแหน่ง"), 
            cell_header("Waste (m)<br/>เศษเหลือ"), 
            cell_header("Utilization<br/>% ใช้งาน")
        ]]
        
        for stock in stocks:
            # First cut row
            first_cut = stock.cuts[0]
            plan_data.append([
                cell_center(str(stock.stock_id)),
                cell_center(first_cut['bar_mark']),
                cell_center(f"{first_cut['length']:.2f}"),
                cell_center(f"{first_cut['start']:.2f} - {first_cut['end']:.2f}"),
                cell_center(f"{stock.remaining:.2f}"),
                cell_center(f"{stock.utilization:.1f}%")
            ])
            
            # Additional cuts
            for cut in stock.cuts[1:]:
                plan_data.append([
                    "",  # Same stock
                    cell_center(cut['bar_mark']),
                    cell_center(f"{cut['length']:.2f}"),
                    cell_center(f"{cut['start']:.2f} - {cut['end']:.2f}"),
                    "",
                    ""
                ])
        
        plan_table = Table(plan_data, colWidths=[18*mm, 30*mm, 25*mm, 35*mm, 25*mm, 27*mm], repeatRows=1)
        plan_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')])
        ]))
        story.append(plan_table)
        story.append(Spacer(1, 5*mm))
    
    # Remnant Summary
    story.append(Paragraph("<b>Remnant Summary / สรุปเศษเหล็กที่เหลือ</b>", heading_style))
    
    # Reusable remnants
    story.append(Paragraph("<b>Reusable Remnants (≥ 1.0m) / เศษใช้งานต่อได้</b>", normal_style))
    story.append(Spacer(1, 2*mm))
    
    if remnant_summary['reusable']:
        reusable_data = [[
            cell_header("Stock #"), 
            cell_header("Diameter"), 
            cell_header("Length (m)"), 
            cell_header("Weight (kg)")
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
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(reusable_table)
        
        total_reusable_length = sum(rem['length'] for rem in remnant_summary['reusable'])
        total_reusable_weight = sum(rem['weight'] for rem in remnant_summary['reusable'])
        story.append(Spacer(1, 2*mm))
        story.append(Paragraph(f"Total: {len(remnant_summary['reusable'])} pieces | {total_reusable_length:.2f} m | {total_reusable_weight:.2f} kg", normal_style))
    else:
        story.append(Paragraph("No reusable remnants / ไม่มีเศษที่สามารถใช้ได้", normal_style))
    
    story.append(Spacer(1, 5*mm))
    
    # Scrap remnants
    story.append(Paragraph("<b>Scrap Remnants (< 1.0m) / เศษทิ้ง</b>", normal_style))
    story.append(Spacer(1, 2*mm))
    
    if remnant_summary['scrap']:
        scrap_data = [[
            cell_header("Stock #"), 
            cell_header("Diameter"), 
            cell_header("Length (m)"), 
            cell_header("Weight (kg)")
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
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF9800')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(scrap_table)
        
        total_scrap_length = sum(rem['length'] for rem in remnant_summary['scrap'])
        total_scrap_weight = sum(rem['weight'] for rem in remnant_summary['scrap'])
        story.append(Spacer(1, 2*mm))
        story.append(Paragraph(f"Total: {len(remnant_summary['scrap'])} pieces | {total_scrap_length:.2f} m | {total_scrap_weight:.2f} kg", normal_style))
    else:
        story.append(Paragraph("No scrap remnants / ไม่มีเศษทิ้ง", normal_style))
    
    story.append(Spacer(1, 10*mm))
    
    # Build PDF with footer
    doc.build(story, onFirstPage=lambda c, d: add_page_footer(c, d, font_name), 
              onLaterPages=lambda c, d: add_page_footer(c, d, font_name))
    buffer.seek(0)
    return buffer
