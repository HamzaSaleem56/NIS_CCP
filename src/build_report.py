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
MEMBERS = (('Hamza Saleem', 'CR-23009'), ('M Imaad Tahir', 'CR-23014'), ('Mesum Raza', 'CR-23032'), ('Waleed Kashif', 'CR-23040'), ('Owais Khan', 'CR-23301'))
AUTHOR = ', '.join((name for name, _ in MEMBERS))
LOGO = REPORT / 'ned-logo.png'
COVER_LINES = ('Complex Computing Problem Report', 'CT-486: Network and Information Security', 'Final Year - Cyber Security', 'Batch: 2023')
SUBMITTED_TO = 'Prof. Dr. Shariq Mahmood Khan (Professor, Department of CS & IT)'
SUBMISSION_DATE = 'November 08, 2026'
TITLE = 'Design and Break a Custom Cipher: Vigenère–Hill Cascade (VHC)'
SERIF_DIR = Path('/usr/share/fonts/truetype/freefont')
MONO_FONT = Path('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf')

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
    known = [r for r in summary if r['attack'].startswith('known-prefix-')]
    freq_table = markdown_table(['Length', 'Exact recovery', '95% Wilson interval', 'Mean letter accuracy', 'Median time'], [[r['ciphertext_length'], f'{r['exact_successes']}/{r['trials']} ({float(r['exact_success_pct']):g}%)', f'{float(r['wilson_95_low_pct']):g}%–{float(r['wilson_95_high_pct']):g}%', f'{float(r['mean_letter_accuracy_pct']):g}%', f'{float(r['median_elapsed_ms']):g} ms'] for r in frequency])
    known_table = markdown_table(['Ciphertext length', 'Known prefix', 'Exact recovery', 'Mean candidates', 'Median time'], [[r['ciphertext_length'], r['attack'].rsplit('-', 1)[1], f'{r['exact_successes']}/{r['trials']} ({float(r['exact_success_pct']):g}%)', f'{float(r['mean_candidates']):g}', f'{float(r['median_elapsed_ms']):g} ms'] for r in known])
    prefix_rows = read_csv('known_prefix_lengths.csv')
    prefix_table_rows = []
    for length in sorted({int(r['known_prefix_length']) for r in prefix_rows}):
        group = [r for r in prefix_rows if int(r['known_prefix_length']) == length]
        successes = sum((int(r['exact_recovery']) for r in group))
        by_key = []
        for key_length in sorted({int(r['key_length']) for r in group}):
            subgroup = [r for r in group if int(r['key_length']) == key_length]
            by_key.append(f'L={key_length}: {sum((int(r['exact_recovery']) for r in subgroup))}/{len(subgroup)}')
        prefix_table_rows.append([str(length), f'{successes}/{len(group)} ({100 * successes / len(group):g}%)', ', '.join(by_key), f'{statistics.mean((int(r['evaluated_candidates']) for r in group)):g}', f'{statistics.median((float(r['elapsed_ms']) for r in group)):g} ms'])
    prefix_table = markdown_table(['Known prefix m', 'Exact recovery', 'By keyword length', 'Mean candidates', 'Median time'], prefix_table_rows)
    performance = read_csv('performance.csv')
    operations = ('shift_encrypt', 'vigenere_encrypt', 'hill_encrypt', 'vhc_encrypt', 'vhc_decrypt')
    perf_rows = []
    for length in (1000, 10000, 100000, 1000000):
        row = [f'{length:,}']
        for operation in operations:
            match = next((r for r in performance if r['operation'] == operation and int(r['input_length']) == length))
            row.append(f'{float(match['median_ms']):g}')
        perf_rows.append(row)
    perf_table = markdown_table(['Characters', 'Shift enc. (ms)', 'Vigenère enc. (ms)', 'Hill enc. (ms)', 'VHC enc. (ms)', 'VHC dec. (ms)'], perf_rows)
    metrics = {r['operation']: float(r['median_ms']) for r in performance if int(r['input_length']) == 1000000}
    performance_analysis = f'At one million characters, VHC encryption took {metrics['vhc_encrypt']:.2f} ms versus {metrics['shift_encrypt']:.2f} ms for Shift encryption (approximately {metrics['vhc_encrypt'] / metrics['shift_encrypt']:.2f}×), while VHC decryption took {metrics['vhc_decrypt']:.2f} ms versus {metrics['shift_decrypt']:.2f} ms for Shift decryption (approximately {metrics['vhc_decrypt'] / metrics['shift_decrypt']:.2f}×).'
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

def inline_pdf(text: str) -> str:
    value = html.escape(text, quote=False)
    value = re.sub('\\[([^\\]]+)\\]\\((https?://[^)]+)\\)', '<link href="\\2">\\1</link>', value)
    value = re.sub('\\*\\*([^*]+)\\*\\*', '<b>\\1</b>', value)
    value = re.sub('`([^`]+)`', '<font name="Mono" size="8.6">\\1</font>', value)
    value = re.sub('(?<!\\w)\\*([^*]+)\\*(?!\\w)', '<i>\\1</i>', value)
    return value

def build_pdf(text: str) -> None:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, XPreformatted
    from reportlab.platypus.tableofcontents import TableOfContents
    pdfmetrics.registerFont(TTFont('Times', str(SERIF_DIR / 'FreeSerif.ttf')))
    pdfmetrics.registerFont(TTFont('TimesBold', str(SERIF_DIR / 'FreeSerifBold.ttf')))
    pdfmetrics.registerFont(TTFont('TimesItalic', str(SERIF_DIR / 'FreeSerifItalic.ttf')))
    pdfmetrics.registerFont(TTFont('TimesBoldItalic', str(SERIF_DIR / 'FreeSerifBoldItalic.ttf')))
    pdfmetrics.registerFont(TTFont('Mono', str(MONO_FONT)))
    pdfmetrics.registerFontFamily('Times', normal='Times', bold='TimesBold', italic='TimesItalic', boldItalic='TimesBoldItalic')
    black = colors.black
    rule = colors.HexColor('#000000')
    shade = colors.HexColor('#ececec')
    styles = getSampleStyleSheet()
    body = ParagraphStyle('BodyCustom', parent=styles['BodyText'], fontName='Times', fontSize=11, leading=14.6, textColor=black, spaceAfter=6.5, alignment=TA_JUSTIFY, splitLongWords=True)
    h1 = ParagraphStyle('Heading1', parent=styles['Heading1'], fontName='TimesBold', fontSize=16, leading=20, textColor=black, spaceBefore=16, spaceAfter=8, keepWithNext=True)
    h2 = ParagraphStyle('Heading2', parent=styles['Heading2'], fontName='TimesBold', fontSize=13, leading=16.5, textColor=black, spaceBefore=11, spaceAfter=5, keepWithNext=True)
    h3 = ParagraphStyle('Heading3', parent=styles['Heading3'], fontName='TimesBoldItalic', fontSize=11.5, leading=14.5, textColor=black, spaceBefore=8, spaceAfter=4, keepWithNext=True)
    caption = ParagraphStyle('Caption', parent=body, fontName='TimesItalic', fontSize=10, leading=12.5, alignment=TA_CENTER, spaceBefore=3, spaceAfter=9)
    bullet = ParagraphStyle('Bullet', parent=body, leftIndent=16, firstLineIndent=0, bulletIndent=4, bulletFontName='Times', bulletFontSize=11, spaceAfter=3.5)
    code_style = ParagraphStyle('Code', parent=body, fontName='Mono', fontSize=8.2, leading=11, textColor=black, alignment=TA_LEFT, spaceAfter=0)
    body_left = ParagraphStyle('BodyLeft', parent=body, alignment=TA_LEFT)
    table_body = ParagraphStyle('TableBody', parent=body, fontSize=9.6, leading=12, alignment=TA_LEFT, spaceAfter=0)
    table_head = ParagraphStyle('TableHead', parent=table_body, fontName='TimesBold')
    quote_style = ParagraphStyle('Quote', parent=body, fontName='TimesItalic', alignment=TA_LEFT, spaceAfter=0)
    center = lambda name, font, size, after: ParagraphStyle(name, parent=body, fontName=font, fontSize=size, leading=size * 1.25, alignment=TA_CENTER, spaceAfter=after)

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
        canvas.setFont('Times', 10)
        canvas.setFillColor(black)
        canvas.drawCentredString(A4[0] / 2, 12 * mm, str(doc.page))
        canvas.restoreState()
    doc = ReportDoc(str(PDF_OUT), pagesize=A4, leftMargin=25 * mm, rightMargin=25 * mm, topMargin=22 * mm, bottomMargin=22 * mm, title=TITLE, author=AUTHOR, subject='Network and Information Security (CT-486), Complex Computing Problem, Fall 2026')
    story = [Spacer(1, 9 * mm)]
    story.append(Paragraph(COVER_LINES[0], center('CoverTitle', 'TimesBold', 24, 9)))
    story.append(Paragraph(COVER_LINES[1], center('CoverCourse', 'TimesBold', 15, 6)))
    story.append(Paragraph(COVER_LINES[2], center('CoverYear', 'Times', 13, 3)))
    story.append(Paragraph(COVER_LINES[3], center('CoverBatch', 'Times', 13, 0)))
    story.append(Spacer(1, 9 * mm))
    logo = Image(str(LOGO), width=53 * mm, height=53 * mm * 744 / 752)
    logo.hAlign = 'CENTER'
    story.append(logo)
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph('Group Members:', center('CoverMembers', 'TimesBold', 15, 8)))
    name_width = 77 * mm
    dot_width = pdfmetrics.stringWidth('.', 'Times', 8.5)
    rows = []
    for name, registration in MEMBERS:
        label = f'Mr. {name}'
        free = name_width - pdfmetrics.stringWidth(label + ' ', 'TimesBold', 10) - 4
        dots = '.' * max(3, int(free / dot_width))
        rows.append([Paragraph(f'<b>{html.escape(label)}</b> <font name="Times" size="8.5">{dots}</font>', ParagraphStyle('Member', parent=body, fontSize=10, leading=12, alignment=TA_LEFT, spaceAfter=0)), Paragraph(f'<b>({registration})</b>', ParagraphStyle('MemberId', parent=body, fontSize=10, leading=12, alignment=TA_LEFT, spaceAfter=0))])
    members = Table(rows, colWidths=[11 * mm + name_width + 20 * mm, 30 * mm], hAlign='LEFT')
    members.setStyle(TableStyle([('LEFTPADDING', (0, 0), (0, -1), 11 * mm), ('RIGHTPADDING', (0, 0), (0, -1), 20 * mm), ('LEFTPADDING', (1, 0), (1, -1), 0), ('RIGHTPADDING', (1, 0), (1, -1), 0), ('TOPPADDING', (0, 0), (-1, -1), 4.6), ('BOTTOMPADDING', (0, 0), (-1, -1), 4.6), ('VALIGN', (0, 0), (-1, -1), 'BOTTOM')]))
    story.append(members)
    story.append(Spacer(1, 11 * mm))
    left_small = ParagraphStyle('CoverInfo', parent=body, fontSize=9.5, leading=13, alignment=TA_LEFT, spaceAfter=3)
    story.append(Paragraph(f'<b>Submitted to:</b> {html.escape(SUBMITTED_TO)}', left_small))
    story.append(Paragraph(f'<b>Submission Date:</b> {SUBMISSION_DATE}', left_small))
    story.append(PageBreak())
    story.append(Paragraph('Contents', ParagraphStyle('ContentsTitle', parent=h1, fontSize=18, alignment=TA_CENTER, spaceAfter=14)))
    toc = TableOfContents()
    toc.dotsMinLevel = 0
    toc.levelStyles = [ParagraphStyle('TOC1', parent=body, fontName='TimesBold', fontSize=11, leading=17, leftIndent=0, firstLineIndent=0, alignment=TA_LEFT), ParagraphStyle('TOC2', parent=body, fontSize=10.5, leading=14, leftIndent=14, firstLineIndent=0, alignment=TA_LEFT), ParagraphStyle('TOC3', parent=body, fontSize=10, leading=13, leftIndent=28, firstLineIndent=0, alignment=TA_LEFT)]
    story.append(toc)
    story.append(PageBreak())
    for kind, payload in markdown_blocks(text):
        if kind == 'heading':
            level, title = payload
            story.append(Paragraph(inline_pdf(title), (h1, h2, h3)[level - 1]))
        elif kind == 'paragraph':
            story.append(Paragraph(inline_pdf(payload), body_left if re.match('^\\[\\d+\\]', payload) or 'https://' in payload else body))
        elif kind in ('bullet', 'number'):
            marker = '•' if kind == 'bullet' else payload.split('.', 1)[0] + '.'
            content = payload if kind == 'bullet' else payload.split('.', 1)[1].strip()
            story.append(Paragraph(inline_pdf(content), bullet, bulletText=marker))
        elif kind == 'quote':
            quote = Table([[Paragraph(inline_pdf(payload), quote_style)]], colWidths=[doc.width])
            quote.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), shade), ('BOX', (0, 0), (-1, -1), 0.5, rule), ('LEFTPADDING', (0, 0), (-1, -1), 10), ('RIGHTPADDING', (0, 0), (-1, -1), 10), ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 7)]))
            story.extend([quote, Spacer(1, 7)])
        elif kind == 'code':
            block = Table([[XPreformatted(html.escape(payload), code_style)]], colWidths=[doc.width])
            block.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), shade), ('BOX', (0, 0), (-1, -1), 0.5, rule), ('LEFTPADDING', (0, 0), (-1, -1), 9), ('RIGHTPADDING', (0, 0), (-1, -1), 9), ('TOPPADDING', (0, 0), (-1, -1), 7), ('BOTTOMPADDING', (0, 0), (-1, -1), 7)]))
            story.extend([block, Spacer(1, 7)])
        elif kind == 'table':
            raw = [[cell.strip() for cell in row.strip('|').split('|')] for row in payload]
            raw = [raw[0]] + raw[2:]
            count = len(raw[0])
            data = [[Paragraph(inline_pdf(cell), table_head if r == 0 else table_body) for cell in row] for r, row in enumerate(raw)]
            if count == 2:
                widths = [doc.width * 0.27, doc.width * 0.73]
            elif count > 6:
                widths = [doc.width * 0.16] + [doc.width * 0.84 / (count - 1)] * (count - 1)
            elif count == 4:
                widths = [doc.width * 0.23, doc.width * 0.19, doc.width * 0.2, doc.width * 0.38]
            else:
                widths = [doc.width / count] * count
            table = Table(data, colWidths=widths, repeatRows=1, hAlign='CENTER')
            table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), shade), ('GRID', (0, 0), (-1, -1), 0.5, rule), ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 5), ('RIGHTPADDING', (0, 0), (-1, -1), 5), ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
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

def _set_font(target, name: str) -> None:
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    rpr = target.element.get_or_add_rPr() if hasattr(target, 'element') and hasattr(target.element, 'get_or_add_rPr') else target._element.get_or_add_rPr()
    fonts = rpr.find(qn('w:rFonts'))
    if fonts is None:
        fonts = OxmlElement('w:rFonts')
        rpr.insert(0, fonts)
    for attr in ('w:asciiTheme', 'w:hAnsiTheme', 'w:eastAsiaTheme', 'w:cstheme'):
        if fonts.get(qn(attr)) is not None:
            del fonts.attrib[qn(attr)]
    for attr in ('w:ascii', 'w:hAnsi', 'w:eastAsia', 'w:cs'):
        fonts.set(qn(attr), name)

def add_inline_docx(paragraph, text: str) -> None:
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
            _set_font(run, 'Consolas')
        elif token.startswith('*'):
            paragraph.add_run(token[1:-1]).italic = True
        else:
            link = re.match('\\[([^]]+)\\]\\((https?://[^)]+)\\)', token)
            paragraph.add_run(f'{link.group(1)} ({link.group(2)})')
        cursor = match.end()
    if cursor < len(text):
        paragraph.add_run(text[cursor:])

def build_docx(text: str) -> None:
    from docx import Document
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Mm, Pt, RGBColor
    black = RGBColor(0, 0, 0)
    document = Document()
    section = document.sections[0]
    section.page_width = Mm(210)
    section.page_height = Mm(297)
    section.left_margin = Mm(25)
    section.right_margin = Mm(25)
    section.top_margin = Mm(22)
    section.bottom_margin = Mm(22)
    section.different_first_page_header_footer = True
    styles = document.styles
    for name in ('Normal', 'Title', 'Subtitle', 'Caption', 'List Bullet', 'Heading 1', 'Heading 2', 'Heading 3'):
        style = styles[name]
        _set_font(style, 'Times New Roman')
        style.font.color.rgb = black
    normal = styles['Normal']
    normal.font.size = Pt(11)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.15
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for name, size, italic in (('Heading 1', 16, False), ('Heading 2', 13, False), ('Heading 3', 11.5, True)):
        styles[name].font.size = Pt(size)
        styles[name].font.bold = True
        styles[name].font.italic = italic
        styles[name].paragraph_format.keep_with_next = True
        styles[name].paragraph_format.space_before = Pt(14 if name == 'Heading 1' else 10)
        styles[name].paragraph_format.space_after = Pt(6)
        styles[name].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    styles['Caption'].font.size = Pt(10)
    styles['Caption'].font.italic = True
    styles['Caption'].font.bold = False
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    page_run = footer.add_run()
    for tag, attr in (('w:fldChar', {'w:fldCharType': 'begin'}), ('w:instrText', None), ('w:fldChar', {'w:fldCharType': 'end'})):
        element = OxmlElement(tag)
        if attr:
            for key, value in attr.items():
                element.set(qn(key), value)
        else:
            element.set(qn('xml:space'), 'preserve')
            element.text = 'PAGE'
        page_run._r.append(element)
    document.core_properties.title = TITLE
    document.core_properties.author = AUTHOR
    document.core_properties.subject = 'Network and Information Security (CT-486), Complex Computing Problem, Fall 2026'

    def cover_line(value: str, size: float, bold: bool, before: float=0, after: float=0):
        paragraph = document.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.space_before = Pt(before)
        paragraph.paragraph_format.space_after = Pt(after)
        run = paragraph.add_run(value)
        run.font.size = Pt(size)
        run.bold = bold
        return paragraph
    cover_line(COVER_LINES[0], 25, True, before=48, after=8)
    cover_line(COVER_LINES[1], 15.5, True, after=5)
    cover_line(COVER_LINES[2], 13, False, after=2)
    cover_line(COVER_LINES[3], 13, False, after=20)
    logo = document.add_paragraph()
    logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    logo.add_run().add_picture(str(LOGO), width=Mm(50))
    cover_line('Group Members:', 16, True, before=20, after=8)
    for name, registration in MEMBERS:
        paragraph = document.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
        paragraph.paragraph_format.left_indent = Mm(11)
        paragraph.paragraph_format.space_after = Pt(4)
        paragraph.paragraph_format.tab_stops.add_tab_stop(Mm(103), WD_TAB_ALIGNMENT.LEFT, WD_TAB_LEADER.DOTS)
        paragraph.paragraph_format.tab_stops.add_tab_stop(Mm(117), WD_TAB_ALIGNMENT.LEFT, WD_TAB_LEADER.SPACES)
        paragraph.add_run(f'Mr. {name} ').bold = True
        paragraph.add_run('\t\t')
        paragraph.add_run(f'({registration})').bold = True
    for label, value, before in (('Submitted to: ', SUBMITTED_TO, 40), ('Submission Date: ', SUBMISSION_DATE, 0)):
        paragraph = document.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
        paragraph.paragraph_format.space_before = Pt(before)
        paragraph.paragraph_format.space_after = Pt(3)
        paragraph.add_run(label).bold = True
        paragraph.add_run(value)
    document.add_page_break()
    contents = document.add_paragraph()
    contents.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = contents.add_run('Contents')
    run.bold = True
    run.font.size = Pt(18)
    for kind, payload in markdown_blocks(text):
        if kind == 'heading' and payload[0] <= 2:
            paragraph = document.add_paragraph()
            paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
            paragraph.paragraph_format.left_indent = Mm((payload[0] - 1) * 6)
            paragraph.paragraph_format.space_after = Pt(2)
            entry = paragraph.add_run(payload[1])
            entry.bold = payload[0] == 1
    document.add_page_break()

    def shade(element, fill: str):
        shading = OxmlElement('w:shd')
        shading.set(qn('w:val'), 'clear')
        shading.set(qn('w:fill'), fill)
        element.append(shading)

    def border_box(paragraph):
        borders = OxmlElement('w:pBdr')
        for side in ('top', 'left', 'bottom', 'right'):
            edge = OxmlElement(f'w:{side}')
            edge.set(qn('w:val'), 'single')
            edge.set(qn('w:sz'), '4')
            edge.set(qn('w:space'), '4')
            edge.set(qn('w:color'), '000000')
            borders.append(edge)
        paragraph._p.get_or_add_pPr().append(borders)
    for kind, payload in markdown_blocks(text):
        if kind == 'heading':
            level, title_text = payload
            document.add_heading(title_text, level=level)
        elif kind == 'paragraph':
            add_inline_docx(document.add_paragraph(), payload)
        elif kind == 'bullet':
            add_inline_docx(document.add_paragraph(style='List Bullet'), payload)
        elif kind == 'number':
            paragraph = document.add_paragraph()
            paragraph.paragraph_format.left_indent = Mm(6)
            add_inline_docx(paragraph, payload)
        elif kind == 'quote':
            paragraph = document.add_paragraph()
            paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
            add_inline_docx(paragraph, payload)
            paragraph.paragraph_format.left_indent = Mm(4)
            paragraph.paragraph_format.right_indent = Mm(4)
            border_box(paragraph)
            shade(paragraph._p.get_or_add_pPr(), 'ECECEC')
            for run in paragraph.runs:
                run.italic = True
        elif kind == 'code':
            paragraph = document.add_paragraph()
            paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
            paragraph.paragraph_format.left_indent = Mm(4)
            paragraph.paragraph_format.right_indent = Mm(4)
            paragraph.paragraph_format.line_spacing = 1.0
            border_box(paragraph)
            shade(paragraph._p.get_or_add_pPr(), 'ECECEC')
            lines = payload.splitlines()
            for index, line in enumerate(lines):
                run = paragraph.add_run(line)
                _set_font(run, 'Consolas')
                run.font.size = Pt(8)
                if index < len(lines) - 1:
                    run.add_break()
        elif kind == 'table':
            raw = [[cell.strip() for cell in row.strip('|').split('|')] for row in payload]
            raw = [raw[0]] + raw[2:]
            table = document.add_table(rows=len(raw), cols=len(raw[0]))
            table.style = 'Table Grid'
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            for r, row in enumerate(raw):
                for c, value in enumerate(row):
                    cell = table.cell(r, c)
                    cell.text = ''
                    cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
                    cell.paragraphs[0].paragraph_format.space_after = Pt(0)
                    add_inline_docx(cell.paragraphs[0], value)
                    for run in cell.paragraphs[0].runs:
                        run.font.size = Pt(9.5)
                        if r == 0:
                            run.font.bold = True
                    if r == 0:
                        shade(cell._tc.get_or_add_tcPr(), 'ECECEC')
            if len(raw[0]) > 6:
                table.autofit = False
                for c, column in enumerate(table.columns):
                    column.width = Mm(28) if c == 0 else Mm(132 / (len(raw[0]) - 1))
                for row in table.rows:
                    for c, cell in enumerate(row.cells):
                        cell.width = Mm(28) if c == 0 else Mm(132 / (len(raw[0]) - 1))
            document.add_paragraph('')
        elif kind == 'image':
            caption_text, relative = payload
            image_path = (SOURCE.parent / relative).resolve()
            document.add_picture(str(image_path), width=Mm(158))
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
