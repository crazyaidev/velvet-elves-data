"""Generate Word documents from project source files."""
import argparse
import re
from pathlib import Path
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn


BASE_DIR = Path(__file__).resolve().parent
BODY_FONT_SIZE = Pt(10)
TABLE_HEADER_FILL = "D9E2F3"
INLINE_MARKDOWN_PATTERN = re.compile(r"(\*\*.+?\*\*|`.+?`)")
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$")
BULLET_PATTERN = re.compile(r"^(\s*)-\s+(.+)$")
ORDERED_LIST_PATTERN = re.compile(r"^(\s*)(\d+)\.\s+(.+)$")
METADATA_PATTERN = re.compile(r"^\*\*(.+?):\*\*\s*(.+)$")
TABLE_DIVIDER_PATTERN = re.compile(r"^:?-{3,}:?$")


def set_cell_shading(cell, color_hex):
    """Set cell background color."""
    shading = cell._element.get_or_add_tcPr()
    shd = shading.makeelement(qn('w:shd'), {
        qn('w:val'): 'clear',
        qn('w:color'): 'auto',
        qn('w:fill'): color_hex,
    })
    shading.append(shd)


def add_styled_paragraph(doc, text, style_name, bold=False, color=None, size=None, alignment=None, space_after=None, space_before=None):
    """Add a paragraph with optional styling."""
    p = doc.add_paragraph(style=style_name)
    run = p.add_run(text)
    if bold:
        run.bold = True
    if color:
        run.font.color.rgb = color
    if size:
        run.font.size = size
    if alignment is not None:
        p.alignment = alignment
    if space_after is not None:
        p.paragraph_format.space_after = space_after
    if space_before is not None:
        p.paragraph_format.space_before = space_before
    return p


def read_source_lines(filename):
    """Read a source file from the repo root."""
    return (BASE_DIR / filename).read_text(encoding="utf-8-sig").splitlines()


def save_document(doc, filename):
    """Save a document into the repo root."""
    output_path = BASE_DIR / filename
    doc.save(output_path)
    print(f"Created {output_path.name}")


def add_text_run(paragraph, text, bold=False, code=False, size=BODY_FONT_SIZE):
    """Add a run with consistent sizing and optional inline-code styling."""
    if not text:
        return None

    run = paragraph.add_run(text)
    run.bold = bold
    run.font.size = size
    if code:
        run.font.name = "Consolas"
    return run


def add_inline_markdown_runs(paragraph, text, size=BODY_FONT_SIZE, force_bold=False):
    """Render simple markdown inline styles inside a paragraph."""
    cursor = 0

    for match in INLINE_MARKDOWN_PATTERN.finditer(text):
        if match.start() > cursor:
            add_text_run(paragraph, text[cursor:match.start()], bold=force_bold, size=size)

        token = match.group(0)
        if token.startswith("**") and token.endswith("**"):
            add_text_run(paragraph, token[2:-2], bold=True, size=size)
        else:
            add_text_run(paragraph, token[1:-1], bold=force_bold, code=True, size=size)

        cursor = match.end()

    if cursor < len(text):
        add_text_run(paragraph, text[cursor:], bold=force_bold, size=size)


def strip_inline_markdown(text):
    """Remove inline markdown markers for headings and titles."""
    return text.replace("**", "").replace("`", "")


def split_markdown_table_row(line):
    """Split a markdown table row into cells."""
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_markdown_table_divider(cells):
    """Detect the markdown divider row between table header and body."""
    return bool(cells) and all(TABLE_DIVIDER_PATTERN.fullmatch(cell.replace(" ", "")) for cell in cells)


def set_markdown_cell_text(cell, text, force_bold=False):
    """Write markdown-aware text into a table cell."""
    cell.text = ""
    paragraph = cell.paragraphs[0]
    add_inline_markdown_runs(paragraph, text, force_bold=force_bold)
    paragraph.paragraph_format.space_after = Pt(0)


def add_markdown_table(doc, table_lines):
    """Render a basic markdown table into the Word document."""
    parsed_rows = [split_markdown_table_row(line) for line in table_lines]
    parsed_rows = [row for row in parsed_rows if any(cell for cell in row)]
    if not parsed_rows:
        return

    header = parsed_rows[0]
    data_rows = parsed_rows[1:]
    if data_rows and is_markdown_table_divider(data_rows[0]):
        data_rows = data_rows[1:]

    all_rows = [header] + data_rows
    column_count = max(len(row) for row in all_rows)

    table = doc.add_table(rows=len(all_rows), cols=column_count)
    table.style = 'Light Grid Accent 1'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    for column_index in range(column_count):
        header_text = header[column_index] if column_index < len(header) else ""
        cell = table.rows[0].cells[column_index]
        set_markdown_cell_text(cell, header_text, force_bold=True)
        set_cell_shading(cell, TABLE_HEADER_FILL)

    for row_index, row_data in enumerate(data_rows, start=1):
        for column_index in range(column_count):
            value = row_data[column_index] if column_index < len(row_data) else ""
            set_markdown_cell_text(table.rows[row_index].cells[column_index], value)

    doc.add_paragraph()


def extract_feedback_header(lines):
    """Extract the title and metadata block from design-feedback.md."""
    title = "Design Feedback"
    metadata = []
    body_start = len(lines)

    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue

        heading_match = re.match(r"^#\s+(.+)$", stripped)
        if heading_match and title == "Design Feedback":
            title = heading_match.group(1).strip()
            continue

        metadata_match = METADATA_PATTERN.match(stripped)
        if metadata_match:
            metadata.append((metadata_match.group(1).strip(), metadata_match.group(2).strip()))
            continue

        if stripped == "---":
            body_start = index + 1
            break

        body_start = index
        break

    return title, metadata, lines[body_start:]


def split_document_title(title):
    """Split a markdown title into primary and secondary title lines."""
    parts = re.split(r"\s+[\u2014-]\s+", title, maxsplit=1)
    main_title = parts[0].strip().upper() if parts else "DESIGN FEEDBACK"
    subtitle = parts[1].strip() if len(parts) > 1 else ""
    return main_title, subtitle


def add_marked_list_paragraph(doc, marker, text, level=0, size=BODY_FONT_SIZE):
    """Add an indented paragraph that uses a visible list marker."""
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.left_indent = Cm(0.63 * (level + 1))
    paragraph.paragraph_format.first_line_indent = Cm(-0.45)
    paragraph.paragraph_format.space_after = Pt(2)
    add_text_run(paragraph, f"{marker} ", size=size)
    add_inline_markdown_runs(paragraph, text, size=size)
    return paragraph


def render_feedback_body(doc, lines):
    """Render the main markdown body of design-feedback.md."""
    index = 0

    while index < len(lines):
        raw_line = lines[index]
        stripped = raw_line.strip()

        if not stripped:
            index += 1
            continue

        if stripped == "---":
            spacer = doc.add_paragraph()
            spacer.paragraph_format.space_after = Pt(6)
            index += 1
            continue

        if stripped.startswith("|"):
            table_lines = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index].strip())
                index += 1
            add_markdown_table(doc, table_lines)
            continue

        heading_match = HEADING_PATTERN.match(stripped)
        if heading_match:
            level = len(heading_match.group(1))
            heading_text = strip_inline_markdown(heading_match.group(2))

            if level <= 2:
                add_styled_paragraph(doc, heading_text, 'Heading 1',
                                     space_before=Pt(18), space_after=Pt(6))
            elif level == 3:
                add_styled_paragraph(doc, heading_text, 'Heading 2',
                                     space_before=Pt(12), space_after=Pt(4))
            else:
                add_styled_paragraph(doc, heading_text, 'Heading 3',
                                     space_before=Pt(8), space_after=Pt(4))

            index += 1
            continue

        bullet_match = BULLET_PATTERN.match(raw_line)
        if bullet_match:
            level = len(bullet_match.group(1).expandtabs(2)) // 2
            add_marked_list_paragraph(doc, "-", bullet_match.group(2).strip(), level=level)
            index += 1
            continue

        ordered_match = ORDERED_LIST_PATTERN.match(raw_line)
        if ordered_match:
            level = len(ordered_match.group(1).expandtabs(2)) // 2
            add_marked_list_paragraph(doc, f"{ordered_match.group(2)}.", ordered_match.group(3).strip(), level=level)
            index += 1
            continue

        paragraph_lines = [stripped]
        index += 1

        while index < len(lines):
            next_raw = lines[index]
            next_stripped = next_raw.strip()
            if not next_stripped:
                break
            if next_stripped == "---" or next_stripped.startswith("|") or \
               HEADING_PATTERN.match(next_stripped) or BULLET_PATTERN.match(next_raw) or \
               ORDERED_LIST_PATTERN.match(next_raw):
                break
            paragraph_lines.append(next_stripped)
            index += 1

        paragraph = doc.add_paragraph()
        add_inline_markdown_runs(paragraph, " ".join(paragraph_lines))
        paragraph.paragraph_format.space_after = Pt(4)


def create_requirements_doc():
    doc = Document()

    # Page margins
    for section in doc.sections:
        section.top_margin = Cm(2.54)
        section.bottom_margin = Cm(2.54)
        section.left_margin = Cm(2.54)
        section.right_margin = Cm(2.54)

    # --- TITLE PAGE ---
    doc.add_paragraph()
    doc.add_paragraph()
    add_styled_paragraph(doc, "VELVET ELVES", 'Title', bold=True,
                         alignment=WD_ALIGN_PARAGRAPH.CENTER, size=Pt(28))
    add_styled_paragraph(doc, "AI-First Transaction Management Platform", 'Subtitle',
                         alignment=WD_ALIGN_PARAGRAPH.CENTER, size=Pt(18))
    doc.add_paragraph()
    add_styled_paragraph(doc, "ESTABLISHED PROJECT REQUIREMENTS", 'Heading 1',
                         alignment=WD_ALIGN_PARAGRAPH.CENTER)
    doc.add_paragraph()

    # Info table
    table = doc.add_table(rows=5, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = 'Light Grid Accent 1'
    info = [
        ("Date Established", "March 4, 2026"),
        ("Timeline", "22 Weeks (MVP Delivery)"),
        ("Budget", "Under USD $40,000 (Fixed-Price)"),
        ("Tech Stack", "React (Frontend) | FastAPI (Backend) | OpenAI GPT (AI) | Supabase (Database & Auth) | AWS EC2 (Hosting)"),
        ("Project Type", "Complex SaaS Rebuild"),
    ]
    for i, (label, value) in enumerate(info):
        table.rows[i].cells[0].text = label
        table.rows[i].cells[1].text = value
        for cell in table.rows[i].cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(10)
            if cell == table.rows[i].cells[0]:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.bold = True

    doc.add_page_break()

    # --- TABLE OF CONTENTS placeholder ---
    add_styled_paragraph(doc, "Table of Contents", 'Heading 1', space_after=Pt(12))
    toc_items = [
        "1. User Management & Authentication",
        "2. Transaction Management",
        "3. The Wizard (AI-Driven Transaction Intake Engine)",
        "4. Task Engine (Most Critical Component)",
        "5. Document Management",
        "6. Communication Engine",
        "7. Integrations",
        "8. AI & Automation",
        "9. User Interface & Experience",
        "10. Data Migration & Security",
        "11. Advertising & Monetization",
        "12. Future Features (Non-MVP)",
        "13. Deployment & Infrastructure",
    ]
    for item in toc_items:
        p = doc.add_paragraph(item, style='List Number')
        p.paragraph_format.space_after = Pt(4)

    doc.add_page_break()

    # --- CONTENT ---
    # Read the requirements file
    lines = read_source_lines("requirements.txt")

    # Parse and format
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip the header block (already on title page)
        if stripped.startswith("====") or stripped == "" or stripped.startswith("Date Established") or \
           stripped.startswith("Timeline:") or stripped.startswith("Budget:") or \
           stripped.startswith("Tech Stack:") or stripped == "VELVET ELVES - AI-FIRST TRANSACTION MANAGEMENT PLATFORM" or \
           stripped == "ESTABLISHED PROJECT REQUIREMENTS" or stripped == "END OF REQUIREMENTS":
            i += 1
            continue

        # Major section headers (e.g., "1. USER MANAGEMENT & AUTHENTICATION")
        major_match = re.match(r'^(\d+)\.\s+(.+)$', stripped)
        if major_match and stripped == stripped.upper():
            section_num = major_match.group(1)
            section_title = major_match.group(2).title()
            add_styled_paragraph(doc, f"{section_num}. {section_title}", 'Heading 1',
                                 space_before=Pt(18), space_after=Pt(8))
            i += 1
            continue

        # Sub-section headers (e.g., "1.1 Account Registration & Login")
        sub_match = re.match(r'^(\d+\.\d+)\s+(.+)$', stripped)
        if sub_match:
            sub_num = sub_match.group(1)
            sub_title = sub_match.group(2)
            add_styled_paragraph(doc, f"{sub_num} {sub_title}", 'Heading 2',
                                 space_before=Pt(12), space_after=Pt(6))
            i += 1
            continue

        # Role headers (e.g., "a) Agent")
        role_match = re.match(r'^([a-f])\)\s+(.+)$', stripped)
        if role_match:
            add_styled_paragraph(doc, stripped, 'Heading 3',
                                 space_before=Pt(8), space_after=Pt(4))
            i += 1
            continue

        # Sub-headers like "Roles:", "Deliverables:", etc.
        if stripped.endswith(':') and len(stripped) < 60 and not stripped.startswith('-') and not stripped.startswith('['):
            p = doc.add_paragraph()
            run = p.add_run(stripped)
            run.bold = True
            run.font.size = Pt(10)
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(4)
            i += 1
            continue

        # Bullet items (lines starting with -)
        if stripped.startswith('- '):
            text = stripped[2:]
            p = doc.add_paragraph(text, style='List Bullet')
            p.paragraph_format.space_after = Pt(2)
            i += 1
            continue

        # Sub-bullet items (indented deeper)
        if stripped.startswith('CANNOT') or stripped.startswith('Cannot'):
            p = doc.add_paragraph()
            run = p.add_run(stripped)
            run.bold = True
            run.font.color.rgb = RGBColor(0xCC, 0x00, 0x00)
            run.font.size = Pt(10)
            i += 1
            continue

        # Numbered items within text (e.g., "1. Buyer - Financing")
        num_item = re.match(r'^(\d+)\.\s+(.+)$', stripped)
        if num_item and stripped != stripped.upper():
            p = doc.add_paragraph(stripped, style='List Number')
            p.paragraph_format.space_after = Pt(2)
            i += 1
            continue

        # Regular text
        if stripped:
            p = doc.add_paragraph(stripped)
            p.paragraph_format.space_after = Pt(4)
            for run in p.runs:
                run.font.size = Pt(10)

        i += 1

    save_document(doc, "requirements.docx")


def create_milestones_doc():
    doc = Document()

    for section in doc.sections:
        section.top_margin = Cm(2.54)
        section.bottom_margin = Cm(2.54)
        section.left_margin = Cm(2.54)
        section.right_margin = Cm(2.54)

    # --- TITLE PAGE ---
    doc.add_paragraph()
    doc.add_paragraph()
    add_styled_paragraph(doc, "VELVET ELVES", 'Title', bold=True,
                         alignment=WD_ALIGN_PARAGRAPH.CENTER, size=Pt(28))
    add_styled_paragraph(doc, "AI-First Transaction Management Platform", 'Subtitle',
                         alignment=WD_ALIGN_PARAGRAPH.CENTER, size=Pt(18))
    doc.add_paragraph()
    add_styled_paragraph(doc, "PROJECT MILESTONES", 'Heading 1',
                         alignment=WD_ALIGN_PARAGRAPH.CENTER)
    add_styled_paragraph(doc, "22-Week Timeline", 'Heading 2',
                         alignment=WD_ALIGN_PARAGRAPH.CENTER)
    doc.add_paragraph()

    # Info table
    table = doc.add_table(rows=5, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = 'Light Grid Accent 1'
    info = [
        ("Date Established", "March 4, 2026"),
        ("Start Date", "Week 1 (March 9, 2026)"),
        ("End Date", "Week 22 (August 2, 2026)"),
        ("Budget", "Under USD $40,000 (Fixed-Price)"),
        ("Tech Stack", "React | FastAPI | OpenAI GPT | Supabase | AWS EC2"),
    ]
    for i, (label, value) in enumerate(info):
        table.rows[i].cells[0].text = label
        table.rows[i].cells[1].text = value
        for cell in table.rows[i].cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(10)
            if cell == table.rows[i].cells[0]:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.bold = True

    doc.add_page_break()

    # --- MILESTONE SUMMARY TABLE ---
    add_styled_paragraph(doc, "Milestone Summary", 'Heading 1', space_after=Pt(12))

    summary_table = doc.add_table(rows=8, cols=4)
    summary_table.style = 'Medium Shading 1 Accent 1'
    summary_table.alignment = WD_TABLE_ALIGNMENT.CENTER

    headers = ["Phase", "Weeks", "Focus Area", "Duration"]
    for j, h in enumerate(headers):
        summary_table.rows[0].cells[j].text = h

    summary_data = [
        ("1", "1-3", "Discovery, Architecture & Foundation", "3 weeks"),
        ("2", "4-8", "Core Transaction & Task Engine", "5 weeks"),
        ("3", "9-13", "AI Wizard & Document Management", "5 weeks"),
        ("4", "14-16", "Communication Engine & AI Email", "3 weeks"),
        ("5", "17-19", "Dashboards, Payments & Profiles", "3 weeks"),
        ("6", "20-21", "White-Label, Integrations & Ad Hooks", "2 weeks"),
        ("7", "22", "Testing, Deployment & Launch", "1 week"),
    ]
    for i, row_data in enumerate(summary_data):
        for j, val in enumerate(row_data):
            summary_table.rows[i+1].cells[j].text = val

    doc.add_page_break()

    # --- DETAILED MILESTONES ---
    lines = read_source_lines("milestones.txt")

    i = 0
    in_summary_section = False
    in_dependencies_section = False
    in_roadmap_section = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip header block and separator lines
        if stripped.startswith("====") or stripped.startswith("------") or stripped.startswith("------|"):
            i += 1
            continue

        if stripped in ["", "VELVET ELVES - AI-FIRST TRANSACTION MANAGEMENT PLATFORM",
                        "PROJECT MILESTONES (22-WEEK TIMELINE)",
                        "END OF MILESTONES"]:
            i += 1
            continue

        if stripped.startswith("Date Established:") or stripped.startswith("Start Date:") or \
           stripped.startswith("End Date:") or stripped.startswith("Budget:") or \
           stripped.startswith("Tech Stack:"):
            i += 1
            continue

        # Skip the text summary table (we already made a nice one)
        if stripped == "MILESTONE SUMMARY":
            in_summary_section = True
            i += 1
            continue
        if in_summary_section:
            if stripped.startswith("KEY DEPENDENCIES"):
                in_summary_section = False
            elif stripped.startswith("Phase") or stripped.startswith("TOTAL") or re.match(r'^\d+\s+\|', stripped):
                i += 1
                continue
            else:
                i += 1
                continue

        # Phase headers (e.g., "PHASE 1: DISCOVERY...")
        phase_match = re.match(r'^PHASE\s+(\d+):\s+(.+)$', stripped)
        if phase_match:
            phase_num = phase_match.group(1)
            phase_title = phase_match.group(2).title()
            add_styled_paragraph(doc, f"Phase {phase_num}: {phase_title}", 'Heading 1',
                                 space_before=Pt(24), space_after=Pt(4))
            # Next line should be the week range
            i += 1
            if i < len(lines):
                week_line = lines[i].strip()
                if week_line.startswith("Weeks") or week_line.startswith("Week"):
                    p = doc.add_paragraph()
                    run = p.add_run(week_line)
                    run.italic = True
                    run.font.size = Pt(11)
                    run.font.color.rgb = RGBColor(0x44, 0x72, 0xC4)
                    p.paragraph_format.space_after = Pt(8)
            i += 1
            continue

        # Milestone headers (e.g., "MILESTONE 1.1 - Project Setup...")
        milestone_match = re.match(r'^MILESTONE\s+(\d+\.\d+)\s+-\s+(.+?)(?:\s+\((.+?)\))?$', stripped)
        if milestone_match:
            m_num = milestone_match.group(1)
            m_title = milestone_match.group(2)
            m_weeks = milestone_match.group(3) or ""
            heading_text = f"Milestone {m_num} - {m_title}"
            if m_weeks:
                heading_text += f" ({m_weeks})"
            add_styled_paragraph(doc, heading_text, 'Heading 2',
                                 space_before=Pt(14), space_after=Pt(6))
            i += 1
            continue

        # Section labels
        if stripped == "Deliverables:":
            p = doc.add_paragraph()
            run = p.add_run("Deliverables:")
            run.bold = True
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor(0x2E, 0x74, 0xB5)
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(4)
            i += 1
            continue

        if stripped.startswith("Success Criteria:"):
            p = doc.add_paragraph()
            run = p.add_run("Success Criteria: ")
            run.bold = True
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor(0x00, 0x80, 0x00)
            criteria_text = stripped.replace("Success Criteria: ", "").replace("Success Criteria:", "")
            run2 = p.add_run(criteria_text)
            run2.font.size = Pt(10)
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(12)
            i += 1
            # Continuation lines
            while i < len(lines):
                next_stripped = lines[i].strip()
                if next_stripped and not next_stripped.startswith("[") and not next_stripped.startswith("MILESTONE") and \
                   not next_stripped.startswith("PHASE") and not next_stripped.startswith("====") and \
                   not next_stripped.startswith("KEY") and not next_stripped.startswith("POST-MVP"):
                    run3 = p.add_run(" " + next_stripped)
                    run3.font.size = Pt(10)
                    i += 1
                else:
                    break
            continue

        # Checkbox items
        if stripped.startswith("[ ]"):
            text = stripped[4:]
            p = doc.add_paragraph(style='List Bullet')
            run = p.add_run("[ ] " + text)
            run.font.size = Pt(10)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.left_indent = Cm(1.27)
            i += 1
            # Check for continuation lines (indented sub-items starting with -)
            while i < len(lines):
                next_line = lines[i]
                next_stripped = next_line.strip()
                if next_stripped.startswith("- ") and next_line.startswith("      "):
                    sub_text = next_stripped[2:]
                    sp = doc.add_paragraph(style='List Bullet 2')
                    sr = sp.add_run(sub_text)
                    sr.font.size = Pt(9)
                    sp.paragraph_format.space_after = Pt(1)
                    sp.paragraph_format.left_indent = Cm(2.54)
                    i += 1
                elif next_stripped and not next_stripped.startswith("[") and not next_stripped.startswith("Success") and \
                     not next_stripped.startswith("MILESTONE") and not next_stripped.startswith("PHASE") and \
                     not next_stripped.startswith("====") and not next_stripped.startswith("KEY") and \
                     not next_stripped.startswith("POST-MVP") and not next_stripped.startswith("Deliverables") and \
                     next_line.startswith("      "):
                    # Continuation of the checkbox item
                    run2 = p.add_run(" " + next_stripped)
                    run2.font.size = Pt(10)
                    i += 1
                else:
                    break
            continue

        # Key Dependencies section
        if stripped == "KEY DEPENDENCIES & RISKS":
            in_dependencies_section = True
            doc.add_page_break()
            add_styled_paragraph(doc, "Key Dependencies & Risks", 'Heading 1',
                                 space_before=Pt(18), space_after=Pt(8))
            i += 1
            continue

        # Post-MVP section
        if stripped == "POST-MVP ROADMAP (Beyond 22 Weeks)":
            in_roadmap_section = True
            in_dependencies_section = False
            add_styled_paragraph(doc, "Post-MVP Roadmap (Beyond 22 Weeks)", 'Heading 1',
                                 space_before=Pt(18), space_after=Pt(8))
            i += 1
            continue

        # Numbered dependency items
        dep_match = re.match(r'^(\d+)\.\s+(.+?):\s+(.+)$', stripped)
        if dep_match and in_dependencies_section:
            num = dep_match.group(1)
            title = dep_match.group(2)
            desc = dep_match.group(3)
            p = doc.add_paragraph()
            run_num = p.add_run(f"{num}. {title}: ")
            run_num.bold = True
            run_num.font.size = Pt(10)
            run_desc = p.add_run(desc)
            run_desc.font.size = Pt(10)
            p.paragraph_format.space_after = Pt(6)
            i += 1
            continue

        # Roadmap items (starting with -)
        if stripped.startswith("- ") and in_roadmap_section:
            text = stripped[2:]
            p = doc.add_paragraph(text, style='List Bullet')
            p.paragraph_format.space_after = Pt(3)
            i += 1
            continue

        # Default: regular paragraph
        if stripped:
            p = doc.add_paragraph(stripped)
            p.paragraph_format.space_after = Pt(4)
            for run in p.runs:
                run.font.size = Pt(10)

        i += 1

    save_document(doc, "milestones.docx")


def create_design_feedback_doc():
    """Generate a .docx export of design-feedback.md."""
    doc = Document()

    for section in doc.sections:
        section.top_margin = Cm(2.54)
        section.bottom_margin = Cm(2.54)
        section.left_margin = Cm(2.54)
        section.right_margin = Cm(2.54)

    lines = read_source_lines("design-feedback.md")
    title, metadata, body_lines = extract_feedback_header(lines)
    main_title, subtitle = split_document_title(title)

    # --- TITLE PAGE ---
    doc.add_paragraph()
    doc.add_paragraph()
    add_styled_paragraph(doc, "VELVET ELVES", 'Title', bold=True,
                         alignment=WD_ALIGN_PARAGRAPH.CENTER, size=Pt(28))
    add_styled_paragraph(doc, "AI-First Transaction Management Platform", 'Subtitle',
                         alignment=WD_ALIGN_PARAGRAPH.CENTER, size=Pt(18))
    doc.add_paragraph()
    add_styled_paragraph(doc, main_title, 'Heading 1', bold=True,
                         alignment=WD_ALIGN_PARAGRAPH.CENTER, size=Pt(20))
    if subtitle:
        add_styled_paragraph(doc, subtitle, 'Heading 2',
                             alignment=WD_ALIGN_PARAGRAPH.CENTER, size=Pt(14))
    doc.add_paragraph()

    if metadata:
        table = doc.add_table(rows=len(metadata), cols=2)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.style = 'Light Grid Accent 1'
        for row_index, (label, value) in enumerate(metadata):
            table.rows[row_index].cells[0].text = label
            table.rows[row_index].cells[1].text = value
            for column_index, cell in enumerate(table.rows[row_index].cells):
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.size = BODY_FONT_SIZE
                        if column_index == 0:
                            run.bold = True

    doc.add_page_break()

    # --- CONTENT ---
    render_feedback_body(doc, body_lines)

    save_document(doc, "design-feedback.docx")


TESTING_REVIEW_FEATURES = None  # Populated at bottom of file


def _add_plain_paragraph(doc, text, size=Pt(10), bold=False, space_after=Pt(4), space_before=None):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.size = size
    run.bold = bold
    p.paragraph_format.space_after = space_after
    if space_before is not None:
        p.paragraph_format.space_before = space_before
    return p


def _add_dash_bullet(doc, text, size=Pt(10)):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.left_indent = Cm(0.75)
    paragraph.paragraph_format.first_line_indent = Cm(-0.45)
    paragraph.paragraph_format.space_after = Pt(2)
    add_text_run(paragraph, "-  ", size=size)
    add_text_run(paragraph, text, size=size)
    return paragraph


def _add_dot_bullet(doc, text, size=Pt(10)):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.left_indent = Cm(1.6)
    paragraph.paragraph_format.first_line_indent = Cm(-0.45)
    paragraph.paragraph_format.space_after = Pt(2)
    add_text_run(paragraph, "\u2022  ", size=size)
    add_text_run(paragraph, text, size=size)
    return paragraph


def _add_section_label(doc, text, color=RGBColor(0x1F, 0x3A, 0x5F)):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(11)
    run.font.color.rgb = color
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(3)
    return p


def _render_bullet_group(doc, items):
    """Render a list of (main_text, [sub_bullets]) tuples."""
    for entry in items:
        if isinstance(entry, str):
            _add_dash_bullet(doc, entry)
        else:
            main, subs = entry
            _add_dash_bullet(doc, main)
            for sub in subs:
                _add_dot_bullet(doc, sub)


def _add_feedback_block(doc, lines=8):
    """Add a blank, visually-delimited block where the client can write feedback."""
    _add_section_label(doc, "Feedback", color=RGBColor(0xC0, 0x50, 0x4D))

    hint = doc.add_paragraph()
    hint_run = hint.add_run(
        "Please note below: Status (Pass / Fail / Needs Work), any comments or issues you hit, "
        "and your priority for the improvement ideas above (High / Medium / Low / Skip)."
    )
    hint_run.italic = True
    hint_run.font.size = Pt(9)
    hint_run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
    hint.paragraph_format.space_after = Pt(4)

    for _ in range(lines):
        blank = doc.add_paragraph()
        underline_run = blank.add_run("_" * 90)
        underline_run.font.size = Pt(10)
        underline_run.font.color.rgb = RGBColor(0xBB, 0xBB, 0xBB)
        blank.paragraph_format.space_after = Pt(6)


def create_testing_review_doc():
    """Generate a .docx for client testing review with per-feature feedback space."""
    doc = Document()

    for section in doc.sections:
        section.top_margin = Cm(2.54)
        section.bottom_margin = Cm(2.54)
        section.left_margin = Cm(2.54)
        section.right_margin = Cm(2.54)

    # --- TITLE PAGE ---
    doc.add_paragraph()
    doc.add_paragraph()
    add_styled_paragraph(doc, "VELVET ELVES", 'Title', bold=True,
                         alignment=WD_ALIGN_PARAGRAPH.CENTER, size=Pt(28))
    add_styled_paragraph(doc, "AI-First Transaction Management Platform", 'Subtitle',
                         alignment=WD_ALIGN_PARAGRAPH.CENTER, size=Pt(18))
    doc.add_paragraph()
    add_styled_paragraph(doc, "FRONTEND CLIENT TESTING REVIEW", 'Heading 1', bold=True,
                         alignment=WD_ALIGN_PARAGRAPH.CENTER, size=Pt(20))
    add_styled_paragraph(doc, "Features Currently Complete — Client Feedback Requested", 'Heading 2',
                         alignment=WD_ALIGN_PARAGRAPH.CENTER, size=Pt(13))
    doc.add_paragraph()

    _add_plain_paragraph(doc, "Last Updated: April 15, 2026",
                         bold=True, space_after=Pt(3))
    _add_plain_paragraph(doc, "Test Environment: http://dev.velvetelves.com/",
                         space_after=Pt(3))
    _add_plain_paragraph(doc, "Recommended Browsers: Chrome or Edge (please allow pop-ups and downloads)",
                         space_after=Pt(3))
    _add_plain_paragraph(doc, "Reviewer: Client — please fill in the Feedback block under each feature",
                         space_after=Pt(6))

    doc.add_page_break()

    # --- HOW TO USE ---
    add_styled_paragraph(doc, "How To Use This Document", 'Heading 1',
                         space_before=Pt(6), space_after=Pt(8))

    _add_section_label(doc, "What is in this document")
    _render_bullet_group(doc, [
        "This document lists every frontend feature that is currently complete and needs your review.",
        "Each feature includes the page address, the exact steps to test, the expected result, our ideas for future improvements, and a blank Feedback area for your notes.",
        "Features that are still being built (for example placeholder 'Coming Soon' pages) are intentionally left out of this review.",
    ])

    _add_section_label(doc, "How to fill in the Feedback area")
    _render_bullet_group(doc, [
        "Status — write Pass, Fail, or Needs Work after you try the feature.",
        "Comments — anything you noticed: confusing text, slow actions, wrong results, missing fields, visual issues.",
        "Improvement priority — for the ideas listed under 'Future Improvement Suggestions', please mark each as High, Medium, Low, or Skip.",
    ])

    _add_section_label(doc, "Accounts you will need")
    _render_bullet_group(doc, [
        ("Agent or Elf — covers the main day-to-day workflow.", []),
        ("Team Lead or Admin — needed to see the Delete button on transactions and the admin-only Task Templates pages.", []),
        ("Attorney — loads the attorney-specific workspace at /transactions.", []),
        ("FSBO Customer — verifies the FSBO sidebar layout.", []),
        ("Admin with a known user ID — needed only for the direct user-detail link at /admin/users/<userId>.", []),
    ])

    _add_section_label(doc, "Suggested order of testing")
    _render_bullet_group(doc, [
        "1. Public pages and sign-in / sign-up",
        "2. Onboarding and the first-time tutorial",
        "3. Standard Agent or Elf workflow (dashboard, new transaction, transactions list, documents)",
        "4. Team Lead or Admin extras (delete permission, task templates)",
        "5. Attorney workspace",
        "6. FSBO-customer sidebar",
        "7. Direct links and error pages",
    ])

    doc.add_page_break()

    # --- FEATURES ---
    features = TESTING_REVIEW_FEATURES
    category_order = []
    categories = {}
    for feature in features:
        cat = feature["category"]
        if cat not in categories:
            categories[cat] = []
            category_order.append(cat)
        categories[cat].append(feature)

    for section_index, cat in enumerate(category_order, start=1):
        add_styled_paragraph(doc, f"Section {section_index} — {cat}", 'Heading 1',
                             space_before=Pt(18), space_after=Pt(8))

        for feature in categories[cat]:
            add_styled_paragraph(doc, f"{feature['no']}. {feature['feature']}", 'Heading 2',
                                 space_before=Pt(14), space_after=Pt(4))

            _add_section_label(doc, "Route / Location")
            _add_plain_paragraph(doc, feature["route"], size=Pt(10), space_after=Pt(2))

            _add_section_label(doc, "How To Test")
            _render_bullet_group(doc, feature["how_to_test"])

            _add_section_label(doc, "Expected Result")
            _render_bullet_group(doc, feature["expected_result"])

            _add_section_label(doc, "Future Improvement Suggestions")
            _render_bullet_group(doc, feature["future_ideas"])

            _add_feedback_block(doc, lines=6)

            doc.add_paragraph()

        doc.add_page_break()

    # --- OVERALL FEEDBACK ---
    add_styled_paragraph(doc, "Overall Feedback", 'Heading 1',
                         space_before=Pt(6), space_after=Pt(8))

    overall_labels = [
        "Biggest usability wins you noticed",
        "Biggest friction points you noticed",
        "Features you would like prioritized next",
        "Additional requests or general notes",
    ]
    for label in overall_labels:
        _add_section_label(doc, label)
        for _ in range(6):
            blank = doc.add_paragraph()
            underline_run = blank.add_run("_" * 90)
            underline_run.font.size = Pt(10)
            underline_run.font.color.rgb = RGBColor(0xBB, 0xBB, 0xBB)
            blank.paragraph_format.space_after = Pt(6)

    save_document(doc, "FRONTEND_CLIENT_TESTING_REVIEW.docx")


TESTING_REVIEW_FEATURES = [
    # ============================================================
    # SECTION 1 — PUBLIC & SIGN-IN PAGES
    # ============================================================
    {
        "no": 1,
        "category": "Public & Sign-In Pages",
        "feature": "Terms of Service page",
        "route": "/terms",
        "how_to_test": [
            ("Open the page in two different ways.", [
                "Open /terms while you are signed out.",
                "Open /terms again while signed in as any role.",
            ]),
            ("Scroll the page from top to bottom and read the legal text.", [
                "Check headings and paragraphs render without missing text.",
                "Confirm any links inside the document open correctly.",
            ]),
        ],
        "expected_result": [
            "The page loads without asking you to sign in.",
            "The page title at the top clearly says Terms of Service.",
            "The full legal content appears in a clean, readable layout.",
        ],
        "future_ideas": [
            "Show a 'Last updated' date at the top so readers know which version they are looking at.",
            "Add a clickable Table of Contents so long sections are easy to jump to.",
            "Offer a 'Save as PDF' button for clients who want to keep a copy.",
        ],
    },
    {
        "no": 2,
        "category": "Public & Sign-In Pages",
        "feature": "Privacy Policy page",
        "route": "/privacy",
        "how_to_test": [
            ("Open /privacy while signed out, then open it again while signed in.", []),
            ("Scroll the whole page and read through the policy sections.", [
                "Make sure nothing is cut off on the right side on a wide screen.",
                "Confirm any in-page links work.",
            ]),
        ],
        "expected_result": [
            "The page loads without any sign-in prompt.",
            "The page title clearly says Privacy Policy.",
            "The content reads cleanly in both signed-out and signed-in states.",
        ],
        "future_ideas": [
            "Add jump links to common sections such as data storage and user rights.",
            "Provide a print-friendly layout so clients can save a paper copy.",
            "Summarize key points at the top in plain language.",
        ],
    },
    {
        "no": 3,
        "category": "Public & Sign-In Pages",
        "feature": "Protected page redirect",
        "route": "/dashboard (while signed out)",
        "how_to_test": [
            ("Sign out, then paste /dashboard directly into the browser address bar and press Enter.", []),
        ],
        "expected_result": [
            "The app should send you straight to /login instead of showing the dashboard.",
            "No protected content (such as transactions) should appear on screen.",
        ],
        "future_ideas": [
            "Remember the page you originally tried to open, and take you there after you sign in.",
            "Show a short explanation on the login screen that says 'Please sign in to continue'.",
        ],
    },
    {
        "no": 4,
        "category": "Public & Sign-In Pages",
        "feature": "Register (sign-up) page",
        "route": "/register",
        "how_to_test": [
            ("Check that every field is visible.", [
                "Full name, Email, Password, Confirm Password, Phone (optional), Role, and the Terms / Privacy checkbox.",
                "A Google sign-up button at the top of the form.",
            ]),
            ("Try invalid inputs and make sure the page stops you.", [
                "An invalid email address (for example 'abc' with no @).",
                "A weak password — confirm the password-strength hints appear.",
                "Mismatched Password and Confirm Password.",
                "Leaving the Terms / Privacy box unchecked.",
            ]),
            ("Submit a valid registration using a real email you can check.", []),
        ],
        "expected_result": [
            "Each invalid case shows a clear inline message next to the field.",
            ("After a successful submission, one of two things should happen.", [
                "You are signed in automatically and taken to the /onboarding page.",
                "Or you are taken to /login with a message asking you to confirm your email.",
            ]),
        ],
        "future_ideas": [
            "Check email availability while typing (instead of only after submit).",
            "Add an eye icon that shows / hides the password while typing.",
            "Show a short sentence under each Role to explain what that role can do.",
        ],
    },
    {
        "no": 5,
        "category": "Public & Sign-In Pages",
        "feature": "Login (sign-in) page",
        "route": "/login",
        "how_to_test": [
            ("Check the page content.", [
                "A Google sign-in button is visible at the top.",
                "Email and password fields are visible.",
                "A 'Forgot password?' link is visible.",
                "A link to the Register page is visible.",
            ]),
            ("Try bad inputs.", [
                "Invalid email format — an error should appear.",
                "Wrong password — a clear error banner should appear.",
            ]),
            ("Sign in with a valid account, then refresh the browser tab.", []),
        ],
        "expected_result": [
            "Users who have not finished onboarding go to /onboarding.",
            "Users who have finished onboarding go to /dashboard.",
            "After a page refresh, you are still signed in.",
        ],
        "future_ideas": [
            "Add a 'Remember me' checkbox for longer sessions.",
            "Show a clear lockout message after several failed attempts.",
            "Add optional two-step verification for extra safety.",
        ],
    },
    {
        "no": 6,
        "category": "Public & Sign-In Pages",
        "feature": "Log out",
        "route": "User menu (top-right avatar)",
        "how_to_test": [
            ("Sign in, then open the avatar menu in the top-right corner.", []),
            ("Click Log Out.", []),
            ("After signing out, try to re-open /dashboard directly in the browser.", []),
        ],
        "expected_result": [
            "You are returned to the /login page right away.",
            "Protected pages cannot be opened again until you sign back in.",
        ],
        "future_ideas": [
            "Add a 'Sign out of all devices' option for extra safety if a laptop is shared or lost.",
            "Briefly confirm the sign-out with a small message ('You have been signed out').",
        ],
    },
    {
        "no": 7,
        "category": "Public & Sign-In Pages",
        "feature": "Forgot password",
        "route": "/forgot-password",
        "how_to_test": [
            ("Verify the screen.", [
                "An email field and a 'Send Reset Link' button should be visible.",
            ]),
            ("Try an invalid email format first, then submit a valid email.", []),
        ],
        "expected_result": [
            "Invalid formats are blocked by a clear message.",
            ("A valid submission switches the page into a success state.", [
                "It shows the email address you entered.",
                "It offers a 'Try a different email' link.",
                "It offers a link back to sign in.",
            ]),
        ],
        "future_ideas": [
            "Show the same success message for known and unknown emails so that no one can fish for registered emails.",
            "Add a 'Resend email' button that is enabled after 60 seconds.",
        ],
    },
    {
        "no": 8,
        "category": "Public & Sign-In Pages",
        "feature": "Reset password",
        "route": "/reset-password (opened from the reset email)",
        "how_to_test": [
            ("Open a real reset link from your email inbox.", []),
            ("Try a weak password and confirm the page blocks it.", []),
            ("Enter a strong password and a matching confirmation, then submit.", []),
            ("Also test opening /reset-password directly with no token, or an expired token.", []),
        ],
        "expected_result": [
            "The reset form loads correctly when the link is valid.",
            "A successful reset shows a success screen and then takes you to /login.",
            "An invalid or expired link shows a clear 'Invalid or expired link' screen with a way to request a new one.",
        ],
        "future_ideas": [
            "Show a password strength meter while typing.",
            "Warn the user that all other signed-in sessions will be logged out after reset.",
        ],
    },
    {
        "no": 9,
        "category": "Public & Sign-In Pages",
        "feature": "Email confirmation",
        "route": "/auth/confirm (opened from the confirmation email)",
        "how_to_test": [
            ("Open a valid confirmation link from your email inbox.", []),
            ("Watch the spinner and wait for the redirect.", []),
            ("Also open a broken / malformed confirmation URL.", []),
        ],
        "expected_result": [
            "A valid link signs you in and takes you to /onboarding (new user) or /dashboard (returning user).",
            "A malformed link shows a clear error screen.",
        ],
        "future_ideas": [
            "Show the confirmed email address on the success screen so the user can double-check the right account was confirmed.",
            "Offer a 'Resend confirmation email' button on the error screen.",
        ],
    },
    {
        "no": 10,
        "category": "Public & Sign-In Pages",
        "feature": "Google sign-in and sign-up",
        "route": "/login and /register",
        "how_to_test": [
            ("Click the Google button on the Login page.", []),
            ("Do the same on the Register page.", []),
            ("Approve Google's consent screen.", []),
        ],
        "expected_result": [
            "The browser goes to Google, then comes back through the app's callback page.",
            "You are signed in and taken to /onboarding (new user) or /dashboard (returning user).",
            "If Google sign-in is not configured in this environment, an error message should appear cleanly rather than breaking the page.",
        ],
        "future_ideas": [
            "Add Microsoft / Outlook and Apple sign-in buttons next to Google.",
            "Show the connected Google account email on the first screen after sign-in.",
        ],
    },
    {
        "no": 11,
        "category": "Public & Sign-In Pages",
        "feature": "Invite acceptance",
        "route": "/invite/<token> (opened from the invite email)",
        "how_to_test": [
            ("Open the invite URL.", [
                "Confirm the page shows the invited email and the invited role.",
                "Confirm the form fields for Full Name, Password, and optional Phone.",
            ]),
            ("Submit the form with valid values.", []),
            ("Separately, open an invite URL with an invalid token.", []),
        ],
        "expected_result": [
            "A valid invite signs the new user in and takes them to /onboarding.",
            "An invalid token shows an 'Invalid Invitation' screen with a link back to login.",
        ],
        "future_ideas": [
            "Show a countdown for how long the invite is still valid.",
            "Let the person who sent the invite resend or cancel it from the admin area when that page is built.",
        ],
    },

    # ============================================================
    # SECTION 2 — FIRST-TIME USER EXPERIENCE
    # ============================================================
    {
        "no": 12,
        "category": "First-Time User Experience",
        "feature": "Onboarding wizard",
        "route": "/onboarding",
        "how_to_test": [
            ("Step 1 — Welcome.", [
                "Read the welcome copy and check the progress indicator.",
                "Click Next.",
            ]),
            ("Step 2 — Role & Company.", [
                "Change the Role dropdown.",
                "Enter a company name.",
                "Upload a company logo and confirm the preview appears.",
                "Also test the Skip button on this step.",
            ]),
            ("Step 3 — Integrations.", [
                "Confirm the Gmail Connect button is shown.",
                "Click Connect (if Gmail is configured, confirm the connected state).",
                "Also test the Skip button.",
            ]),
            ("Step 4 — First Transaction.", [
                "Drag and drop a test PDF or use Browse Files.",
                "Confirm the uploaded file name appears.",
                "Also test the Skip button.",
            ]),
            ("Step 5 — All Set.", [
                "Verify the final success screen.",
                "Click Go to Dashboard.",
            ]),
        ],
        "expected_result": [
            "Each step shows the correct fields and text.",
            "Skip behaves as expected on every step.",
            "Clicking Go to Dashboard at the end takes you to /dashboard.",
        ],
        "future_ideas": [
            "Add a 'Save and finish later' option so users can leave and return.",
            "Show a named progress bar at the top (Welcome → Role → Integrations → Transaction → Done).",
            "Preview the uploaded logo at the exact size it will appear in the app's sidebar.",
        ],
    },
    {
        "no": 13,
        "category": "First-Time User Experience",
        "feature": "First-time tutorial overlay",
        "route": "/dashboard (first visit)",
        "how_to_test": [
            ("On the first dashboard visit, an overlay should appear automatically.", [
                "Click Next through all steps.",
                "Click Back to verify you can go back.",
                "Click Skip to verify it closes the overlay.",
            ]),
            ("On the last step, click Get Started.", []),
            ("To test again: clear the browser storage key 'velvet_elves_tutorial_completed' and reload.", []),
        ],
        "expected_result": [
            "The overlay closes after Skip or Get Started.",
            "The overlay does not reappear automatically on the next visit.",
        ],
        "future_ideas": [
            "Create role-specific tutorials (different tips for Agents, Team Leads, and Attorneys).",
            "Add a 'Replay tutorial' button inside the user menu so clients can rewatch it any time.",
        ],
    },

    # ============================================================
    # SECTION 3 — DAILY AGENT / ELF WORKFLOW
    # ============================================================
    {
        "no": 14,
        "category": "Daily Agent / Elf Workflow",
        "feature": "Dashboard home",
        "route": "/dashboard",
        "how_to_test": [
            ("Open the dashboard and check each card.", [
                "A personalized greeting is visible.",
                "'My week' pills show tasks, overdue, completed, and active counts.",
                "'My Tasks' card has Upcoming and Overdue tabs.",
                "'My Deadlines' card has Upcoming and Overdue tabs.",
                "'Upcoming Closings' shows cards or a clean empty state.",
            ]),
            ("Click the New Transaction button.", []),
        ],
        "expected_result": [
            "Every card shows real data or a clean empty state — nothing blank or broken.",
            "The New Transaction button opens the transaction wizard.",
        ],
        "future_ideas": [
            "Let the user reorder or hide cards to personalize their landing page.",
            "Add an 'AI summary of my day' card at the top.",
            "Show a small comparison like 'this week vs last week' on the My Week pills.",
        ],
    },
    {
        "no": 15,
        "category": "Daily Agent / Elf Workflow",
        "feature": "Sidebar and top bar",
        "route": "Every signed-in page",
        "how_to_test": [
            ("Check the sidebar.", [
                "Navigation items change depending on the signed-in role.",
                "KPI tiles in the sidebar show numbers such as overdue tasks, closings this week, etc.",
            ]),
            ("Check the top bar.", [
                "Click 'Today's AI Briefing' — a side panel should open.",
                "Click any status chip (Critical / Needs Attention / On Track) — it should filter the transactions list.",
                "Open the avatar menu — confirm My Profile, Settings, and Log Out.",
                "On a narrow browser window, click the mobile menu icon.",
            ]),
            ("Please note the current state of two items:", [
                "The search field in the top bar is visual only right now and does not run a real search.",
                "The bell icon in the top bar is visual only right now and does not open notifications.",
            ]),
        ],
        "expected_result": [
            "Sidebar navigation and KPIs adjust correctly to the user's role.",
            "The AI Briefing panel opens and closes cleanly.",
            "Status chips take you to the correct filtered transaction view.",
            "The user menu and mobile menu both behave correctly.",
        ],
        "future_ideas": [
            "Turn the top-bar search into a live global search across deals, tasks, and documents.",
            "Wire the bell icon to real notifications with unread counts.",
            "Add a sidebar collapse toggle for users on smaller laptops.",
        ],
    },
    {
        "no": 16,
        "category": "Daily Agent / Elf Workflow",
        "feature": "New Transaction wizard",
        "route": "Opens from the top bar, the sidebar, and the dashboard 'New Transaction' button",
        "how_to_test": [
            ("Start the wizard.", []),
            ("Step 1 — Documents.", [
                "Upload one PDF, then upload several files at once.",
                "Remove a file and confirm the count updates.",
                "Click Split on a PDF to try the page-range selector.",
                "Also try 'Skip upload — enter details manually'.",
            ]),
            ("Step 2 — AI Parsing.", [
                "If you uploaded a document, let AI parsing run.",
                "If it cannot finish, check that you can still continue manually.",
            ]),
            ("Step 3 — Address.", [
                "Fill in Street, City, State, and ZIP.",
                "Leave the 'I confirm this address is correct' box unchecked — Continue should stay disabled.",
                "Check the box and confirm Continue becomes active.",
            ]),
            ("Step 4 — Purchase Info.", [
                "Enter purchase price, closing date, inspection days, financing, title ordered by, and notes.",
                "Toggle Home Warranty and HOA — extra fields should appear.",
                "Click Add Party and add a party.",
            ]),
            ("Step 5 — Missing Info (appears only if something is missing).", [
                "Leave one required field empty to trigger this step on purpose.",
                "Fill it in manually, then try AI Search.",
            ]),
            ("Step 6 — Confirm.", [
                "Review every section.",
                "Click an Edit button to jump back.",
                "Finally click Accept & Create Transaction.",
            ]),
            ("Close the wizard mid-way and confirm the discard warning appears.", []),
        ],
        "expected_result": [
            "Each step shows only the fields described above.",
            "Continue is blocked until required information is present.",
            "At the end, the transaction is created and the list page shows it.",
        ],
        "future_ideas": [
            "Add a 'Save draft and continue later' button.",
            "Show the uploaded document side-by-side with the AI-parsed fields.",
            "Show a confidence badge next to each AI-filled field (High / Medium / Low).",
        ],
    },
    {
        "no": 17,
        "category": "Daily Agent / Elf Workflow",
        "feature": "Active Transactions page",
        "route": "/transactions",
        "how_to_test": [
            ("Check the page header.", [
                "The correct title and the total deal count are shown.",
                "Export CSV, Export Excel, and Print Report buttons are visible.",
            ]),
            ("Use the filter tabs.", [
                "All, Overdue, Due Today, Closing Soon, In Inspection, On Track, Unhealthy.",
                "The list updates as you switch tabs.",
            ]),
            ("Use the sort control.", []),
            ("From the sidebar, switch between Active Transactions, Pending, Closed, and All Transactions.", []),
            ("Click Export CSV and Export Excel — confirm the files download.", []),
            ("Click Print Report — confirm a printable window opens.", []),
            ("Click the floating Ask AI button.", []),
        ],
        "expected_result": [
            "Filter tabs and sidebar filters update the title and the list correctly.",
            "The exports download files named 'transactions.csv' and 'transactions.xls'.",
            "Ask AI opens the AI side panel.",
        ],
        "future_ideas": [
            "Let the user save custom filter views such as 'My hot deals this week'.",
            "Add multi-select and bulk actions on cards (bulk reassign, bulk status change).",
            "Let the user pick which columns to include in the CSV / Excel export.",
        ],
    },
    {
        "no": 18,
        "category": "Daily Agent / Elf Workflow",
        "feature": "Transaction card — Tasks area",
        "route": "Expanded card on /transactions",
        "how_to_test": [
            ("Expand a card.", []),
            ("In the Tasks area, click the checkbox on a task to mark it complete, then click again to mark it incomplete.", []),
            ("Open the task status dropdown and change the status.", []),
            ("Click '+ Add' or '+ Add Task'.", []),
        ],
        "expected_result": [
            "The task state updates on screen right away.",
            "The Add Task button opens the Add Task window.",
        ],
        "future_ideas": [
            "Let the user rename a task inline without opening a modal.",
            "Allow drag-and-drop reordering of tasks.",
            "Add a 'Snooze until' option for tasks the user wants to hide temporarily.",
        ],
    },
    {
        "no": 19,
        "category": "Daily Agent / Elf Workflow",
        "feature": "Transaction card — Key Dates area",
        "route": "Expanded card on /transactions",
        "how_to_test": [
            ("Click any key date row.", []),
            ("Change the date in the popover and click Save.", []),
        ],
        "expected_result": [
            "The new date shows up on the card right away.",
            "Any dates that are overdue are visually marked (for example in red).",
        ],
        "future_ideas": [
            "When a key date changes, preview which downstream tasks will move.",
            "Offer a one-click 'Notify client of new date' option.",
        ],
    },
    {
        "no": 20,
        "category": "Daily Agent / Elf Workflow",
        "feature": "Transaction card — Contacts area",
        "route": "Expanded card on /transactions",
        "how_to_test": [
            ("Expand a contact row and try the phone and email actions if those fields are filled in.", []),
            ("Click the plus button to add a new contact.", []),
            ("On an empty contact group, click the empty-state add area.", []),
        ],
        "expected_result": [
            "The contact creation window opens with the role already chosen, matching the group you clicked.",
        ],
        "future_ideas": [
            "Show 'Last contacted' date next to each person.",
            "Add a 'Log a call' one-click shortcut that records when you called them.",
        ],
    },
    {
        "no": 21,
        "category": "Daily Agent / Elf Workflow",
        "feature": "Add Task window",
        "route": "Opens from an expanded transaction card",
        "how_to_test": [
            ("Open the Add Task window.", [
                "Leave the task name empty and try to save — it should block you.",
                "Enter a name, pick a Completion Method, pick a Due Date, and pick an Assignee (Myself or AI Agent).",
            ]),
            ("Click 'Get AI Suggestions on How to Complete'.", []),
            ("Apply one of the AI suggestions, then submit the task.", []),
        ],
        "expected_result": [
            "The task is created and the window closes.",
            "Applying an AI suggestion fills in the Completion Method when the suggestion provides one.",
        ],
        "future_ideas": [
            "Add a dropdown of common task templates for one-click creation.",
            "Add a 'Recurring task' option (weekly, monthly).",
            "Allow attaching a document while creating the task.",
        ],
    },
    {
        "no": 22,
        "category": "Daily Agent / Elf Workflow",
        "feature": "Add Contact window",
        "route": "Opens from an expanded transaction card",
        "how_to_test": [
            ("Open the Add Contact window from different groups (Buyer, Lender, Title, etc.).", [
                "Confirm the role label matches the group you opened it from.",
                "Confirm Company Name appears for Lender and Title groups.",
            ]),
            ("Enter First Name, Last Name, Phone, Email, and optional Company.", []),
            ("Submit the form.", []),
        ],
        "expected_result": [
            "The new contact is added and the window closes.",
        ],
        "future_ideas": [
            "Offer 'Pick from existing contacts' so vendors used on other deals can be reused without retyping.",
            "Auto-format phone numbers while typing.",
        ],
    },
    {
        "no": 23,
        "category": "Daily Agent / Elf Workflow",
        "feature": "Documents window on a transaction card",
        "route": "Opens from an expanded transaction card",
        "how_to_test": [
            ("Open the Documents window.", [
                "Confirm the list of existing documents appears.",
                "Expand Details on a document and read the metadata.",
            ]),
            ("Click Download on a document.", []),
            ("Click Add Document and upload a new file.", []),
        ],
        "expected_result": [
            "The download link opens the document.",
            "The uploaded file appears in the list, with version and last-updated info.",
        ],
        "future_ideas": [
            "Let the user rename a document without leaving the page.",
            "Suggest the document type automatically when uploading (Contract, Addendum, etc.).",
            "Offer a 'Download all as zip' button for the full packet.",
        ],
    },
    {
        "no": 24,
        "category": "Daily Agent / Elf Workflow",
        "feature": "Transaction history panel",
        "route": "Opens from an expanded transaction card",
        "how_to_test": [
            ("Open the History panel from a card.", [
                "Check that it slides in from the right.",
            ]),
            ("Type in the search box and confirm the list filters.", []),
            ("Confirm events are grouped by date (Today, Yesterday, etc.).", []),
        ],
        "expected_result": [
            "Matching events stay visible and the rest are filtered out.",
        ],
        "future_ideas": [
            "Add filter chips by event type (emails, tasks, documents, AI flags).",
            "Add an 'Export this timeline as PDF' button for client hand-offs.",
        ],
    },
    {
        "no": 25,
        "category": "Daily Agent / Elf Workflow",
        "feature": "Print and AI actions on a transaction card",
        "route": "Expanded card on /transactions",
        "how_to_test": [
            ("Click Print on a card.", []),
            ("Click the next-step suggestion or any AI chip on a card.", []),
        ],
        "expected_result": [
            "Print opens a printable closing-checklist window.",
            "AI chips open the AI side panel.",
        ],
        "future_ideas": [
            "Let the user pick a print template (full checklist, one-pager, client summary).",
            "Let the user decide which sections to include in the printout.",
        ],
    },
    {
        "no": 26,
        "category": "Daily Agent / Elf Workflow",
        "feature": "Velvet Elves AI chat panel",
        "route": "Top bar 'Today's AI Briefing', floating Ask AI button, and AI chips on cards",
        "how_to_test": [
            ("Open and close the panel from each of the three entry points.", []),
            ("Click several of the suggested-action chips at the bottom.", []),
            ("Type your own message such as 'Summarize the Smith deal' and click Send.", []),
            ("Try a deal-specific question with a transaction card expanded so the AI picks up that transaction as context.", []),
            ("Try the message actions on a returned reply — Copy, Edit, Delete, and Regenerate.", []),
        ],
        "expected_result": [
            "Each Send produces a real AI reply (the panel is connected to a live AI service).",
            "Suggested chips fill the input with a useful starting prompt.",
            "Copy, Edit, Delete, and Regenerate all work on existing messages.",
        ],
        "future_ideas": [
            "Save past conversations so users can come back later.",
            "Let users 'pin' a transaction so the AI always uses it as context.",
            "Stream answers word-by-word instead of waiting for the full response.",
        ],
    },
    {
        "no": 27,
        "category": "Daily Agent / Elf Workflow",
        "feature": "Transaction detail page",
        "route": "/transactions/<transactionId>",
        "how_to_test": [
            ("Open a transaction either from the list or from the dashboard.", [
                "Property address, created date, status badge, and status dropdown are visible.",
            ]),
            ("Change the status using the dropdown.", []),
            ("Sign in as Team Lead or Admin — confirm the Delete button is visible and asks for confirmation.", []),
            ("Open each tab and try the available actions.", [
                "Overview — summary card, key dates, status, use case, price.",
                "Tasks — add a task, change status, toggle complete, open task details.",
                "Documents — upload and list documents.",
                "Parties — currently an intentional empty placeholder. No feedback needed yet.",
                "Communications — currently an intentional empty placeholder. No feedback needed yet.",
            ]),
        ],
        "expected_result": [
            "The header reflects the status changes you make.",
            "A successful delete takes the user back to /transactions.",
            "Overview, Tasks, and Documents tabs are fully interactive.",
        ],
        "future_ideas": [
            "Finish the AI Suggestions block on the Overview tab with real-time deal insights.",
            "Add an activity sidebar showing recent emails and task updates at a glance.",
        ],
    },
    {
        "no": 28,
        "category": "Daily Agent / Elf Workflow",
        "feature": "Task detail page (direct link)",
        "route": "/tasks/<taskId>",
        "how_to_test": [
            ("Open a known task URL.", [
                "Confirm name, status, due date, description, automation level, and metadata all appear.",
            ]),
            ("Click Edit Task, change a few fields, and Save.", []),
            ("Click Cancel to exit edit mode without saving.", []),
            ("Open /tasks/non-existent to check the error state.", []),
        ],
        "expected_result": [
            "Edits save and the page returns to read-only view.",
            "An invalid ID shows a clean 'Task not found' screen.",
        ],
        "future_ideas": [
            "Add a 'Open task detail' button inside expanded transaction cards so users don't need to type URLs.",
            "Add a comments thread on each task for collaboration.",
        ],
    },
    {
        "no": 29,
        "category": "Daily Agent / Elf Workflow",
        "feature": "Documents page",
        "route": "/documents",
        "how_to_test": [
            ("Open /documents.", [
                "Verify the page header and Upload button.",
            ]),
            ("Type in the search box to filter documents by name.", []),
            ("Toggle between grid and list view.", []),
            ("Upload a supported file.", []),
            ("Click a document to open its detail dialog.", []),
        ],
        "expected_result": [
            "Search narrows the list by file name.",
            "Uploads appear in the list.",
            "The detail dialog shows file size, upload date, transaction it belongs to, and storage path.",
        ],
        "future_ideas": [
            "Add bulk-select with bulk download or bulk delete.",
            "Add AI auto-tagging of document types on upload.",
            "Add filter chips by transaction and document type.",
        ],
    },
    {
        "no": 30,
        "category": "Daily Agent / Elf Workflow",
        "feature": "My Profile page",
        "route": "/profile",
        "how_to_test": [
            ("Open /profile from the user menu.", [
                "Confirm the summary card (initials, role, status, email, created date).",
            ]),
            ("Edit your name or phone number, then click Save Changes.", []),
        ],
        "expected_result": [
            "A success toast appears and the profile card reflects the update.",
        ],
        "future_ideas": [
            "Allow avatar photo upload.",
            "Add a change-password form on this page.",
            "Add a notification-preferences section (email, in-app, daily digest).",
        ],
    },
    {
        "no": 31,
        "category": "Daily Agent / Elf Workflow",
        "feature": "Settings — Integrations tab",
        "route": "/settings (Integrations tab)",
        "how_to_test": [
            ("Open /settings and go to the Integrations tab.", []),
            ("Click Refresh to reload integrations.", []),
            ("For Gmail, try Connect and then Disconnect.", []),
        ],
        "expected_result": [
            "The Gmail row updates its connected state after each action.",
        ],
        "future_ideas": [
            "Add Microsoft / Outlook and Apple iCloud integrations next to Gmail.",
            "Show a 'Last synced' timestamp and a sync-now button per integration.",
        ],
    },

    # ============================================================
    # SECTION 4 — ADMIN / TEAM LEAD EXTRAS
    # ============================================================
    {
        "no": 32,
        "category": "Admin / Team Lead Extras",
        "feature": "Task Templates list",
        "route": "/admin/task-templates",
        "how_to_test": [
            ("Type in the search box to filter templates.", []),
            ("Confirm templates are grouped by category.", []),
            ("Click New Template and create a template.", [
                "Fill in Name, Description, Automation Level, and Category.",
                "Submit.",
            ]),
            ("Click an existing template to open it.", []),
        ],
        "expected_result": [
            "The newly created template appears in the list right away.",
        ],
        "future_ideas": [
            "Allow CSV import and export of templates.",
            "Add a 'Duplicate this template' shortcut.",
        ],
    },
    {
        "no": 33,
        "category": "Admin / Team Lead Extras",
        "feature": "Task Template detail",
        "route": "/admin/task-templates/<templateId>",
        "how_to_test": [
            ("Open a template.", [
                "Check the read-only detail view.",
            ]),
            ("Click Edit Template and update several fields.", [
                "Name, description, target, milestone label, dependency, float days, automation level, category, sort order, active toggle.",
            ]),
            ("Try the dependency rule builder section.", []),
            ("Click Save.", []),
        ],
        "expected_result": [
            "All changes persist and the page returns to read-only mode.",
        ],
        "future_ideas": [
            "Add a visual dependency graph so admins can see how tasks connect.",
            "Show a 'where used' indicator listing which transaction types use this template.",
        ],
    },
    {
        "no": 34,
        "category": "Admin / Team Lead Extras",
        "feature": "Admin user detail (direct link)",
        "route": "/admin/users/<userId>",
        "how_to_test": [
            ("As an Admin, open a known user ID URL.", []),
            ("Open an invalid user ID to check the error state.", []),
        ],
        "expected_result": [
            "A valid ID renders the user's profile card.",
            "An invalid ID shows a clean error state.",
        ],
        "future_ideas": [
            "Finish the Team Members list page so this page is reachable without typing URLs.",
            "Add an audit trail showing the user's recent actions.",
        ],
    },

    # ============================================================
    # SECTION 5 — ROLE-SPECIFIC WORKSPACES
    # ============================================================
    {
        "no": 35,
        "category": "Role-Specific Workspaces",
        "feature": "Attorney workspace",
        "route": "/transactions (as Attorney)",
        "how_to_test": [
            ("Sign in as an Attorney and open /transactions.", [
                "The page should automatically switch to the attorney layout.",
            ]),
            ("Check the header.", [
                "The attorney-specific title and KPI row are visible.",
            ]),
            ("Use the filter tabs.", [
                "All, Needs Review, Missing Docs, Ready To Release, Clean Files.",
            ]),
            ("Confirm the matter cards render.", []),
            ("Click the floating Ask AI button.", []),
            ("Please note the current state of three header buttons:", [
                "Open review queue — visual only right now.",
                "State rules — visual only right now.",
                "Upload legal packet — visual only right now.",
            ]),
        ],
        "expected_result": [
            "The attorney layout loads with the correct tabs and matter cards.",
            "The Ask AI panel opens correctly.",
        ],
        "future_ideas": [
            "Wire the three header buttons (Open review queue, State rules, Upload legal packet).",
            "Add a quick-reference modal for state recording rules.",
            "Add a 'Sign off all in this packet' bulk action.",
        ],
    },
    {
        "no": 36,
        "category": "Role-Specific Workspaces",
        "feature": "FSBO customer sidebar",
        "route": "Sidebar (as FSBO Customer)",
        "how_to_test": [
            ("Sign in as an FSBO Customer.", [
                "Confirm the sidebar shows: My Properties, Documents, Milestones & Messages, Ask Velvet Elves AI, Notifications, Sharing.",
            ]),
            ("Confirm Dashboard, Transactions, and Documents pages still load cleanly.", []),
            ("Please note which sidebar items are intentional placeholders today:", [
                "Milestones & Messages, Notifications, and Sharing are 'Coming Soon' pages for now.",
            ]),
        ],
        "expected_result": [
            "FSBO sidebar items render correctly.",
            "Dashboard, Transactions, and Documents are reachable and working.",
        ],
        "future_ideas": [
            "Replace the placeholder pages with the FSBO milestone viewer and sharing-link manager planned for Phase 5.",
            "Simplify the home screen for FSBO customers who are less technical.",
        ],
    },

    # ============================================================
    # SECTION 6 — DIRECT LINKS AND ERROR PAGES
    # ============================================================
    {
        "no": 37,
        "category": "Direct Links and Error Pages",
        "feature": "Unauthorized page",
        "route": "/unauthorized (or any blocked page)",
        "how_to_test": [
            ("Sign in as a basic Agent and open one of these URLs directly:", [
                "/team",
                "/admin/task-templates",
                "/admin/users/some-id",
            ]),
        ],
        "expected_result": [
            "The app redirects you to /unauthorized.",
            "A clear 'Access denied' screen appears.",
        ],
        "future_ideas": [
            "Add a 'Request access from your admin' button that emails the tenant admin.",
            "Explain in plain language which role is needed to open the page.",
        ],
    },
    {
        "no": 38,
        "category": "Direct Links and Error Pages",
        "feature": "Not Found (404) page",
        "route": "Any unknown URL, for example /this-does-not-exist",
        "how_to_test": [
            ("Type an invalid URL in the browser address bar and press Enter.", []),
        ],
        "expected_result": [
            "A 404 page appears with a Back to Dashboard button.",
        ],
        "future_ideas": [
            "Add a small search bar on the 404 page that suggests the likely intended page based on the URL.",
        ],
    },
]


TARGET_BUILDERS = {
    "requirements": create_requirements_doc,
    "milestones": create_milestones_doc,
    "design-feedback": create_design_feedback_doc,
    "testing-review": create_testing_review_doc,
}

TARGET_ALIASES = {
    "requirements.txt": "requirements",
    "requirements.docx": "requirements",
    "milestones.txt": "milestones",
    "milestones.docx": "milestones",
    "design-feedback.md": "design-feedback",
    "design-feedback.docx": "design-feedback",
    "design_feedback": "design-feedback",
    "feedback": "design-feedback",
    "testing_review": "testing-review",
    "testing": "testing-review",
    "review": "testing-review",
    "frontend_client_testing_review.csv": "testing-review",
    "frontend_client_testing_review.docx": "testing-review",
    "all": "all",
}


def normalize_targets(raw_targets):
    """Normalize CLI target names into supported document keys."""
    normalized_targets = []

    for raw_target in raw_targets:
        target = TARGET_ALIASES.get(raw_target.lower(), raw_target.lower())
        if target == "all":
            for name in TARGET_BUILDERS:
                if name not in normalized_targets:
                    normalized_targets.append(name)
            continue

        if target not in TARGET_BUILDERS:
            valid = ", ".join(list(TARGET_BUILDERS.keys()) + ["all"])
            raise SystemExit(f"Unknown document target '{raw_target}'. Use one of: {valid}")

        if target not in normalized_targets:
            normalized_targets.append(target)

    return normalized_targets


def main():
    """Parse CLI args and generate the requested documents."""
    parser = argparse.ArgumentParser(description="Generate Word documents from project source files.")
    parser.add_argument(
        "documents",
        nargs="*",
        help="Documents to generate: requirements, milestones, design-feedback, or all.",
    )
    args = parser.parse_args()

    targets = normalize_targets(args.documents or ["requirements", "milestones"])
    for target in targets:
        TARGET_BUILDERS[target]()

    print(f"Done! Created {len(targets)} document(s) in {BASE_DIR}")


if __name__ == "__main__":
    main()
