from __future__ import annotations
import csv
import html
import re
import statistics
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'results'
REPORT = ROOT / 'report'
SOURCE = REPORT / 'Report.md'
PDF_OUT = REPORT / 'CCP_NIS_Fall_2026_Report.pdf'
DOCX_OUT = REPORT / 'CCP_NIS_Fall_2026_Report.docx'
AUTHOR = 'Muhammad Imaad Tahir'
REGISTRATION = 'CR-23014'

def read_csv(name: str) -> list[dict[str, str]]:
    with (RESULTS / name).open(encoding='utf-8') as handle:
        return list(csv.DictReader(handle))

def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ['| ' + ' | '.join(headers) + ' |', '|' + '|'.join(('---' for _ in headers)) + '|']
    lines.extend(('| ' + ' | '.join(row) + ' |' for row in rows))
    return '\n'.join(lines)

def replacements() -> dict[str, str]:
    summary = read_csv('attack_summary.csv')
    frequency = [r for r in summary if r['attack'] == 'frequency']
    known = [r for r in summary if r['attack'] == 'known-prefix-24']
    freq_table = markdown_table(['Length', 'Exact recovery', '95% Wilson interval', 'Mean letter accuracy', 'Median time'], [[r['ciphertext_length'], f'{r['exact_successes']}/{r['trials']} ({float(r['exact_success_pct']):g}%)', f'{float(r['wilson_95_low_pct']):g}%–{float(r['wilson_95_high_pct']):g}%', f'{float(r['mean_letter_accuracy_pct']):g}%', f'{float(r['median_elapsed_ms']):g} ms'] for r in frequency])
    known_table = markdown_table(['Ciphertext length', 'Known prefix', 'Exact recovery', 'Mean candidates', 'Median time'], [[r['ciphertext_length'], '24', f'{r['exact_successes']}/{r['trials']} ({float(r['exact_success_pct']):g}%)', f'{float(r['mean_candidates']):g}', f'{float(r['median_elapsed_ms']):g} ms'] for r in known])
    prefix_rows = read_csv('known_prefix_lengths.csv')
    prefix_table_rows = []
    for length in (12, 24, 48, 96):
        group = [r for r in prefix_rows if int(r['known_prefix_length']) == length]
        successes = sum((int(r['exact_recovery']) for r in group))
        prefix_table_rows.append([str(length), str(len(group)), f'{successes}/{len(group)} ({100 * successes / len(group):g}%)', f'{statistics.mean((int(r['evaluated_candidates']) for r in group)):g}', f'{statistics.median((float(r['elapsed_ms']) for r in group)):g} ms'])
    prefix_table = markdown_table(['Known prefix m', 'Trials', 'Exact recovery', 'Mean candidates', 'Median time'], prefix_table_rows)
    performance = read_csv('performance.csv')
    operations = ('shift_encrypt', 'vigenere_encrypt', 'vrf_encrypt', 'vrf_decrypt')
    perf_rows = []
    for length in (1000, 10000, 100000, 1000000):
        row = [f'{length:,}']
        for operation in operations:
            match = next((r for r in performance if r['operation'] == operation and int(r['input_length']) == length))
            row.append(f'{float(match['median_ms']):g}')
        perf_rows.append(row)
    perf_table = markdown_table(['Characters', 'Shift enc. (ms)', 'Vigenère enc. (ms)', 'VRFC enc. (ms)', 'VRFC dec. (ms)'], perf_rows)
    metrics = {r['operation']: float(r['median_ms']) for r in performance if int(r['input_length']) == 1000000}
    performance_analysis = f'At one million characters, VRFC encryption took {metrics['vrf_encrypt']:.2f} ms versus {metrics['shift_encrypt']:.2f} ms for Shift encryption (approximately {metrics['vrf_encrypt'] / metrics['shift_encrypt']:.2f}×), while VRFC decryption took {metrics['vrf_decrypt']:.2f} ms versus {metrics['shift_decrypt']:.2f} ms for Shift decryption (approximately {metrics['vrf_decrypt'] / metrics['shift_decrypt']:.2f}×).'
    return {'FREQUENCY_TABLE': freq_table, 'KNOWN_TABLE': known_table, 'PREFIX_TABLE': prefix_table, 'PERFORMANCE_TABLE': perf_table, 'PERFORMANCE_ANALYSIS': performance_analysis}

def expanded_markdown() -> str:
    text = SOURCE.read_text(encoding='utf-8')
    for key, value in replacements().items():
        text = text.replace('{{' + key + '}}', value)
    unresolved = re.findall('\\{\\{[A-Z_]+\\}\\}', text)
    if unresolved:
        raise ValueError(f'Unresolved report placeholders: {unresolved}')
    (REPORT / 'Report_Expanded.md').write_text(text, encoding='utf-8')
    return text

def inline_pdf(text: str) -> str:
    value = html.escape(text, quote=False)
    value = re.sub('\\[([^\\]]+)\\]\\((https?://[^)]+)\\)', '<link href="\\2" color="#155e75"><u>\\1</u></link>', value)
    value = re.sub('\\*\\*([^*]+)\\*\\*', '<b>\\1</b>', value)
    value = re.sub('`([^`]+)`', '<font name="DejaVuMono" size="7.5" color="#6d28d9">\\1</font>', value)
    value = re.sub('(?<!\\w)\\*([^*]+)\\*(?!\\w)', '<i>\\1</i>', value)
    return value

def inline_plain(text: str) -> str:
    text = re.sub('\\[([^\\]]+)\\]\\((https?://[^)]+)\\)', '\\1 (\\2)', text)
    return text.replace('**', '').replace('`', '').replace('*', '')

def markdown_blocks(text: str):
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith('```'):
            i += 1
            code = []
            while i < len(lines) and (not lines[i].strip().startswith('```')):
                code.append(lines[i])
                i += 1
            i += 1
            yield ('code', '\n'.join(code))
            continue
        if line.startswith('|'):
            table = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table.append(lines[i].strip())
                i += 1
            yield ('table', table)
            continue
        match = re.match('^!\\[([^]]*)\\]\\(([^)]+)\\)$', line)
        if match:
            yield ('image', (match.group(1), match.group(2)))
            i += 1
            continue
        match = re.match('^(#{1,3})\\s+(.+)$', line)
        if match:
            yield ('heading', (len(match.group(1)), match.group(2)))
            i += 1
            continue
        if line.startswith('> '):
            yield ('quote', line[2:])
            i += 1
            continue
        if re.match('^[-*]\\s+', line):
            yield ('bullet', re.sub('^[-*]\\s+', '', line))
            i += 1
            continue
        if re.match('^\\d+\\.\\s+', line):
            yield ('number', line)
            i += 1
            continue
        paragraph = [line]
        i += 1
        while i < len(lines):
            candidate = lines[i].strip()
            if not candidate or candidate.startswith(('#', '|', '```', '> ', '![')) or re.match('^[-*]\\s+', candidate) or re.match('^\\d+\\.\\s+', candidate):
                break
            paragraph.append(candidate)
            i += 1
        yield ('paragraph', ' '.join(paragraph))

def build_pdf(text: str) -> None:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, XPreformatted
    from reportlab.platypus.tableofcontents import TableOfContents
    font_dir = Path('/usr/share/fonts/truetype/dejavu')
    pdfmetrics.registerFont(TTFont('DejaVu', str(font_dir / 'DejaVuSans.ttf')))
    pdfmetrics.registerFont(TTFont('DejaVuBold', str(font_dir / 'DejaVuSans-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('DejaVuItalic', '/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuMono', str(font_dir / 'DejaVuSansMono.ttf')))
    pdfmetrics.registerFontFamily('DejaVu', normal='DejaVu', bold='DejaVuBold', italic='DejaVuItalic')
    navy = colors.HexColor('#172554')
    purple = colors.HexColor('#6d28d9')
    cyan = colors.HexColor('#0e7490')
    slate = colors.HexColor('#475569')
    light = colors.HexColor('#f1f5f9')
    styles = getSampleStyleSheet()
    body = ParagraphStyle('BodyCustom', parent=styles['BodyText'], fontName='DejaVu', fontSize=8.8, leading=12.8, textColor=colors.HexColor('#1e293b'), spaceAfter=6, alignment=TA_LEFT, splitLongWords=True)
    h1 = ParagraphStyle('Heading1', parent=styles['Heading1'], fontName='DejaVuBold', fontSize=16, leading=20, textColor=navy, spaceBefore=15, spaceAfter=8, keepWithNext=True)
    h2 = ParagraphStyle('Heading2', parent=styles['Heading2'], fontName='DejaVuBold', fontSize=11.5, leading=15, textColor=purple, spaceBefore=10, spaceAfter=5, keepWithNext=True)
    h3 = ParagraphStyle('Heading3', parent=styles['Heading3'], fontName='DejaVuBold', fontSize=9.6, leading=13, textColor=cyan, spaceBefore=8, spaceAfter=4, keepWithNext=True)
    caption = ParagraphStyle('Caption', parent=body, fontSize=7.6, leading=10, textColor=slate, alignment=TA_CENTER, spaceBefore=3, spaceAfter=8)
    bullet = ParagraphStyle('Bullet', parent=body, leftIndent=14, firstLineIndent=-8, bulletIndent=3, spaceAfter=3)
    code_style = ParagraphStyle('Code', parent=body, fontName='DejaVuMono', fontSize=6.8, leading=9.3, textColor=colors.HexColor('#e2e8f0'), leftIndent=0, spaceAfter=0)
    table_body = ParagraphStyle('TableBody', parent=body, fontSize=7.0, leading=9.3, spaceAfter=0)
    table_head = ParagraphStyle('TableHead', parent=table_body, fontName='DejaVuBold', textColor=colors.white)
    quote_style = ParagraphStyle('Quote', parent=body, fontName='DejaVuItalic', textColor=colors.HexColor('#155e75'), spaceAfter=0)

    class ReportDoc(SimpleDocTemplate):

        def afterFlowable(self, flowable):
            if not isinstance(flowable, Paragraph):
                return
            name = flowable.style.name
            if name not in ('Heading1', 'Heading2', 'Heading3'):
                return
            level = int(name[-1]) - 1
            title = flowable.getPlainText()
            key = f'heading-{self.seq.nextf('heading')}'
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(title, key, level=level, closed=False)
            self.notify('TOCEntry', (level, title, self.page, key))

    def on_page(canvas, doc):
        if doc.page == 1:
            return
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor('#cbd5e1'))
        canvas.setLineWidth(0.5)
        canvas.line(doc.leftMargin, A4[1] - 15 * mm, A4[0] - doc.rightMargin, A4[1] - 15 * mm)
        canvas.setFont('DejaVu', 7.2)
        canvas.setFillColor(slate)
        canvas.drawString(doc.leftMargin, A4[1] - 12.5 * mm, 'CT-486 · Complex Computing Problem')
        canvas.drawRightString(A4[0] - doc.rightMargin, A4[1] - 12.5 * mm, 'VRFC · Fall 2026')
        canvas.line(doc.leftMargin, 13 * mm, A4[0] - doc.rightMargin, 13 * mm)
        canvas.drawString(doc.leftMargin, 9.5 * mm, f'{AUTHOR} · {REGISTRATION}')
        canvas.drawRightString(A4[0] - doc.rightMargin, 9.5 * mm, f'Page {doc.page}')
        canvas.restoreState()
    doc = ReportDoc(str(PDF_OUT), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=21 * mm, bottomMargin=18 * mm, title='Design and Break a Custom Cipher — VRFC', author=AUTHOR, subject='Network and Information Security (CT-486), CCP Fall 2026')
    story = []
    story.append(Spacer(1, 24 * mm))
    story.append(Paragraph('NETWORK AND INFORMATION SECURITY · CT-486', ParagraphStyle('CoverCourse', parent=body, fontName='DejaVuBold', fontSize=10, textColor=cyan, alignment=TA_CENTER, spaceAfter=12)))
    story.append(Paragraph('Design and Break<br/>a Custom Cipher', ParagraphStyle('CoverTitle', parent=body, fontName='DejaVuBold', fontSize=28, leading=35, textColor=navy, alignment=TA_CENTER, spaceAfter=12)))
    story.append(Paragraph('Vigenère–Rail-Fence Cascade (VRFC)', ParagraphStyle('CoverSubtitle', parent=body, fontName='DejaVu', fontSize=14, leading=19, textColor=purple, alignment=TA_CENTER, spaceAfter=18)))
    badge = Table([[Paragraph('TWO CLASSICAL STAGES', table_head), Paragraph('DUAL ATTACK SIMULATION', table_head), Paragraph('MEASURED RESULTS', table_head)]], colWidths=[doc.width / 3] * 3)
    badge.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, 0), purple), ('BACKGROUND', (1, 0), (1, 0), cyan), ('BACKGROUND', (2, 0), (2, 0), navy), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 9), ('BOTTOMPADDING', (0, 0), (-1, -1), 9)]))
    story.append(badge)
    story.append(Spacer(1, 24 * mm))
    info = [['Submitted by', AUTHOR], ['Registration no.', REGISTRATION], ['Assessment', 'Complex Computing Problem · CLO3'], ['Term', 'Fall 2026'], ['Submission deadline', '8 November 2026'], ['Maximum marks', '10']]
    info_table = Table([[Paragraph(inline_pdf(a), table_body), Paragraph(inline_pdf(b), table_body)] for a, b in info], colWidths=[doc.width * 0.34, doc.width * 0.56], hAlign='CENTER')
    info_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, -1), light), ('TEXTCOLOR', (0, 0), (0, -1), navy), ('FONTNAME', (0, 0), (0, -1), 'DejaVuBold'), ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cbd5e1')), ('LEFTPADDING', (0, 0), (-1, -1), 8), ('RIGHTPADDING', (0, 0), (-1, -1), 8), ('TOPPADDING', (0, 0), (-1, -1), 7), ('BOTTOMPADDING', (0, 0), (-1, -1), 7)]))
    story.append(info_table)
    story.append(Spacer(1, 15 * mm))
    story.append(Paragraph('Advanced technical report · implementation · cryptanalysis · reproducible benchmarks', ParagraphStyle('CoverFooter', parent=caption, textColor=slate)))
    story.append(PageBreak())
    story.append(Paragraph('Contents', ParagraphStyle('ContentsTitle', parent=h1, fontSize=21, alignment=TA_CENTER, spaceAfter=15)))
    toc = TableOfContents()
    toc.levelStyles = [ParagraphStyle('TOC1', parent=body, fontName='DejaVuBold', fontSize=9, leading=15, leftIndent=0, firstLineIndent=0, textColor=navy), ParagraphStyle('TOC2', parent=body, fontSize=8, leading=12, leftIndent=14, firstLineIndent=0, textColor=slate), ParagraphStyle('TOC3', parent=body, fontSize=7.5, leading=11, leftIndent=28, firstLineIndent=0, textColor=slate)]
    story.append(toc)
    story.append(PageBreak())
    for kind, payload in markdown_blocks(text):
        if kind == 'heading':
            level, title = payload
            story.append(Paragraph(inline_pdf(title), (h1, h2, h3)[level - 1]))
        elif kind == 'paragraph':
            story.append(Paragraph(inline_pdf(payload), body))
        elif kind in ('bullet', 'number'):
            marker = '•' if kind == 'bullet' else payload.split('.', 1)[0] + '.'
            content = payload if kind == 'bullet' else payload.split('.', 1)[1].strip()
            story.append(Paragraph(inline_pdf(content), bullet, bulletText=marker))
        elif kind == 'quote':
            quote = Table([[Paragraph(inline_pdf(payload), quote_style)]], colWidths=[doc.width])
            quote.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ecfeff')), ('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor('#67e8f9')), ('LEFTPADDING', (0, 0), (-1, -1), 10), ('RIGHTPADDING', (0, 0), (-1, -1), 10), ('TOPPADDING', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, -1), 8)]))
            story.extend([quote, Spacer(1, 7)])
        elif kind == 'code':
            block = Table([[XPreformatted(html.escape(payload), code_style)]], colWidths=[doc.width])
            block.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0f172a')), ('LEFTPADDING', (0, 0), (-1, -1), 9), ('RIGHTPADDING', (0, 0), (-1, -1), 9), ('TOPPADDING', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, -1), 8)]))
            story.extend([block, Spacer(1, 7)])
        elif kind == 'table':
            raw = [[cell.strip() for cell in row.strip('|').split('|')] for row in payload]
            raw = [raw[0]] + raw[2:]
            count = len(raw[0])
            data = [[Paragraph(inline_pdf(cell), table_head if r == 0 else table_body) for cell in row] for r, row in enumerate(raw)]
            if count == 2:
                widths = [doc.width * 0.23, doc.width * 0.77]
            elif count == 4:
                widths = [doc.width * 0.23, doc.width * 0.19, doc.width * 0.2, doc.width * 0.38]
            else:
                widths = [doc.width / count] * count
            table = Table(data, colWidths=widths, repeatRows=1, hAlign='CENTER')
            commands = [('BACKGROUND', (0, 0), (-1, 0), navy), ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#cbd5e1')), ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 5), ('RIGHTPADDING', (0, 0), (-1, -1), 5), ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]
            for row_index in range(2, len(data), 2):
                commands.append(('BACKGROUND', (0, row_index), (-1, row_index), light))
            table.setStyle(TableStyle(commands))
            story.extend([table, Spacer(1, 8)])
        elif kind == 'image':
            caption_text, relative = payload
            image_path = (SOURCE.parent / relative).resolve()
            image = Image(str(image_path))
            ratio = image.imageHeight / image.imageWidth
            image.drawWidth = doc.width
            image.drawHeight = min(doc.width * ratio, 105 * mm)
            if image.drawHeight == 105 * mm:
                image.drawWidth = image.drawHeight / ratio
            image.hAlign = 'CENTER'
            story.append(KeepTogether([image, Paragraph(inline_pdf(caption_text), caption)]))
    doc.multiBuild(story, onFirstPage=on_page, onLaterPages=on_page)

def add_inline_docx(paragraph, text: str) -> None:
    from docx.shared import RGBColor
    pattern = re.compile('(\\*\\*[^*]+\\*\\*|`[^`]+`|(?<!\\w)\\*[^*]+\\*(?!\\w)|\\[[^\\]]+\\]\\(https?://[^)]+\\))')
    cursor = 0
    for match in pattern.finditer(text):
        if match.start() > cursor:
            paragraph.add_run(text[cursor:match.start()])
        token = match.group(0)
        if token.startswith('**'):
            paragraph.add_run(token[2:-2]).bold = True
        elif token.startswith('`'):
            run = paragraph.add_run(token[1:-1])
            run.font.name = 'Consolas'
            run.font.color.rgb = RGBColor(109, 40, 217)
        elif token.startswith('*'):
            paragraph.add_run(token[1:-1]).italic = True
        else:
            link = re.match('\\[([^]]+)\\]\\((https?://[^)]+)\\)', token)
            run = paragraph.add_run(f'{link.group(1)} ({link.group(2)})')
            run.font.color.rgb = RGBColor(21, 94, 117)
        cursor = match.end()
    if cursor < len(text):
        paragraph.add_run(text[cursor:])

def build_docx(text: str) -> None:
    from docx import Document
    from docx.enum.section import WD_SECTION
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Inches, Mm, Pt, RGBColor
    document = Document()
    section = document.sections[0]
    section.page_width = Mm(210)
    section.page_height = Mm(297)
    section.left_margin = Mm(19)
    section.right_margin = Mm(19)
    section.top_margin = Mm(20)
    section.bottom_margin = Mm(18)
    section.different_first_page_header_footer = True
    styles = document.styles
    normal = styles['Normal']
    normal.font.name = 'Aptos'
    normal.font.size = Pt(10)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.13
    for name, size, color in (('Title', 30, '172554'), ('Heading 1', 17, '172554'), ('Heading 2', 13, '6D28D9'), ('Heading 3', 11, '0E7490')):
        styles[name].font.name = 'Aptos Display'
        styles[name].font.size = Pt(size)
        styles[name].font.color.rgb = RGBColor.from_string(color)
        styles[name].font.bold = True
        styles[name].paragraph_format.keep_with_next = True
        styles[name].paragraph_format.space_before = Pt(12)
        styles[name].paragraph_format.space_after = Pt(6)
    header = section.header.paragraphs[0]
    header.text = 'CT-486 · Complex Computing Problem                                      VRFC · Fall 2026'
    header.style = styles['Caption']
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run(f'{AUTHOR} · {REGISTRATION}    |    Page ')
    field = OxmlElement('w:fldSimple')
    field.set(qn('w:instr'), 'PAGE')
    footer._p.append(field)
    document.core_properties.title = 'Design and Break a Custom Cipher — VRFC'
    document.core_properties.author = AUTHOR
    document.core_properties.subject = 'Network and Information Security (CT-486), CCP Fall 2026'
    document.add_paragraph('NETWORK AND INFORMATION SECURITY · CT-486', style='Subtitle').alignment = WD_ALIGN_PARAGRAPH.CENTER
    document.add_paragraph('')
    title = document.add_paragraph('Design and Break\na Custom Cipher', style='Title')
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle = document.add_paragraph('Vigenère–Rail-Fence Cascade (VRFC)')
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.runs[0].font.size = Pt(16)
    subtitle.runs[0].font.color.rgb = RGBColor(109, 40, 217)
    document.add_paragraph('')
    badge = document.add_table(rows=1, cols=3)
    badge.style = 'Table Grid'
    for cell, label, color in zip(badge.rows[0].cells, ('TWO CLASSICAL STAGES', 'DUAL ATTACK SIMULATION', 'MEASURED RESULTS'), ('6D28D9', '0E7490', '172554')):
        cell.text = label
        shading = OxmlElement('w:shd')
        shading.set(qn('w:fill'), color)
        cell._tc.get_or_add_tcPr().append(shading)
        for run in cell.paragraphs[0].runs:
            run.font.color.rgb = RGBColor(255, 255, 255)
            run.font.bold = True
            run.font.size = Pt(8)
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    document.add_paragraph('')
    info = document.add_table(rows=0, cols=2)
    info.style = 'Table Grid'
    for label, value in (('Submitted by', AUTHOR), ('Registration no.', REGISTRATION), ('Assessment', 'Complex Computing Problem · CLO3'), ('Term', 'Fall 2026'), ('Submission deadline', '8 November 2026'), ('Maximum marks', '10')):
        cells = info.add_row().cells
        cells[0].text = label
        cells[1].text = value
        cells[0].paragraphs[0].runs[0].font.bold = True
    document.add_paragraph('Advanced technical report · implementation · cryptanalysis · reproducible benchmarks', style='Caption').alignment = WD_ALIGN_PARAGRAPH.CENTER
    document.add_page_break()
    document.add_heading('Contents', level=1)
    for kind, payload in markdown_blocks(text):
        if kind == 'heading' and payload[0] <= 2:
            paragraph = document.add_paragraph(payload[1])
            paragraph.paragraph_format.left_indent = Mm((payload[0] - 1) * 6)
            paragraph.paragraph_format.space_after = Pt(2)
    document.add_page_break()

    def shade_paragraph(paragraph, fill: str):
        shading = OxmlElement('w:shd')
        shading.set(qn('w:fill'), fill)
        paragraph._p.get_or_add_pPr().append(shading)
    for kind, payload in markdown_blocks(text):
        if kind == 'heading':
            level, title_text = payload
            document.add_heading(title_text, level=level)
        elif kind == 'paragraph':
            add_inline_docx(document.add_paragraph(), payload)
        elif kind == 'bullet':
            add_inline_docx(document.add_paragraph(style='List Bullet'), payload)
        elif kind == 'number':
            add_inline_docx(document.add_paragraph(), payload)
        elif kind == 'quote':
            paragraph = document.add_paragraph()
            add_inline_docx(paragraph, payload)
            paragraph.paragraph_format.left_indent = Mm(5)
            paragraph.paragraph_format.right_indent = Mm(5)
            shade_paragraph(paragraph, 'ECFEFF')
            for run in paragraph.runs:
                run.italic = True
        elif kind == 'code':
            paragraph = document.add_paragraph()
            paragraph.paragraph_format.left_indent = Mm(3)
            paragraph.paragraph_format.right_indent = Mm(3)
            shade_paragraph(paragraph, '0F172A')
            lines = payload.splitlines()
            for index, line in enumerate(lines):
                run = paragraph.add_run(line)
                run.font.name = 'Consolas'
                run.font.size = Pt(7.5)
                run.font.color.rgb = RGBColor(226, 232, 240)
                if index < len(lines) - 1:
                    run.add_break()
        elif kind == 'table':
            raw = [[cell.strip() for cell in row.strip('|').split('|')] for row in payload]
            raw = [raw[0]] + raw[2:]
            table = document.add_table(rows=len(raw), cols=len(raw[0]))
            table.style = 'Table Grid'
            for r, row in enumerate(raw):
                for c, value in enumerate(row):
                    cell = table.cell(r, c)
                    cell.text = ''
                    add_inline_docx(cell.paragraphs[0], value)
                    for run in cell.paragraphs[0].runs:
                        run.font.size = Pt(8)
                        if r == 0:
                            run.font.bold = True
                            run.font.color.rgb = RGBColor(255, 255, 255)
                    if r == 0:
                        shading = OxmlElement('w:shd')
                        shading.set(qn('w:fill'), '172554')
                        cell._tc.get_or_add_tcPr().append(shading)
            document.add_paragraph('')
        elif kind == 'image':
            caption_text, relative = payload
            image_path = (SOURCE.parent / relative).resolve()
            picture = document.add_picture(str(image_path), width=Inches(6.45))
            document.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
            caption = document.add_paragraph(style='Caption')
            add_inline_docx(caption, caption_text)
            caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
    document.save(DOCX_OUT)

def main() -> None:
    text = expanded_markdown()
    build_pdf(text)
    build_docx(text)
    print(PDF_OUT)
    print(DOCX_OUT)
if __name__ == '__main__':
    main()
