"""PDF Generator using ReportLab"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Frame
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from datetime import datetime
from io import BytesIO
from uuid import UUID
from decimal import Decimal
import logging

def generate_goal_report_pdf(user_data: dict, goals: list, entries_stats: dict) -> bytes:
    """
    Generate a comprehensive PDF report with user data and all goals
    
    Args:
        user_data: User information
        goals: List of goal objects
        entries_stats: Time entry statistics
    
    Returns:
        PDF bytes
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Starting comprehensive goal report PDF generation - User: {user_data.get('google_email', 'N/A')}, Goals count: {len(goals)}, Stats: {entries_stats}")
    
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, topMargin=1.5*inch, bottomMargin=0.5*inch)
    
    elements = []
    styles = getSampleStyleSheet()
    
    total_money_earned = 0
    for goal in goals:
        hourly_rate = float(goal.get('hourly_rate', 0) or 0)
        goal_id = goal.get('goal_id')
        if goal_id and goal_id in entries_stats.get('goals_hours', {}):
            hours = entries_stats['goals_hours'][goal_id]
            total_money_earned += hourly_rate * hours
    
    def draw_header(canvas, doc):
        canvas.saveState()
        
        right_margin = doc.width + doc.leftMargin
        top = doc.height + doc.bottomMargin + 0.5*inch
        
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawRightString(right_margin, top, user_data.get('full_name') or 'N/A')
        
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(right_margin, top - 15, user_data.get('google_email') or 'N/A')
        canvas.drawRightString(right_margin, top - 30, user_data.get('country') or 'N/A')
        if user_data.get('phone'):
            canvas.drawRightString(right_margin, top - 45, user_data.get('phone') or 'N/A')
            canvas.drawRightString(right_margin, top - 60, f"Currency: {user_data.get('currency') or 'N/A'}")
            line_offset = 75
        else:
            canvas.drawRightString(right_margin, top - 45, f"Currency: {user_data.get('currency') or 'N/A'}")
            line_offset = 60
        
        canvas.setStrokeColor(colors.HexColor('#cccccc'))
        canvas.setLineWidth(0.5)
        canvas.line(right_margin - 150, top - line_offset, right_margin, top - line_offset)
        
        canvas.restoreState()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    elements.append(Paragraph("Trackify Goals Report", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    elements.append(Paragraph("Summary Statistics", styles['Heading2']))
    elements.append(Spacer(1, 0.1*inch))
    
    total_hours = entries_stats.get('total_hours', 0)
    total_entries = entries_stats.get('total_entries', 0)
    currency = user_data.get('currency') or 'USD'
    
    summary_data = [
        ['Metric', 'Value'],
        ['Total Goals', str(len(goals))],
        ['Total Hours Logged', f"{total_hours:.1f} hours"],
        ['Total Entries', str(total_entries)],
        ['Total Money Earned', f"{currency} {total_money_earned:,.2f}"],
        ['Report Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 4*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3*inch))
    
    elements.append(Paragraph("Goals Details", styles['Heading2']))
    elements.append(Spacer(1, 0.1*inch))
    
    if goals:
        for idx, goal in enumerate(goals, 1):
            goal_heading = f"Goal {idx}: {goal.get('title', 'Untitled')}"
            elements.append(Paragraph(goal_heading, styles['Heading3']))
            
            goal_details = [
                ['Attribute', 'Value'],
                ['Title', goal.get('title', 'N/A')],
                ['Target Hours', str(goal.get('target_hours', 'N/A'))],
                ['Hourly Rate', f"${goal.get('hourly_rate', 0)}" if goal.get('hourly_rate') else 'N/A'],
                ['Start Date', str(goal.get('start_date', 'N/A'))],
                ['End Date', str(goal.get('end_date', 'N/A'))],
                ['Description', goal.get('description', 'No description provided')[:100]],
            ]
            
            goal_table = Table(goal_details, colWidths=[2*inch, 4*inch])
            goal_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8b5cf6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),
            ]))
            elements.append(goal_table)
            elements.append(Spacer(1, 0.2*inch))
            
            if idx % 3 == 0 and idx < len(goals):
                elements.append(PageBreak())
    else:
        elements.append(Paragraph("No goals found.", styles['Normal']))
    
    try:
        logger.info("Building comprehensive goal report PDF document...")
        doc.build(elements, onFirstPage=draw_header, onLaterPages=draw_header)
        pdf_buffer.seek(0)
        result = pdf_buffer.getvalue()
        logger.info(f"Comprehensive goal report PDF generated successfully, size: {len(result)} bytes")
        return result
    except Exception as e:
        logger.error(f"Error building comprehensive goal report PDF document: {e}", exc_info=True)
        raise

def generate_goal_specific_pdf(goal_data: dict, user_data: dict, goal_hours: dict) -> bytes:
    """
    Generate a PDF for a specific goal with detailed information
    
    Args:
        goal_data: Goal information
        user_data: User information
        goal_hours: Time tracking data for the goal
    
    Returns:
        PDF bytes
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Starting PDF generation with goal_data type: {type(goal_data)}, user_data type: {type(user_data)}, goal_hours type: {type(goal_hours)}")
        
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, topMargin=1.5*inch, bottomMargin=0.5*inch)
        
        elements = []
        styles = getSampleStyleSheet()
        
        total_hours = goal_hours.get('total_hours', 0)
        hourly_rate = float(goal_data.get('hourly_rate', 0) or 0)
        money_earned = total_hours * hourly_rate
        currency = user_data.get('currency') or 'USD'
    except Exception as e:
        logger.error(f"Error in PDF generation initialization: {e}", exc_info=True)
        raise
    
    def draw_header(canvas, doc):
        canvas.saveState()
        
        right_margin = doc.width + doc.leftMargin
        top = doc.height + doc.bottomMargin + 0.5*inch
        
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawRightString(right_margin, top, user_data.get('full_name') or 'N/A')
        
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(right_margin, top - 15, user_data.get('google_email') or 'N/A')
        canvas.drawRightString(right_margin, top - 30, user_data.get('country') or 'N/A')
        if user_data.get('phone'):
            canvas.drawRightString(right_margin, top - 45, user_data.get('phone') or 'N/A')
            canvas.drawRightString(right_margin, top - 60, f"Currency: {user_data.get('currency') or 'N/A'}")
            line_offset = 75
        else:
            canvas.drawRightString(right_margin, top - 45, f"Currency: {user_data.get('currency') or 'N/A'}")
            line_offset = 60
        
        canvas.setStrokeColor(colors.HexColor('#cccccc'))
        canvas.setLineWidth(0.5)
        canvas.line(right_margin - 150, top - line_offset, right_margin, top - line_offset)
        
        canvas.restoreState()
    
    goal_title = goal_data.get('title') or 'Goal Report'
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=20,
        alignment=TA_LEFT
    )
    elements.append(Paragraph(f"Goal: {goal_title}", title_style))
    elements.append(Spacer(1, 0.1*inch))
    
    target_hours = goal_data.get('target_hours', 0)
    progress = (float(total_hours) / float(target_hours) * 100) if target_hours else 0
    
    description = goal_data.get('description') or 'N/A'
    if description != 'N/A':
        description = description[:80]
    
    goal_details = [
        ['Field', 'Value'],
        ['Title', goal_data.get('title', 'N/A')],
        ['Description', description],
        ['Target Hours', str(target_hours)],
        ['Hours Completed', f"{total_hours:.1f}"],
        ['Progress', f"{progress:.1f}%"],
        ['Hourly Rate', f"{currency} {hourly_rate:.2f}"],
        ['Money Earned', f"{currency} {money_earned:,.2f}"],
        ['Start Date', str(goal_data.get('start_date', 'N/A'))],
        ['End Date', str(goal_data.get('end_date', 'N/A'))],
    ]
    
    goal_table = Table(goal_details, colWidths=[2*inch, 4*inch])
    goal_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),
    ]))
    elements.append(goal_table)
    elements.append(Spacer(1, 0.3*inch))
    
    footer_text = f"Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}"
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph(footer_text, styles['Normal']))
    
    try:
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Building PDF document for specific goal...")
        doc.build(elements, onFirstPage=draw_header, onLaterPages=draw_header)
        pdf_buffer.seek(0)
        result = pdf_buffer.getvalue()
        logger.info(f"PDF generated successfully, size: {len(result)} bytes")
        return result
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error building PDF document: {e}", exc_info=True)
        raise