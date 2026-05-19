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


def _write_testing_review_md(output_filename="FRONTEND_CLIENT_TESTING_REVIEW.md"):
    """Generate a client-friendly Markdown version of the testing review."""
    lines = []
    lines.append("# Velvet Elves — Frontend Client Testing Review")
    lines.append("")
    lines.append("## Features Currently Complete — Client Feedback Requested")
    lines.append("")
    lines.append("**Last Updated:** May 13, 2026  ")
    lines.append("**Test Environment:** http://dev.velvetelves.com/  ")
    lines.append("**Recommended Browsers:** Chrome or Edge (please allow pop-ups and downloads)  ")
    lines.append("**Reviewer:** Client — please fill in the Feedback block under each feature")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## How To Use This Document")
    lines.append("")
    lines.append("### What is in this document")
    lines.append("")
    lines.append("- This document lists every frontend feature that is currently complete and needs your review.")
    lines.append("- Each feature includes the page address, the exact steps to test, the expected result, our ideas for future improvements, and a blank Feedback area for your notes.")
    lines.append("- Features that are still being built (for example placeholder 'Coming Soon' pages) are intentionally left out of this review.")
    lines.append("")
    lines.append("### How to fill in the Feedback area")
    lines.append("")
    lines.append("- **Status** — write Pass, Fail, or Needs Work after you try the feature.")
    lines.append("- **Comments** — anything you noticed: confusing text, slow actions, wrong results, missing fields, visual issues.")
    lines.append("- **Improvement priority** — for the ideas listed under 'Future Improvement Suggestions', please mark each as High, Medium, Low, or Skip.")
    lines.append("")
    lines.append("### Accounts you will need")
    lines.append("")
    lines.append("- **Agent or Elf** — covers the main day-to-day workflow.")
    lines.append("- **Team Lead or Admin** — needed to see the Delete button on transactions, the admin-only Task Templates pages, the Deletion Queue on the Documents page, and the full Team Members admin page.")
    lines.append("- **Workspace Owner** — the very first person who registered the brokerage. Required for the Transfer ownership flow and the Settings → Danger Zone (schedule deletion).")
    lines.append("- **Invited member** — sign up by clicking an invite-email link (instead of /register). Required for the invite-accept flow and the invitee branch of the onboarding wizard.")
    lines.append("- **Attorney** — loads the attorney-specific workspace at /transactions.")
    lines.append("- **FSBO Customer** — verifies the FSBO sidebar layout.")
    lines.append("- **Platform admin** (internal Velvet Elves staff only) — required for the /platform/tenants pages.")
    lines.append("")
    lines.append("### Suggested order of testing")
    lines.append("")
    lines.append("1. Public pages and sign-in / sign-up (including the new Organization field on /register)")
    lines.append("2. Invite-accept flow (open an invite link as a brand-new user)")
    lines.append("3. Onboarding wizard (test both founder and invitee branches) and the product tour overlay")
    lines.append("4. Standard Agent or Elf workflow (dashboard, new transaction, transactions list, documents)")
    lines.append("5. Settings and Email Integrations (needed before AI Email Review can send)")
    lines.append("6. AI Email Review queue at /ai-emails")
    lines.append("7. Team Lead or Admin extras — Team Overview, Team Members admin, invite teammate, ownership transfer, deactivate, Company Details, Danger Zone, plus task templates and deletion queue")
    lines.append("8. Attorney workspace")
    lines.append("9. FSBO-customer sidebar")
    lines.append("10. Platform admin pages (internal Velvet Elves staff only)")
    lines.append("11. Direct links and error pages")
    lines.append("")
    lines.append("---")
    lines.append("")

    def _render_md_bullets(items, indent=""):
        out = []
        for entry in items:
            if isinstance(entry, str):
                out.append(f"{indent}- {entry}")
            else:
                main, subs = entry
                out.append(f"{indent}- {main}")
                for sub in subs:
                    out.append(f"{indent}  - {sub}")
        return out

    category_order = []
    categories = {}
    for f in TESTING_REVIEW_FEATURES:
        cat = f["category"]
        if cat not in categories:
            categories[cat] = []
            category_order.append(cat)
        categories[cat].append(f)

    for section_index, cat in enumerate(category_order, start=1):
        lines.append(f"## Section {section_index} — {cat}")
        lines.append("")
        for feature in categories[cat]:
            lines.append(f"### {feature['no']}. {feature['feature']}")
            lines.append("")

            lines.append("**Route / Location**")
            lines.append("")
            lines.append(feature["route"])
            lines.append("")

            lines.append("**How To Test**")
            lines.append("")
            lines.extend(_render_md_bullets(feature["how_to_test"]))
            lines.append("")

            lines.append("**Expected Result**")
            lines.append("")
            lines.extend(_render_md_bullets(feature["expected_result"]))
            lines.append("")

            lines.append("**Future Improvement Suggestions**")
            lines.append("")
            lines.extend(_render_md_bullets(feature["future_ideas"]))
            lines.append("")

            lines.append("**Feedback**")
            lines.append("")
            lines.append("_Please note: Status (Pass / Fail / Needs Work), any comments or issues you hit, and your priority for the improvement ideas above (High / Medium / Low / Skip)._")
            lines.append("")
            lines.append("> _Status:_ ")
            lines.append("> ")
            lines.append("> _Comments:_ ")
            lines.append("> ")
            lines.append("> _Improvement priority:_ ")
            lines.append("")
            lines.append("---")
            lines.append("")

    lines.append("## Overall Feedback")
    lines.append("")
    overall_labels = [
        "Biggest usability wins you noticed",
        "Biggest friction points you noticed",
        "Features you would like prioritized next",
        "Additional requests or general notes",
    ]
    for label in overall_labels:
        lines.append(f"### {label}")
        lines.append("")
        lines.append("> ")
        lines.append("> ")
        lines.append("> ")
        lines.append("")

    output_path = BASE_DIR / output_filename
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Created {output_path.name}")


def create_testing_review_doc():
    """Generate both .docx and .md for client testing review, with per-feature feedback space."""
    _write_testing_review_md()

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

    _add_plain_paragraph(doc, "Last Updated: May 13, 2026",
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
        ("Team Lead or Admin — needed to see the Delete button on transactions, the admin-only Task Templates pages, the Deletion Queue on the Documents page, and the full Team Members admin page.", []),
        ("Workspace Owner — the very first person who registered the brokerage. Required for the Transfer ownership flow and the Settings → Danger Zone (schedule deletion).", []),
        ("Invited member — sign up by clicking an invite-email link (instead of /register). Required for the invite-accept flow and the invitee branch of the onboarding wizard.", []),
        ("Attorney — loads the attorney-specific workspace at /transactions.", []),
        ("FSBO Customer — verifies the FSBO sidebar layout.", []),
        ("Platform admin (internal Velvet Elves staff only) — required for the /platform/tenants pages.", []),
    ])

    _add_section_label(doc, "Suggested order of testing")
    _render_bullet_group(doc, [
        "1. Public pages and sign-in / sign-up (including the new Organization field on /register)",
        "2. Invite-accept flow (open an invite link as a brand-new user)",
        "3. Onboarding wizard (test both founder and invitee branches) and the product tour overlay",
        "4. Standard Agent or Elf workflow (dashboard, new transaction, transactions list, documents)",
        "5. Settings and Email Integrations (needed before AI Email Review can send)",
        "6. AI Email Review queue at /ai-emails",
        "7. Team Lead or Admin extras — Team Overview, Team Members admin, invite teammate, ownership transfer, deactivate, Company Details, Danger Zone, plus task templates and deletion queue",
        "8. Attorney workspace",
        "9. FSBO-customer sidebar",
        "10. Platform admin pages (internal Velvet Elves staff only)",
        "11. Direct links and error pages",
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
            "Open /register and confirm the fields: Full name, Organization (optional), Email, Password, Confirm Password, Phone (optional), and a Terms / Privacy checkbox. A Google sign-up button is also available.",
            "Note: there is no Role dropdown. The first person to register for an organization is automatically the Admin and Owner of a brand-new workspace. To join an existing brokerage you must use an invite link — typing the brokerage name in Organization does not join you to it.",
            "Type an email already in use and confirm the page blocks Create Account and offers a 'Sign in instead' link.",
            "Type a weak password (under 8 characters, no number, no symbol, etc.) and confirm the page shows which rules still need to be met.",
            "Type mismatching passwords and confirm Create Account is blocked until they match.",
            "Leave the Terms / Privacy box unchecked and confirm Create Account is blocked.",
            "Submit a valid registration using an email you can check.",
        ],
        "expected_result": [
            "Each invalid case shows a clear message next to the field, and Create Account stays disabled.",
            "After a successful submission you are either signed in and taken to /onboarding, or taken to /login with a 'please confirm your email' message.",
        ],
        "future_ideas": [
            "Add an eye icon that shows / hides the password while typing.",
            "Show a one-line preview of how the Organization name will appear on outbound emails before you submit.",
            "Add Microsoft / Outlook and Apple sign-up buttons next to Google.",
            "Auto-suggest an Organization name from the email domain (for example 'acme-realty.com' suggests 'Acme Realty').",
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
            "Open the invite link from your email. Both '/invite/<token>' and '/invite/accept?token=<token>' should work.",
            "Confirm the page shows a 'You're invited!' headline, the role you are joining as (Agent, Transaction Coordinator, Team Lead, Attorney, Client, FSBO Customer, or Vendor), and the invited email.",
            "Fill in Full name (required), Create password (required, at least 8 characters with at least one number), and Phone (optional).",
            "Try an empty name or a weak password and confirm the page blocks Submit.",
            "Click 'Join Velvet Elves' to submit.",
            "Separately, paste a fake token in the browser (e.g. /invite/some-fake-token) and confirm an 'Invalid Invitation' screen appears with a 'Go to login' link.",
        ],
        "expected_result": [
            "A valid invite signs the new user in and takes them to /onboarding.",
            "On /onboarding, the wizard skips the Company / brokerage step and shows a read-only 'Joining: {brokerage name}' line instead.",
            "An invalid or expired token shows the 'Invalid Invitation' screen with a way back to login.",
        ],
        "future_ideas": [
            "Show a countdown for how long the invite is still valid (e.g. 'Expires in 6 hours').",
            "Add a password-strength meter that matches the one on the /register page so invitees see the same five rules.",
            "Show the inviter's name (for example 'Sam Closer invited you to Acme Realty') so the recipient knows it is legitimate.",
        ],
    },

    # ============================================================
    # SECTION 2 — FIRST-TIME USER EXPERIENCE
    # ============================================================
    {
        "no": 12,
        "category": "First-Time User Experience",
        "feature": "Onboarding wizard (role-aware flow)",
        "route": "/onboarding",
        "how_to_test": [
            "Sign up for a fresh account or accept an invite. The wizard should open automatically. An account that already finished onboarding is forwarded straight to /dashboard.",
            "Founder vs. invitee: if you self-registered on /register, Step 2 includes a Company / brokerage field and a Brand logo upload. If you joined via an invite, Step 2 hides those fields and shows a read-only 'Joining: {brokerage name}' line instead.",
            "Step 1 — Welcome: confirm the page greets you by first name and shows a short intro for your role. Internal roles see four value cards; external roles (Client, FSBO, Vendor) see two. Click 'Let's go' to advance.",
            "Step 2 — Your Profile: confirm Full name and Phone (auto-formats as you type) are pre-filled, and a Role dropdown lets you pick your role. Founders also see Company / brokerage and Brand logo (PNG, JPEG, WEBP, SVG, GIF; max 2 MB — upload a wrong type or oversize file and confirm a clear error). Switch the Role dropdown to an external role and confirm the email and e-sign steps disappear from the step list.",
            "Step 3 — Email Inbox (internal roles only): connect Gmail or Outlook by clicking Connect. Confirm a real OAuth popup opens; on success the row flips to Connected. You can also click 'Skip for now' to move on.",
            "Step 4 — E-signature (Agent / TC / Team Lead / Attorney only): connect DocuSign through its OAuth popup, or skip.",
            "Final step — All set: confirm you can click 'Create your first transaction' to open the New Transaction wizard, or 'Go to dashboard' to finish. After finishing, refresh — you should land on /dashboard, not back on /onboarding.",
            "Refresh mid-wizard and confirm your previously-saved fields (name, phone, role, company, logo) are remembered even though the wizard restarts at Step 1.",
        ],
        "expected_result": [
            "Each step shows only the fields that match your role.",
            "Internal roles see 4–5 steps; external roles see 3.",
            "Gmail / Outlook / DocuSign connections persist into Settings → Integrations after onboarding.",
            "Logo files outside the allowed types or larger than 2 MB are rejected with a clear message.",
            "Either final-step button marks onboarding complete on the server and triggers the product tour the next time the dashboard loads.",
        ],
        "future_ideas": [
            "Add a 'Save and finish later' option that remembers the current step (today only the field values are remembered).",
            "Detect popup-blocked browsers up front and offer a fallback redirect-based OAuth path.",
            "Preview the uploaded logo at the exact size it will appear in the app's sidebar.",
            "Let a user preview which steps an external role will see before they switch the role dropdown.",
            "Add an invitee-only 'Welcome from {inviter name}' line so the invitee knows who brought them in.",
        ],
    },
    {
        "no": 13,
        "category": "First-Time User Experience",
        "feature": "Product Tour overlay (role-aware walkthrough)",
        "route": "/dashboard (and any other signed-in page once the tour is started)",
        "how_to_test": [
            "Finish onboarding with a fresh test account, then land on the dashboard. The product tour should start automatically.",
            "If you already finished the tour, open Settings → Help & Tour → Start tour to replay it.",
            "Step through the whole tour using Next / Back / Skip. Internal roles (Agent, Transaction Coordinator, Team Lead, Admin) see a 9-step tour covering sidebar KPIs, Active Transactions, My Task Queue, All Documents, AI Briefing, search, notifications, and the New Transaction button.",
            "Sign in as an Attorney and replay the tour — it should be a 5-step tour focused on the matter queue, documents, and AI briefing.",
            "Sign in as a Client, FSBO Customer, or Vendor and replay the tour — it should be a 5-step tour focused on My Properties, Documents, and Ask Velvet Elves AI.",
            "Use the keyboard: → or Enter to advance, ← to go back, Esc to skip. Confirm Cmd+K / Ctrl+K still opens global search mid-tour.",
            "Skip the tour mid-way and confirm it does not mark complete (Settings → Help & Tour → Start tour starts it again from the beginning).",
            "Finish the tour on the final step and confirm it does not auto-start the next time you log in.",
        ],
        "expected_result": [
            "The tour highlights the right element for each step and the tooltip stays on screen.",
            "Internal roles see a 9-step tour; Attorney and external roles see 5-step role-appropriate tours.",
            "Skipping does not lock the tour; only Finish marks it complete.",
            "Settings → Help & Tour always replays the tour for the role you are signed in as.",
        ],
        "future_ideas": [
            "Add per-feature mini-tours (e.g. 'tour just the Documents page') reachable from inline 'New here?' badges.",
            "Show a one-line tip about what to try after Finish (for example 'Try uploading your first contract').",
            "Add an option to slow down the spotlight animation for users with motion sensitivity.",
            "Track tour completion analytics (where users skip) so we can prioritise improvements.",
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
            "Overdue dates are visually flagged.",
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
        "route": "Opens from the 'View / Add Documents' button on an expanded transaction card",
        "how_to_test": [
            "Expand a transaction card on /transactions/active and click View / Add Documents.",
            "Confirm the documents panel opens and lists every document on that transaction.",
            "Confirm each row shows the document name, a status badge (Signed / Awaiting / Flagged / Uploaded), the version, the upload date, and the size.",
            "Click Download on a row. Confirm the file opens in a new browser tab without being blocked by your pop-up blocker, even if the panel has been open for a while.",
            "Click the document name. Confirm it also opens the download in a new tab.",
            "Click Add Document and upload a new file. Confirm the new file appears in the list with its version and upload date.",
            "Click the Email icon on a row (internal users only). Confirm the Email Document window opens above the panel and is clickable.",
            "Click the Version history icon. Confirm the Version history panel opens above the panel and lists every version.",
            "Open the three-dot menu on any row. As an internal user you should see Rename / Classify, Upload new version, and Archive. As a Client / FSBO / Vendor you should see Flag for deletion (or Flagged if you already flagged it).",
            "Click Archive (internal) and confirm a confirmation window opens. Click Confirm and confirm the document leaves the list.",
            "Click Flag for deletion (Client / FSBO / Vendor) and submit a reason. Confirm the row updates to show Flagged.",
            "Press the Escape key — the panel should close.",
        ],
        "expected_result": [
            "Every action (Download, Email, Version history, Rename, Archive, Flag) opens its window or finishes its action visibly above the panel — no clicks land on something hidden behind the backdrop.",
            "Download is not blocked by the browser's pop-up blocker.",
            "Internal users can rename, classify, archive, and email a document from this panel. External users can flag a document for deletion.",
            "Escape closes the panel.",
        ],
        "future_ideas": [
            "Add a Preview window so PDFs render inline instead of opening in a new tab.",
            "Add Send for Signature, Refresh status, and Void envelope buttons here so internal users can finish the signature flow without leaving the transaction card.",
            "Add a status filter (All / Uploaded / Awaiting / Signed / Flagged) and a sort menu to make long document lists easier to scan.",
            "Add an internal Mark for follow-up flag so the agent can mark a document they need to come back to.",
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
        "feature": "All Documents page — open and access",
        "route": "/documents (also reachable as /documents/all)",
        "how_to_test": [
            "Open /documents while signed in as Agent, Transaction Coordinator, Team Lead, Attorney, or Admin.",
            "Try opening /documents while signed in as a Client, For-Sale-By-Owner Customer, or Vendor.",
            "From any page, press Cmd+K (Mac) or Ctrl+K (Windows), search for a document by name, and press Enter on the result.",
        ],
        "expected_result": [
            "Internal roles see the full All Documents page.",
            "Non-internal roles are sent back to their dashboard instead.",
            "The Cmd+K result opens /documents with the right document highlighted and scrolled into view.",
        ],
        "future_ideas": [
            "Show non-internal users a one-line note explaining where they can find documents inside their assigned transactions.",
            "Remember the last filter and sort the user picked between visits.",
        ],
    },
    {
        "no": "27.1",
        "category": "Daily Agent / Elf Workflow",
        "feature": "All Documents — AI Priority queue and Today's Priority card",
        "route": "/documents (default AI Priority tab)",
        "how_to_test": [
            "Open /documents and stay on the AI Priority tab.",
            "Read the Today's Priority card at the top — it should name the most urgent item with a short reason and one or two recommended actions.",
            "Read the AI Briefing strip just below it — a one-sentence summary plus a button that jumps to whichever tab is most relevant right now.",
            "Scroll down the priority list. Each row names the document or missing item, the transaction it belongs to, and the action buttons available.",
        ],
        "expected_result": [
            "The hero and list highlight whatever is most likely to delay a deal.",
            "Clicking the AI Briefing button switches to the matching tab (for example Missing or Sent for Signature).",
        ],
        "future_ideas": [
            "Show a short reason next to each priority row ('Closing in 3 days', 'Awaiting buyer signature for 5 days').",
            "Allow snoozing an item for a day so it drops out of the list without being marked complete.",
        ],
    },
    {
        "no": "27.2",
        "category": "Daily Agent / Elf Workflow",
        "feature": "All Documents — filter tabs and sort",
        "route": "/documents (tabs under the page title)",
        "how_to_test": [
            "Click each filter tab in turn: AI Priority, All Docs, Missing, Pending Review, Sent for Signature, Signed.",
            "Confirm the list narrows to match the chosen tab.",
            "Open the Sort menu and pick each option in turn: AI Impact, Close Date, Document Name, Recently Updated, Last Touched.",
            "Refresh the page after changing tab or sort.",
        ],
        "expected_result": [
            "Every tab shows only the documents that match its name.",
            "Sort instantly reorders the visible list.",
            "Tab and sort choices stay in place after a refresh (they are saved in the URL).",
        ],
        "future_ideas": [
            "Let the user save a favourite tab + sort combination as a one-click shortcut.",
            "Add a 'Group by document type' option alongside the existing sort options.",
        ],
    },
    {
        "no": "27.3",
        "category": "Daily Agent / Elf Workflow",
        "feature": "All Documents — actions on a priority row",
        "route": "/documents (any row in the AI Priority list)",
        "how_to_test": [
            "Click Request on a missing-document row. Confirm the email modal opens with the right recipient and template, and that the row stays in the queue with a 'Requested today' note after Send.",
            "Click Nudge on a row that already had a request. Confirm a shorter follow-up email is drafted and the row updates with a 'Nudged' note.",
            "Click Upload on a missing-document row. Confirm the Upload Document modal opens with the transaction and document type already filled in, and that uploading clears the row.",
            "Find a missing item that does not have a template ready (for example Appraisal Report). Confirm the Generate button is NOT shown — only Upload / Request / Call appear.",
            "Find a missing item that does have a template ready (for example Lead-Based Paint Disclosure). Click Generate.",
            "If the transaction has all the information the template needs, confirm a draft document is created and the preview opens.",
            "If the transaction is missing information (for example the seller name), confirm an 'Almost ready' window appears listing each missing piece in plain English and a Fix button next to each one.",
            "Click Fix on one of the missing pieces. Confirm you are taken straight to the transaction page with the right field highlighted. Fill it in.",
            "Come back to /documents. Confirm the Generate action retries on its own and either opens the draft or shows the next missing piece. You should not have to click Generate a second time.",
            "Trigger Generate on a requirement that has no template at all (rare). Confirm the window now offers real next-step buttons — Upload draft manually or Request from counter-party — instead of a dead 'Got it' button.",
            "Click Approve on a Pending Review row. Confirm the row leaves the queue and appears in the Cleared Today strip.",
            "Click Mark N/A on any row. Confirm a confirmation appears, the row disappears, and an Undo option is available on the Cleared Today card.",
            "Click Flag on any row. Confirm a flag icon appears next to the item and is still there after refresh.",
            "Click Call on a row with a phone number — confirm your phone app opens and the activity is logged on the transaction.",
            "Click Forward on a signed document. Confirm a forward-style email modal opens with the document attached.",
        ],
        "expected_result": [
            "Every action button does something real (sends an email, opens the right modal, or updates the queue).",
            "Request, Nudge, Call, and Forward keep the row visible with a 'last touched' note until the requirement is actually resolved.",
            "Mark N/A, Approve, Upload, and Generate clear the row and add it to the Cleared Today strip at the bottom of the page.",
            "Generate is only offered when the system actually has a template for that requirement.",
            "The missing-fields window never shows raw machine names — every line is plain English with a Fix button.",
        ],
        "future_ideas": [
            "Show 'Next follow-up due in N hours' on touched rows so the user knows when to nudge again.",
            "Add a 'Skip this field' option on the missing-fields window for rare cases where a value is genuinely unavailable.",
        ],
    },
    {
        "no": "27.4",
        "category": "Daily Agent / Elf Workflow",
        "feature": "All Documents — Cleared Today strip",
        "route": "/documents (strip at the bottom of the page)",
        "how_to_test": [
            "Read the Cleared Today header. There should be a one-line description telling you what the strip is — items resolved in the last 24 hours.",
            "Click the information icon next to the header. A short pop-up should explain what each kind of card means (Signed, Approved, Marked N/A, Generated, Replaced, Voided, Uploaded, Reassigned).",
            "Confirm the strip is visible on every tab (AI Priority, Missing, All Docs, Pending Review, Sent for Signature, Signed) — not only on AI Priority.",
            "Resolve a few items different ways (Approve a review, Mark something N/A, Upload a missing document, sign an envelope, generate a draft). Confirm each one shows up as a card on the strip with the matching label.",
            "Send a Request or Nudge from a row. Confirm those touches do NOT show up here — only true resolutions appear on the strip.",
            "On any card, click View Details. Confirm a small read-only window opens with the document name, the transaction, the badge, who cleared it, and when. (No more single whole-card click — every card has clear buttons.)",
            "On a card that points to a real document, click Open. Confirm the document preview opens.",
            "On a Mark N/A card (which does not have a document attached), click Open. Confirm the transaction's Documents view opens — not a dead window.",
            "On an Approved card, click Undo. Confirm the document goes back to Pending Review.",
            "On a Mark N/A card, click Undo. Confirm the row returns to the Missing list.",
            "On a Generated card, click Undo and confirm the draft is removed and the Missing row comes back.",
            "On a Signed card, confirm Undo is not offered, and a short explanation tells you to void the envelope from the document row instead.",
            "Use the filter buttons at the top of the strip: All, Me, Team. Confirm Me shows only items you cleared, Team shows your teammates' clears, and All shows both.",
            "Click 'View all cleared (last 7 days)'. Confirm a panel slides out listing every clear from the past week with the same filter buttons. Scroll down — more rows should load as you reach the bottom.",
            "If you are signed in as a solo agent with no teammates, confirm the Team filter button is not shown.",
        ],
        "expected_result": [
            "The strip explains itself — a new user can tell what it is and what each card means without help.",
            "Cards never use a single 'click the whole card' target. Every card has a View Details button, an Open button, and an Undo where it makes sense.",
            "Only true resolutions appear on the strip — requests, nudges, calls, and forwards do not.",
            "Undo works for Approve, Mark N/A, Generated, and Uploaded clears. Signed, Replaced, and Voided clears explain why they cannot be undone here.",
            "Switching to Me filters the strip to your own clears; Team shows your teammates'.",
            "The 7-day panel shows the same items beyond the last 24 hours, with the same filter buttons.",
        ],
        "future_ideas": [
            "Show a small badge on the Cleared Today header when new items land while you're on a different tab.",
            "Group the 7-day panel by day so it reads like a timeline.",
            "Let the user export the 7-day list to CSV for end-of-week reporting.",
        ],
    },
    {
        "no": "27.5",
        "category": "Daily Agent / Elf Workflow",
        "feature": "All Documents — Upload Document modal",
        "route": "Opens from the 'Upload Document' header button or from 'Upload' on a missing-document row",
        "how_to_test": [
            "Open the Upload modal from the page header button.",
            "Open it again from the Upload action on a missing-document row and confirm the transaction and document type are already filled in.",
            "Drag a PDF onto the drop zone, or browse and pick a file.",
            "Try a file over 20 MB or an unsupported file type (.zip, .xlsx) and confirm the modal shows a clear error.",
            "Click Upload Document to save.",
        ],
        "expected_result": [
            "Allowed file types: PDF, DOC, DOCX, JPG, PNG, WEBP, GIF, TXT, up to 20 MB.",
            "After upload, the new file appears in the document list and resolves the matching missing item if any.",
        ],
        "future_ideas": [
            "Auto-suggest the document type by reading the file contents on upload.",
            "Let the user drag and drop several files at once.",
        ],
    },
    {
        "no": "27.6",
        "category": "Daily Agent / Elf Workflow",
        "feature": "All Documents — Preview and Download",
        "route": "Preview (eye) and Download icons on any document row",
        "how_to_test": [
            "Click the Preview (eye) icon on a PDF or image — the document should open inside the window.",
            "Click Preview on a non-previewable file (for example a .docx) — the window should offer a Download button instead.",
            "Click the Download icon on a row. The document should open in a new browser tab.",
            "Confirm Download is not blocked by your browser's pop-up blocker, even after the page has been open for a while.",
            "From inside the Preview window, click Send for Signature.",
        ],
        "expected_result": [
            "Preview opens the document inside the page so you can read it without leaving.",
            "Download opens the document in a new tab and is never blocked by the pop-up blocker.",
            "Send for Signature from Preview opens the signature modal with the document already selected.",
        ],
        "future_ideas": [
            "Allow side-by-side comparison of two versions in the preview window.",
            "Remember the last zoom level between previews.",
        ],
    },
    {
        "no": "27.7",
        "category": "Daily Agent / Elf Workflow",
        "feature": "All Documents — Send for Signature (DocuSign)",
        "route": "'Send for Signature' header button, the row's signature icon, or the Preview footer",
        "how_to_test": [
            "Open the Send for Signature modal from each of the three entry points (header button, row icon, preview footer).",
            "If your DocuSign account is not yet connected, click the Connect DocuSign button on the banner and complete the popup sign-in.",
            "Add signers using the suggested-party chips (buyer, listing agent, etc.) and / or the 'Add signer' button. Confirm you cannot send until each row has a name and a valid email.",
            "Edit the subject and message that will go to the signers.",
            "Click Send for Signature.",
        ],
        "expected_result": [
            "After Send, a toast confirms the envelope was sent and the row updates to 'Sent for Sig.' with an 'Awaiting: {names}' note.",
            "Recipients receive a DocuSign email immediately.",
            "If sending fails, the error appears both as a toast and inside the modal so the user does not need to reopen it.",
        ],
        "future_ideas": [
            "Let the sender choose sequential vs. parallel signing order.",
            "Show live signature progress inside the modal so the user does not have to refresh the row.",
        ],
    },
    {
        "no": "27.8",
        "category": "Daily Agent / Elf Workflow",
        "feature": "All Documents — manage envelopes already sent for signature (Refresh, Void, Resend)",
        "route": "Rows whose status is Sent for Sig., Declined, or Voided",
        "how_to_test": [
            "Send a document for signature but do not let recipients sign yet. Confirm the row shows the 'Awaiting: …' line listing the recipients.",
            "Click Refresh on the row and confirm a toast reports the current signature status.",
            "Open the row's three-dot menu and click Void Envelope. Confirm a toast appears and the row switches to a 'Voided' state with a Resend option.",
            "Simulate a declined signer in DocuSign (Decline) and refresh — the row should switch to 'Declined' and offer Resend.",
            "Click Resend for Signature from a voided or declined row and confirm the Send for Signature modal reopens with the same document.",
        ],
        "expected_result": [
            "The agent can see who has not signed yet without opening DocuSign.",
            "Refresh updates the row from DocuSign on demand.",
            "Voided and declined envelopes always offer a one-click Resend so a stuck file is never a dead end.",
        ],
        "future_ideas": [
            "When voiding, prompt the user for a short reason that gets passed to DocuSign.",
            "Add a single 'Force-sync all' button that refreshes every in-flight envelope at once.",
        ],
    },
    {
        "no": "27.9",
        "category": "Daily Agent / Elf Workflow",
        "feature": "All Documents — Email Document, Edit Document (Rename / Reclassify / Reassign), Version History",
        "route": "Three-dot menu on any document row (internal roles only). Edit Document is also reachable from the AI Priority queue rows and the priority detail window.",
        "how_to_test": [
            "Open the three-dot menu and click Email Document. Add at least one recipient and click Send Email. Confirm a toast reports the email is queued.",
            "Click Edit Document. The window should show two groups of fields: Identity (file name, label, document type) and Assignment (the transaction this document belongs to).",
            "Try to save with an empty file name and confirm it is blocked.",
            "Change the file name, label, or type and click Save. Confirm the row updates immediately.",
            "Open Edit Document again. Use the Transaction picker to move the document to a different transaction you have access to. A short note should warn you that moving the document reattaches its history and version chain.",
            "Save. Confirm the document leaves the original transaction's list and now appears under the new transaction.",
            "If the document was satisfying a missing requirement on the new transaction, confirm a 'Reassigned' card appears in Cleared Today.",
            "Try to reassign a document that has an envelope already sent for signature, or one that is already signed. Confirm the save is blocked with a clear message asking you to void the envelope first.",
            "Open Edit Document from a row in the AI Priority list (not just from the Three-dot menu on a document row). Confirm it works the same way.",
            "Click Version History. Confirm every version is listed with v1, v2, … and that downloading any historical version still works. Upload a replacement and confirm the latest version is marked Current.",
        ],
        "expected_result": [
            "Email Document queues the email and records it in the transaction's communication history.",
            "Edit Document handles renaming, reclassifying, and reassigning a document in one window. The label is the same everywhere — there is no separate 'Rename' or 'Reassign' button.",
            "Reassigning the document moves it between transactions and shows up in the audit trail of both transactions.",
            "An envelope-in-flight or signed document cannot be reassigned, and the system tells you exactly why.",
            "Uploading a new version moves the previous one to Legacy.",
        ],
        "future_ideas": [
            "Offer saved email templates ('Client intro', 'Title hand-off', etc.).",
            "Allow rolling a Legacy version back to Current.",
            "Use AI to suggest the right document type during Edit Document.",
            "Add a 'Move all related documents' option when reassigning a document — copy / addendum / disclosure as a group.",
        ],
    },
    {
        "no": "27.10",
        "category": "Daily Agent / Elf Workflow",
        "feature": "All Documents — Archive a document",
        "route": "Three-dot menu on any document row (internal roles only)",
        "how_to_test": [
            "Open the three-dot menu on a document and click Archive Document.",
            "Confirm a confirmation dialog appears explaining the document will be archived and can be restored by an authorized user.",
            "Click Archive and confirm the document leaves the list.",
            "Open the Restore Archived panel (test 27.13) and confirm the document appears there, ready to bring back.",
        ],
        "expected_result": [
            "Archiving requires a confirmation step.",
            "After archive, the document leaves the list and is no longer counted in the tabs.",
            "The Restore Archived panel always shows recently archived documents, so an accidental archive can be undone from there.",
        ],
        "future_ideas": [
            "Add a one-click Undo button on the toast right after archive so the user does not have to open the Restore Archived panel for a fresh mistake.",
            "Allow batch archive of several documents at once.",
            "Auto-clean documents that have been archived for over 90 days, with an admin warning two weeks before.",
        ],
    },
    {
        "no": "27.11",
        "category": "Daily Agent / Elf Workflow",
        "feature": "All Documents — Deletion Approval Queue",
        "route": "'Deletion Queue' header button on /documents (internal roles only)",
        "how_to_test": [
            "Sign in as Team Lead, Admin, or any other internal role.",
            "If no clients have flagged anything yet, confirm the Deletion Queue button is not shown at all (the header stays clean).",
            "When at least one document has been flagged for deletion (use 27.15 to flag one as a client / FSBO customer), confirm the Deletion Queue button now appears in the page header with a small number badge showing how many requests are waiting.",
            "Confirm you also see flagged documents inside the AI Priority list as 'Review deletion request' items, with higher importance if the document has already been signed.",
            "Click Deletion Queue. Review each pending request — confirm you can see the document name, the reason given by the requester, and a decision-notes field.",
            "Click Approve on one request. Confirm a clear confirmation window opens before anything is archived. If the document was signed, confirm the warning says so explicitly. Click Archive document to confirm.",
            "Click Reject on another request without typing a reason. Confirm you are blocked with a clear 'please enter a reason' message — Reject requires a reason so the requester knows why their request was turned down.",
            "Add a reason and click Reject. Confirm the document stays in place and the request is closed.",
            "Sign in as the original requester (the client / FSBO / vendor who flagged the document). Confirm they receive an in-app notification AND an email telling them the decision and the reviewer's reason.",
            "Try to approve deletion of a document that has an envelope already sent for signature. Confirm the system blocks it with a message telling you to void the envelope first.",
        ],
        "expected_result": [
            "Every flagged request from a client / FSBO / vendor appears here for an internal reviewer, and also as a priority item in the AI Priority list so it cannot be missed.",
            "The button only shows up when there is work to do — the badge tells you how many requests are waiting.",
            "Approve always requires an explicit confirmation step. Reject always requires a reason.",
            "Both decisions are recorded for audit, and the requester always hears back by notification and email.",
        ],
        "future_ideas": [
            "Add bulk approve / bulk reject for high-volume cleanup.",
            "Show the requester their previous flag history if they have flagged several documents in a short period.",
        ],
    },
    {
        "no": "27.12",
        "category": "Daily Agent / Elf Workflow",
        "feature": "All Documents — Connect DocuSign wizard",
        "route": "'Connect DocuSign' button inside Send for Signature (when no provider is connected yet)",
        "how_to_test": [
            "Make sure DocuSign is not yet connected. Open the Send for Signature modal and click Connect DocuSign on the banner.",
            "In the wizard, click Continue to DocuSign and complete sign-in in the popup that opens.",
            "After the popup closes, click Back to Send for Signature.",
            "Try the failure path: cancel the DocuSign popup before signing in. Confirm the wizard offers a Retry button.",
        ],
        "expected_result": [
            "The whole connection flow happens inside Velvet Elves; the user never leaves /documents.",
            "On success, a toast confirms the connection and the Send for Signature modal becomes usable.",
            "If the popup is cancelled, the wizard offers a retry without restarting from scratch.",
        ],
        "future_ideas": [
            "Send a tiny test envelope to the signed-in user's own email after a successful connection so they can verify the link works.",
            "Detect popup-blocked browsers up front and offer a redirect flow instead.",
        ],
    },
    {
        "no": "27.13",
        "category": "Daily Agent / Elf Workflow",
        "feature": "All Documents — Restore Archived",
        "route": "'Restore archived' button in the page header on /documents (internal roles only)",
        "how_to_test": [
            "Archive one or two documents from the three-dot menu on a row (see test 27.10).",
            "Click the Restore archived button in the page header (it sits next to Send for Sig and Upload).",
            "Confirm a panel opens listing recently archived documents.",
            "Confirm each row shows the document name and the date it was archived.",
            "Click Restore on a row. Confirm the document comes back to the active list and the row leaves the Restore Archived panel.",
        ],
        "expected_result": [
            "Recently archived documents can be restored from this panel without contacting an admin.",
            "Restoring a document brings it back exactly where it was — same transaction, same version history.",
        ],
        "future_ideas": [
            "Show who archived the document and the reason, so the reviewer can decide whether to restore.",
            "Allow searching the panel by document name or transaction address for tenants with a lot of archived documents.",
            "Add a 'Restored by' note to the document's history so the audit trail is complete.",
        ],
    },
    {
        "no": "27.14",
        "category": "Daily Agent / Elf Workflow",
        "feature": "All Documents — Bulk actions on the Missing tab",
        "route": "/documents (Missing tab)",
        "how_to_test": [
            "Open the Missing tab. Each row should have a small checkbox at the left edge.",
            "Tick the checkboxes on two or three rows. A bulk-action bar should appear above the list showing 'N items selected'.",
            "From the bulk-action bar click Mark N/A. Confirm all selected rows clear at once.",
            "Select two or three more rows and click Request. Confirm a request email window opens for the first selected row (the system asks one recipient at a time — sending one email to several different recipients at once is not yet supported).",
            "Select rows and click Upload / Assign. Confirm the Upload window opens with the first selected row's transaction and document type already filled in.",
            "Click Clear on the bulk-action bar. Confirm the bar disappears and no rows stay selected.",
            "Confirm the bulk-action bar is only shown when at least one row is selected — no checked rows, no bar.",
        ],
        "expected_result": [
            "Multi-select is only offered on the Missing tab — other tabs do not show row checkboxes.",
            "Mark N/A runs on every selected row at once.",
            "Request and Upload / Assign use the first selected row to pre-fill their modal — they do not yet send to several recipients at once.",
            "There is no bulk Reassign on the Missing tab — there's no existing document to move yet.",
        ],
        "future_ideas": [
            "Allow Request to send to several different recipients in one pass.",
            "Add a Select-all checkbox at the top of the list.",
            "Add a 'Select rows by transaction' shortcut so the user can clear an entire deal in two clicks.",
            "Add bulk Reassign on the All Docs and Pending Review tabs once that surface is ready.",
        ],
    },
    {
        "no": "27.15",
        "category": "Daily Agent / Elf Workflow",
        "feature": "Client / FSBO Documents portal — view and flag a document for deletion",
        "route": "/client/documents (Client) or /fsbo/documents (FSBO Customer)",
        "how_to_test": [
            "Sign in as a Client (a buyer or seller invited to a transaction) and open Documents from the sidebar. Confirm a real list of documents shared with you appears (not a stub or count-only summary).",
            "Sign in as an FSBO Customer and open Documents from the sidebar. Confirm the same kind of real list appears.",
            "Confirm each row shows the document name, the upload date, and the document type. If a document is already flagged, a small 'Flagged' badge appears next to its name.",
            "On a row that is not yet flagged, click the Flag for deletion button on the right edge of the row. Fill in the reason field and submit.",
            "Confirm the row now shows a 'Flagged' badge and the Flag for deletion button is no longer offered for that row.",
            "Sign in as the Agent or Team Lead for that transaction. Confirm the document now appears on the Deletion Queue (test 27.11) and as a 'Review deletion request' item in the AI Priority list.",
            "After the agent approves or rejects, sign back in as the original requester. Confirm a notification appears in the bell and an email is in your inbox with the decision and any reviewer note.",
        ],
        "expected_result": [
            "Client and FSBO users see a real document list, not a placeholder.",
            "Anyone outside the agent team can flag a document for deletion, and the agent always hears about it through the queue.",
            "Once flagged, the row shows a Flagged badge so the requester does not flag the same document twice.",
            "The requester always hears back about the decision — through both the in-app bell and email.",
        ],
        "future_ideas": [
            "Add an inline preview of each document so the requester can re-read it before flagging.",
            "Show which transaction each document belongs to (currently only the date and type are shown).",
            "Allow the requester to attach a short note when their reason needs more than one line.",
            "Show the same list to Vendors on the vendor portal once that surface is ready.",
        ],
    },
    {
        "no": 28,
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
        "no": 29,
        "category": "Daily Agent / Elf Workflow",
        "feature": "Settings page — overview and layout",
        "route": "/settings",
        "how_to_test": [
            "Open /settings and confirm it is a single scrolling page divided into seven sections: Company, Email Integrations, E-Signature, Branding, AI Configuration, Task Templates, Help & Tour.",
            "Confirm four Snapshot tiles at the top (Inbox, E-Sign, Credits, Templates) and a 'Sections' nav on the side.",
            "Click each Snapshot tile in turn — the page should jump to the matching section.",
            "Click each item in the Sections nav and confirm the page jumps to that section.",
            "Scroll slowly and confirm the Sections nav highlight follows the active section.",
            "Confirm the Inbox tile's 'connected/total' number matches what the Email Integrations section shows below.",
            "Each individual section is tested in 29.1–29.6.",
        ],
        "expected_result": [
            "Snapshot tiles and the Sections nav both jump to the right section.",
            "Every signed-in role can open /settings (individual sections have their own gating).",
        ],
        "future_ideas": [
            "Role-gate Branding, Task Templates, and AI Configuration so non-admin users cannot see them.",
            "Persist the last-visited section so that returning to /settings scrolls to where the user left off.",
            "Add a 'What's new in Settings' callout when major sections change between releases.",
        ],
    },
    {
        "no": "29.1",
        "category": "Daily Agent / Elf Workflow",
        "feature": "Settings — Email Integrations (Gmail and Outlook)",
        "route": "/settings (Email Integrations section)",
        "how_to_test": [
            "Open Settings and scroll to Email Integrations. Confirm a Gmail row and an Outlook row are visible (iCloud is intentionally not shown yet).",
            "Click Connect on the Gmail row. Complete sign-in in the Google popup that opens. After approval the row should switch to Connected with your email and the date.",
            "Repeat on the Outlook row using a Microsoft 365 account.",
            "Cancel the popup mid-way and confirm the row stays in the 'Connect' state without an error.",
            "Click Disconnect on a connected row. Confirm a warning appears explaining inbound sync and AI email automation will stop.",
            "Cancel the warning — the row should remain connected. Confirm it — the row should return to Connect.",
            "Click Refresh on the section to re-fetch the integration list.",
        ],
        "expected_result": [
            "Both providers connect through their official sign-in popup — no password is typed into Velvet Elves.",
            "Disconnect always asks for confirmation first.",
            "At least one provider must be connected for AI Email Review (29.7+) to send replies.",
        ],
        "future_ideas": [
            "Show a 'Last synced' timestamp and a manual 'Sync now' button per provider.",
            "Re-enable the iCloud row once the Apple app-specific-password flow is reviewed.",
            "Show a small indicator on the row when the linked mailbox has unread AI drafts waiting in /ai-emails.",
            "Detect popup-blocked browsers and offer a redirect-based fallback path.",
        ],
    },
    {
        "no": "29.2",
        "category": "Daily Agent / Elf Workflow",
        "feature": "Settings — E-Signature (DocuSign)",
        "route": "/settings (E-Signature section)",
        "how_to_test": [
            "Open Settings → E-Signature.",
            "If DocuSign is not yet connected, click Connect. Complete the 3-step wizard (Intro → DocuSign popup → Done).",
            "After connecting, confirm the section shows your DocuSign account email and the date you connected.",
            "Click Disconnect, read the warning that future Send-for-Signature attempts will fail, and confirm.",
        ],
        "expected_result": [
            "Connect and Disconnect both work without leaving the Settings page.",
            "Once connected, the same account is also shown inside the Send for Signature modal on /documents.",
        ],
        "future_ideas": [
            "Add support for additional providers (DotLoop, Authentisign, Adobe Sign) alongside DocuSign in this section.",
            "Show the monthly envelope count remaining so users do not hit their DocuSign quota by surprise.",
        ],
    },
    {
        "no": "29.3",
        "category": "Daily Agent / Elf Workflow",
        "feature": "Settings — Branding (placeholder — not wired yet)",
        "route": "/settings (Branding section)",
        "how_to_test": [
            "Open Settings → Branding. Confirm a logo upload, a primary colour field, and a display name field are visible.",
            "Try changing each field and click Save branding.",
            "Refresh the page — the fields should reset to the defaults.",
        ],
        "expected_result": [
            "The Branding section is currently a placeholder; nothing persists after refresh.",
            "Please flag clearly if any client expects this section to be live so we can prioritise wiring it up.",
        ],
        "future_ideas": [
            "Wire all three Branding fields to the tenant settings backend.",
            "Show a live preview of the sidebar and a sample email so the user can see the changes before saving.",
            "Add a tenant-wide 'Reset to Velvet Elves defaults' button.",
        ],
    },
    {
        "no": "29.4",
        "category": "Daily Agent / Elf Workflow",
        "feature": "Settings — AI Configuration (placeholder toggles)",
        "route": "/settings (AI Configuration section)",
        "how_to_test": [
            "Open Settings → AI Configuration.",
            "Confirm an 'AI Credits' line and three toggles: Auto-parse uploaded documents, Task recommendations, and Smart email drafts.",
            "Flip each toggle and refresh — the toggle should reset (settings do not persist yet).",
            "Click Upgrade plan and confirm nothing happens (placeholder button).",
        ],
        "expected_result": [
            "Toggles flip on screen but do not persist on refresh.",
            "The AI Credits numbers shown today are placeholders and do not reflect real usage — please flag if a stakeholder expects them to.",
        ],
        "future_ideas": [
            "Wire each toggle to the tenant AI settings (tone, disclaimer, escalation hours, auto-send threshold) so admins can actually configure AI behaviour.",
            "Replace the placeholder credit count with a real meter pulled from the AI usage backend.",
            "Add a 'Smart email drafts' explainer link that opens a preview of the AI Email Review queue.",
        ],
    },
    {
        "no": "29.5",
        "category": "Daily Agent / Elf Workflow",
        "feature": "Settings — Task Templates (placeholder list)",
        "route": "/settings (Task Templates section)",
        "how_to_test": [
            "Open Settings → Task Templates. Confirm a placeholder list of five templates: Buyer Standard, Seller Standard, Dual Agency, Lease, and Commercial.",
            "Click Edit on any row — nothing should happen (placeholder).",
            "Click Import in the section header — nothing should happen (placeholder).",
        ],
        "expected_result": [
            "Neither Edit nor Import is wired on this section.",
            "Real template management lives at /admin/task-templates (features 30 and 31).",
        ],
        "future_ideas": [
            "Replace this placeholder with a live mini-list pulled from the Task Templates backend.",
            "Or remove this section from Settings and link directly to /admin/task-templates instead.",
        ],
    },
    {
        "no": "29.6",
        "category": "Daily Agent / Elf Workflow",
        "feature": "Settings — Help & Tour (replay the product tour)",
        "route": "/settings (Help & Tour section)",
        "how_to_test": [
            "Open Settings → Help & Tour and click Start tour.",
            "Confirm the product tour starts immediately for whatever role you are signed in as.",
            "Try it for each role (Agent, Transaction Coordinator, Team Lead, Admin, Attorney, Client, FSBO Customer, Vendor) — the tour content should match the role (see feature 13 for what is expected).",
        ],
        "expected_result": [
            "Start tour always launches the product tour for the signed-in role, even if you have already finished it.",
            "This is the only fully-wired control among AI Configuration, Branding, Templates, and Help — please test it for every role.",
        ],
        "future_ideas": [
            "Add a 'What's new in this release' card next to Replay tour so users can re-run a tour focused on recent changes only.",
            "Add a per-feature mini-tour launcher (e.g. 'Replay Documents tour only').",
            "Show a small completion timestamp ('Last completed Apr 28, 2026') so users know whether they've already seen the latest version.",
        ],
    },
    {
        "no": "29.7",
        "category": "Daily Agent / Elf Workflow",
        "feature": "AI Email Review — overview, list, and filter tabs",
        "route": "/ai-emails",
        "how_to_test": [
            "Open Intelligence → AI Email Review from the sidebar (Agent, Transaction Coordinator, Team Lead, and Admin only; Attorney and external roles do not see this entry).",
            "Confirm the filter tabs: All, Needs Review, Ready to Send, Low Confidence, Escalated — each with a count.",
            "Click each tab in turn and confirm the list narrows to that subset.",
            "Click Refresh and confirm the list reloads.",
            "Leave the page open for at least 60 seconds. The list should silently re-fetch every minute, and any new draft should appear without a manual refresh.",
            "Open the top-bar bell on another page and confirm the unread count matches the All tab here.",
            "Force an empty state by switching to a tab with no matches and confirm a clear empty message appears.",
        ],
        "expected_result": [
            "The list only contains drafts your role is allowed to act on.",
            "Auto-refresh runs every 60 seconds; the list also refreshes immediately after Approve / Edit / Discard / Regenerate.",
            "Empty and error states show a clear next step.",
        ],
        "future_ideas": [
            "Add an inline search box and sort control inside the list.",
            "Add per-row checkboxes plus bulk Approve / Discard so a reviewer can clear a backlog quickly.",
            "Wire the deep-link /ai-emails/:logId so notifications open the exact draft in question.",
            "Stream live updates so the list does not have to poll every minute.",
        ],
    },
    {
        "no": "29.8",
        "category": "Daily Agent / Elf Workflow",
        "feature": "AI Email Review — what each draft row shows",
        "route": "/ai-emails (list of drafts)",
        "how_to_test": [
            "Look at any draft row. Confirm it shows: the subject, the recipient(s), the kind of email (Factual question / Document request / Vendor reply / Uncertain / Other), a confidence percent, an Escalated marker if the draft is past its deadline, and a 'how long ago' timestamp.",
            "Click a row and confirm the detail pane on the right loads the full draft (see 29.9).",
            "Note: there is no per-row search, sort, or bulk action yet — the only filtering surface is the tab row at the top. Please flag if this is missing for the way you want to work.",
        ],
        "expected_result": [
            "Every row tells you at a glance how confident the AI is, who the email is to, and whether it is overdue.",
            "Selection survives the 60-second auto-refresh as long as the draft is still in the same filter.",
        ],
        "future_ideas": [
            "Show the transaction address on each row so a reviewer can scan deals without opening each draft.",
            "Show an attachment indicator (planned alongside attachment support).",
            "Offer a compact / comfortable density toggle for high-volume reviewers.",
        ],
    },
    {
        "no": "29.9",
        "category": "Daily Agent / Elf Workflow",
        "feature": "AI Email Review — what the draft detail shows",
        "route": "/ai-emails (open any draft)",
        "how_to_test": [
            "Open any draft and confirm the top of the detail shows the email kind, the confidence percent, and an Escalated marker if applicable. The subject and the To / Cc lines are also visible (by default the file owner is automatically CC'd).",
            "Read the AI-drafted reply. Any phrases the AI is unsure about should be highlighted in the body, and if it made any explicit assumptions, those are listed below the body as 'Flagged assumptions'.",
            "On the right side, confirm an 'AI Verified From' card lists every piece of source data the AI used (address, closing date, status, document names, etc.). If the list is empty, a warning explains that no source data was cited and that the agent should verify each fact manually.",
            "Below it, confirm an 'Original Inbound' card shows the email that triggered this draft (sender, time, subject, body). If the original can't be loaded, the card says so cleanly.",
        ],
        "expected_result": [
            "The confidence percent, kind, and escalation status match whatever was shown on the list row.",
            "Highlighted phrases in the body match the explicit 'Flagged assumptions' list.",
            "AI Verified From only shows facts the AI actually used — it does not guess.",
            "Original Inbound shows the email that triggered this reply, not the entire thread (full-thread view is a future improvement).",
        ],
        "future_ideas": [
            "Show the entire thread, not just the immediate inbound, so a reviewer can see prior context.",
            "Make each AI Verified From row clickable so it deep-links to the source field on the transaction record.",
            "Add an inline 'Flag this fact as wrong' button that pushes a correction back into the AI's training data.",
        ],
    },
    {
        "no": "29.10",
        "category": "Daily Agent / Elf Workflow",
        "feature": "AI Email Review — Approve & Send, Edit & Send, Regenerate, Discard",
        "route": "/ai-emails (action buttons on the open draft)",
        "how_to_test": [
            "Open a draft and click Approve & Send. Confirm the email is sent and a toast confirms.",
            "Open another draft and click Edit. The subject and body should become editable. Make a change and click Send Edit — confirm the edited version is sent.",
            "Click Regenerate on a draft. Confirm the AI redraws a fresh reply from the original inbound email.",
            "Click Discard. Confirm a warning explains the draft will be removed but the original inbound message stays in the communication log. Confirm Discard removes the draft.",
            "Disconnect your email provider in Settings, then click Approve & Send on a draft. Confirm a clear error explains that no email provider is connected.",
            "Confirm the actions that are NOT here yet: no Reassign, no 'Mark Reviewed', no attachment uploader, no scheduled-send.",
        ],
        "expected_result": [
            "Approve, Edit, Regenerate, and Discard all complete with a toast and the list refreshes.",
            "Editing a draft also clears its flagged assumptions, since the human reviewer rewrote the content.",
            "Discard preserves the original inbound message in the communication log — only the draft disappears.",
            "If your role is not allowed to act, an error toast explains it on click rather than the button being hidden.",
        ],
        "future_ideas": [
            "Add a Reassign button so a Team Lead can hand a draft to a colleague without opening it.",
            "Add a Mark Reviewed (no-send) status for drafts the human read but does not want to send.",
            "Add support for attachments when replying so contracts and addenda can ride out with the AI reply.",
            "Add a per-tenant 'Auto-send when confidence is over X%' threshold (backend already supports it; no UI yet).",
        ],
    },
    {
        "no": "29.11",
        "category": "Daily Agent / Elf Workflow",
        "feature": "Vendor directory",
        "route": "/vendors",
        "how_to_test": [
            "Open the sidebar and click Vendors, or go to /vendors directly.",
            "Confirm a card for every vendor company shows the name, category, contact email, and phone.",
            "Use the search box to find a vendor by company name, category, or email.",
            "Use the category dropdown and the 'Preferred only' toggle to narrow the list.",
            "Click New vendor and add a vendor company. Confirm it appears in the directory.",
            "Click a vendor card to open the vendor detail page.",
        ],
        "expected_result": [
            "Every vendor stored for your brokerage shows up in the directory and stays reachable from any transaction.",
            "Search, category, and preferred filters all narrow the visible list in real time.",
            "New vendors created here can be assigned to transactions afterwards.",
        ],
        "future_ideas": [
            "Show the number of open transactions each vendor is currently assigned to.",
            "Allow tagging vendors with custom labels (for example 'fast turnaround', 'cash only').",
        ],
    },
    {
        "no": "29.12",
        "category": "Daily Agent / Elf Workflow",
        "feature": "Vendor detail page (contacts, portfolio, background refresh)",
        "route": "/vendors/{vendorId}",
        "how_to_test": [
            "Open a vendor from the directory.",
            "Confirm the page shows the company name, category, address, phone, email, and preferred status.",
            "Under Contacts, confirm each person on file shows a name, email, and phone, with the primary contact clearly labelled.",
            "Click the Email button on a contact and confirm the Send Vendor Request modal opens with that contact pre-filled.",
            "Hover the Call button — until SMS / voice integration is enabled it should show a 'Coming soon' note.",
            "Under Portfolio, confirm a list of transactions where this vendor is on the team.",
            "Click Refresh info — the Background refresh drawer opens (see entry 29.16).",
            "Click Add colleague (public link) — confirm a one-time link is created and copied to the clipboard.",
        ],
        "expected_result": [
            "The page summarises everything you need to know about the vendor in one screen.",
            "Email opens the request flow with the right contact selected.",
            "Add colleague creates a public link that the vendor can use to add a teammate without logging in.",
            "Refresh info opens the suggestions drawer; nothing applies without an explicit click.",
        ],
        "future_ideas": [
            "Show the latest vendor reply per transaction directly on the portfolio list.",
            "Allow the agent to set vendor-specific reply expectations (for example 'always reply within 24h').",
        ],
    },
    {
        "no": "29.13",
        "category": "Daily Agent / Elf Workflow",
        "feature": "Send Vendor Request (template-based email)",
        "route": "Email button on a vendor contact card, or from a task that has a vendor assignment",
        "how_to_test": [
            "Open a vendor detail page and click Email on one of the contacts.",
            "Pick a template from the list (for example 'Inspection — Schedule Visit'). Confirm the right pane previews the subject and body with the transaction address, task name, and primary contact name filled in.",
            "Confirm the body ends with the reply footer 'Reply with: Scheduled: YYYY-MM-DD' (or the equivalent footer for the chosen template).",
            "Edit the subject or body inline if you want.",
            "Click Send request.",
            "Open the Communications panel for the same transaction and confirm a new outbound row appears with the right vendor and timestamp.",
            "Check the vendor's inbox in another window — the email should be there.",
        ],
        "expected_result": [
            "The request is sent through the agent's connected Gmail or Outlook (not from a Velvet Elves address).",
            "Both the email and a record of it appear in the transaction's communication log.",
            "If no email provider is connected, the modal explains how to fix it and does not silently fail.",
        ],
        "future_ideas": [
            "Allow attaching the most recent contract or inspection report directly from the modal.",
            "Schedule the send for later (overnight or a specific weekday).",
        ],
    },
    {
        "no": "29.14",
        "category": "Daily Agent / Elf Workflow",
        "feature": "Vendor proposals queue",
        "route": "/vendor-proposals (sidebar → Intelligence → Vendor Proposals)",
        "how_to_test": [
            "Open /vendor-proposals from the sidebar.",
            "Confirm three tabs: 'Awaiting decision', 'Awaiting vendor', and 'All open'.",
            "Each proposal card should show the task name, the vendor company, the original task date, and the date the vendor is proposing.",
            "Click Accept & update task on a pending proposal — confirm a toast reports the task date was updated, and check the matching transaction's task tab to verify the new date.",
            "Click Ask vendor to clarify on a vague proposal (one with no clear date) — confirm the proposal moves to the 'Awaiting vendor' tab.",
            "Click Reject on another proposal — confirm a toast reports the task date is unchanged.",
        ],
        "expected_result": [
            "Every vendor reply that proposes a new date lands here for the agent to approve.",
            "Accept is the only action that changes a task's due date — nothing happens automatically.",
            "Decisions are recorded in the audit log for compliance.",
        ],
        "future_ideas": [
            "Show the original vendor email inline so the agent does not have to bounce between this page and /ai-emails.",
            "Suggest an alternative date when Reject is clicked, so the agent can immediately reply with one.",
        ],
    },
    {
        "no": "29.15",
        "category": "Daily Agent / Elf Workflow",
        "feature": "Add a vendor colleague (public link)",
        "route": "'Add colleague (public link)' button on a vendor contact card; the public page is /v/{token}",
        "how_to_test": [
            "On a vendor detail page, click Add colleague (public link). Confirm a one-time link is copied to your clipboard.",
            "Open the link in a private / incognito browser window. The page should show only your brokerage name and the vendor company name (no transaction details).",
            "Submit the form with first name, last name, email, optional phone, and optional title.",
            "Confirm the success screen reads 'You're on the thread.'",
            "Back in the authenticated app, reload the vendor detail page and confirm the new contact appears in the Contacts list (not marked primary).",
            "Try opening the same link again — the page should report the link is no longer valid (single-use).",
        ],
        "expected_result": [
            "Vendors can attach a colleague without creating an account.",
            "The public page never leaks any transaction information.",
            "Each link can be used exactly once and expires after the default window (7 days).",
        ],
        "future_ideas": [
            "Allow the vendor to set their own preferred contact channel (email or SMS) right on the public form.",
            "Let the agent customise the welcome message that appears on the public page.",
        ],
    },
    {
        "no": "29.16",
        "category": "Daily Agent / Elf Workflow",
        "feature": "Vendor background refresh (suggested updates)",
        "route": "'Refresh info' button on a vendor detail page",
        "how_to_test": [
            "Open a vendor detail page that already has one or more contacts and click Refresh info.",
            "In the drawer, click Run refresh. Confirm suggestions appear as 'Current value' vs. 'Suggested value' cards with a confidence score and source label.",
            "Tick one or two suggestions and click Apply selected.",
            "Confirm a toast reports the vendor record was updated, and the At-a-glance section on the vendor detail page reflects the new values.",
            "Reopen the drawer and confirm the suggestions you accepted are gone but the others remain.",
        ],
        "expected_result": [
            "Suggestions are based on existing tenant data (other transactions, other contacts) — no public web search.",
            "Nothing changes on the vendor record without an explicit click.",
            "Every accepted change is recorded in the audit log per field.",
        ],
        "future_ideas": [
            "Pull from approved public sources (state licensing boards, business directories) once that is reviewed.",
            "Run the refresh on a schedule for preferred vendors so suggestions are always fresh.",
        ],
    },

    # ============================================================
    # SECTION 4 — ADMIN / TEAM LEAD EXTRAS
    # ============================================================
    {
        "no": 30,
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
        "no": 31,
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
        "no": 32,
        "category": "Admin / Team Lead Extras",
        "feature": "Admin user detail",
        "route": "/admin/users/<userId> (reachable from /admin/users and /team)",
        "how_to_test": [
            "From /admin/users, click a member's name or 'View profile'. The detail page should open.",
            "From /team, click any member tile in 'Recently added members' and confirm it opens the same page.",
            "Confirm the page shows the member's name, email, phone, joined date, last sign-in, role, and active/inactive status. The workspace owner is clearly marked.",
            "Paste /admin/users/some-fake-id directly in the browser. Confirm a 'Failed to load user' error card appears (not a white screen).",
        ],
        "expected_result": [
            "A valid user id renders the profile without errors.",
            "An invalid or deleted user id shows a clean error state with a way to navigate back.",
        ],
        "future_ideas": [
            "Add an audit trail showing the user's recent actions (logins, role changes, transactions worked).",
            "Add an inline Edit form so an Admin can update name, phone, or role from this page.",
            "Show recent transactions assigned to this user so a Team Lead has full context.",
        ],
    },
    {
        "no": "32.1",
        "category": "Admin / Team Lead Extras",
        "feature": "Team Overview page",
        "route": "/team (Team Lead and Admin only)",
        "how_to_test": [
            "Sign in as Team Lead or Admin and open Team from the sidebar.",
            "Try the same as Agent, Transaction Coordinator, Attorney, Client, FSBO, or Vendor — the page should redirect to Unauthorized.",
            "Confirm the four overview numbers at the top: Active Members, Pending Invites, Seats Used (if your plan has a seat limit), and Recently Active.",
            "Confirm the 'Recently added members' list shows up to 12 members with their role; the workspace owner is clearly marked.",
            "Click any member to open their detail page (feature 32).",
            "Confirm the Role Coverage area shows how many people you have in each role (Admin, Team Lead, Transaction Coordinator, Agent, Attorney).",
            "Confirm the side panels show Pending Invites (with time left), Last Seen (recent sign-ins), and Seat Usage (if your plan has a seat limit).",
            "Click the Team Members and Task Templates quick-link cards at the bottom and confirm they open the matching admin pages.",
            "Click Manage team in the header and confirm it opens /admin/users (feature 32.2).",
        ],
        "expected_result": [
            "Only Team Lead and Admin can reach the page.",
            "Every panel reflects real data for your workspace.",
            "Quick links navigate to the right admin page.",
        ],
        "future_ideas": [
            "Let the user filter Team Members by clicking a role on the Role Coverage row.",
            "Show a 7-day activity sparkline on the top numbers.",
            "Allow pinning a favourite member for quick contact from the side rail.",
        ],
    },
    {
        "no": "32.2",
        "category": "Admin / Team Lead Extras",
        "feature": "Team Members admin — Active members tab",
        "route": "/admin/users (Team Lead and Admin only)",
        "how_to_test": [
            "Open /admin/users from the Team Overview page (Manage team) or directly.",
            "Sign in as Agent or another lower role and confirm the URL redirects to Unauthorized.",
            "Confirm two tabs: 'Active members' and 'Pending invitations'.",
            "On the Active members tab, type in the search box and confirm the list filters by name and email as you type.",
            "Open the role dropdown, pick a role, and confirm only members with that role remain. Combine search and role filter and confirm both apply.",
            "Expand a member card. Confirm Email, Phone, Joined date, and Last sign-in are shown, with a 'View full profile' button.",
            "If you are the workspace owner, confirm a Transfer ownership button appears in the expanded card (see 32.5).",
            "If you are Admin, confirm a Deactivate button appears in the expanded card for every member except yourself and the owner (see 32.6).",
            "Apply a search term with no matches and confirm a clear 'no members match' message appears.",
        ],
        "expected_result": [
            "Search and role filter narrow the list in real time.",
            "Transfer ownership and Deactivate buttons only appear for users who have permission to use them, and never on your own card.",
        ],
        "future_ideas": [
            "Show a 'last active' time directly on the collapsed card.",
            "Add bulk selection so an Admin can deactivate or change role for multiple members at once.",
            "Add an inline 'Resend welcome email' action for members who never signed in.",
        ],
    },
    {
        "no": "32.3",
        "category": "Admin / Team Lead Extras",
        "feature": "Team Members admin — Pending invitations tab",
        "route": "/admin/users → 'Pending invitations' tab",
        "how_to_test": [
            "Switch to the Pending invitations tab on /admin/users.",
            "If there are pending invites, confirm each row shows the invited email, the invited role, and how much time is left before the invite expires.",
            "Click Copy link on a row and confirm the invite URL is copied to your clipboard.",
            "In the row's three-dot menu, try Resend email, Extend by 72h, and Revoke invitation. Each should show a confirming toast and update the row.",
            "If there are no pending invites, confirm a clear empty state pointing at the Invite teammate button.",
            "Block your browser clipboard and click Copy link — confirm a clear error appears rather than a silent failure.",
        ],
        "expected_result": [
            "All four row actions (Copy link, Resend, Extend, Revoke) work on pending invitations.",
            "Accepted invitations do not appear on this tab.",
            "Revoking an invitation removes the row and prevents the invitee from accepting.",
        ],
        "future_ideas": [
            "Add a Bulk revoke expired button so cleanup is one click instead of many.",
            "Show who originally sent each invitation so a Team Lead can see which Admin invited a particular email.",
            "Show a preview of the full invite URL before copying.",
        ],
    },
    {
        "no": "32.4",
        "category": "Admin / Team Lead Extras",
        "feature": "Invite teammate modal",
        "route": "/admin/users → 'Invite teammate' button",
        "how_to_test": [
            "Click Invite teammate on /admin/users.",
            "Confirm two required fields: Email address and Role. A short hint under the dropdown explains what each role can do.",
            "Sign in as different inviter roles (Agent, Team Lead, Admin) and confirm the dropdown only offers roles you are allowed to grant — for example only Admins can invite new Admins.",
            "Try to send with an empty email and confirm it is blocked.",
            "Try to invite an email that already belongs to a member and confirm an inline error explains the email is already in use.",
            "If your plan has a seat cap, try inviting beyond the cap and confirm a seat-limit error appears.",
            "Send a valid invitation and confirm a success toast appears, the modal closes, and the new row appears on the Pending invitations tab.",
        ],
        "expected_result": [
            "Roles you cannot grant are not offered in the dropdown.",
            "Every failure mode shows a clear inline error rather than breaking the modal.",
            "A successful invite appears in the Pending invitations list immediately.",
        ],
        "future_ideas": [
            "Allow inviting multiple emails at once (comma-separated) so an admin can bulk-onboard a team.",
            "Show a 'view what the invitee will see' preview link before sending.",
            "Let the admin attach a team or a transaction at invite time (planned for Phase 5).",
        ],
    },
    {
        "no": "32.5",
        "category": "Admin / Team Lead Extras",
        "feature": "Transfer workspace ownership",
        "route": "/admin/users → member three-dot menu (workspace owner only)",
        "how_to_test": [
            "Sign in as the workspace owner and confirm you are clearly marked as the owner on /admin/users.",
            "Open the three-dot menu (or expand the card) on a different member and confirm a Transfer ownership option is offered. It should not appear on your own row or on a member who is already the owner.",
            "Click Transfer ownership. Confirm the warning dialog explains: the target will be promoted to Admin if they are not already one; you will stay as Admin but lose owner-only abilities (schedule deletion, transfer ownership); and the action is logged.",
            "Confirm the transfer. After success, the owner mark moves from your row to the new owner's row.",
            "Refresh the page and confirm the new ownership state persists.",
            "Sign in as a regular Admin (not the owner) and confirm Transfer ownership is hidden from every member's menu.",
        ],
        "expected_result": [
            "Only the current owner sees the Transfer ownership control.",
            "The confirmation dialog clearly describes the side effects before you commit.",
            "After transfer, the previous owner can no longer schedule deletion or transfer ownership — those controls disappear from Settings.",
        ],
        "future_ideas": [
            "Send an automatic email to the new owner immediately so they know responsibility has moved.",
            "Add an undo window (for example 30 minutes) on a recently-transferred ownership.",
            "Show the full audit trail of past ownership transfers on the Team Overview page.",
        ],
    },
    {
        "no": "32.6",
        "category": "Admin / Team Lead Extras",
        "feature": "Deactivate a member",
        "route": "/admin/users → member three-dot menu (Admin only)",
        "how_to_test": [
            "Sign in as an Admin who is not the target. Open another member's three-dot menu (or expand their card) and confirm a Deactivate option is offered.",
            "Confirm Deactivate is hidden on the workspace owner's row and on your own row.",
            "Click Deactivate. A confirmation dialog should explain the member will no longer be able to sign in and can be re-activated later.",
            "Cancel and confirm the member is still listed. Try again and confirm — the member disappears from Active members.",
            "Switch to Pending invitations and confirm any invitations the deactivated user created are still listed there.",
        ],
        "expected_result": [
            "Deactivation requires confirmation and updates the list immediately.",
            "The owner cannot be deactivated — the option is hidden on their row.",
            "You cannot deactivate yourself — the option is hidden on your own row.",
        ],
        "future_ideas": [
            "Add a paired Re-activate control that surfaces deactivated members in a separate sub-list.",
            "Capture a deactivation reason at confirmation time so the audit log records why.",
            "Auto-revoke any active browser sessions for the deactivated member.",
        ],
    },
    {
        "no": "32.7",
        "category": "Admin / Team Lead Extras",
        "feature": "Settings — Company Details (organization name)",
        "route": "/settings (Company section, at the top of the page)",
        "how_to_test": [
            "As an Admin, open /settings and confirm the Organization Name field is editable with a Save button.",
            "Sign in as any non-Admin (Team Lead, Agent, Transaction Coordinator, Attorney, Client, FSBO Customer, Vendor) and confirm the field is read-only with a note that only an Admin can change it.",
            "As an Admin, type a new name and click Save. Confirm the change is persisted.",
            "Sign in as another member of the same workspace and confirm they see the new name without needing to refresh again.",
            "As an Admin, leave the field empty and click Save — confirm the page shows a clear error rather than saving an empty name.",
        ],
        "expected_result": [
            "Admins can change the organization name; everyone else sees a read-only field with a clear explanation.",
            "The new name shows up for every member of the brokerage on the next page load.",
            "Errors appear inline; the page never breaks silently.",
        ],
        "future_ideas": [
            "Show a small preview of how the organization name will appear in the sidebar, the invitation email, and outbound transaction emails before saving.",
            "Add a 'Tenant slug' field so admins can claim a unique subdomain (for example acme.velvetelves.com).",
            "Show the workspace owner's name and email on this card so members know who to ask for changes.",
        ],
    },
    {
        "no": "32.8",
        "category": "Admin / Team Lead Extras",
        "feature": "Settings — Danger Zone (schedule / cancel deletion)",
        "route": "/settings (Danger Zone section at the bottom — workspace owner only)",
        "how_to_test": [
            "Sign in as the workspace owner and scroll to the bottom of /settings. Confirm a Danger Zone section is visible.",
            "Sign in as any other role on the same workspace and confirm the section is not visible at all.",
            "As the owner, click Delete organization. Confirm the page asks you to type the workspace name exactly before Schedule deletion becomes available.",
            "Schedule deletion and confirm a clear message reports the exact date and time it will run, plus a note that audit logs and a full snapshot are archived under the 2-year retention policy.",
            "Click Cancel deletion and confirm the workspace returns to normal.",
            "If your workspace is on legal hold, confirm the Delete button is disabled with a clear explanation pointing the owner at platform support.",
        ],
        "expected_result": [
            "Only the workspace owner can see and use the Danger Zone.",
            "Scheduling deletion requires typing the workspace name exactly, and the action can be reversed during the grace period.",
            "Members can still sign in while deletion is scheduled, so the owner can cancel it.",
            "Legal hold blocks the action with a clear plain-language reason.",
        ],
        "future_ideas": [
            "Show a top-of-page banner with the deletion date and days remaining while deletion is scheduled.",
            "Send a daily reminder email to the owner while deletion is scheduled.",
            "Let the owner customise the grace-period length (default is 30 days).",
            "Add a 'Download a full export before I leave' button next to the schedule-deletion CTA.",
        ],
    },
    {
        "no": "32.9",
        "category": "Admin / Team Lead Extras",
        "feature": "Platform Admin — Tenants list (internal Velvet Elves staff only)",
        "route": "/platform/tenants (platform admins only)",
        "how_to_test": [
            "Sign in as a platform admin and open /platform/tenants.",
            "Sign in as any non-platform user and try /platform/tenants directly — confirm you get a 404 (not a 403), so the route's existence is not leaked.",
            "Use the filter dropdown (All / Active / Suspended / On legal hold) and confirm the table narrows correctly.",
            "Each tenant row should show the tenant name, slug, current status, plan, and an Actions menu.",
            "Click Details on a row and confirm the tenant detail page opens (feature 32.10).",
            "Click Suspend on an active tenant. Confirm a warning explains members will not be able to sign in and that you can reactivate later. Confirm and check the row updates.",
            "Confirm the Suspend button is disabled for a tenant on legal hold.",
            "Click Reactivate on a suspended tenant and confirm it returns to Active.",
        ],
        "expected_result": [
            "Non-platform users get a 404 — the route's existence is not leaked.",
            "Filters narrow the list correctly.",
            "Suspend / Reactivate updates the row immediately and is recorded in the platform audit log.",
        ],
        "future_ideas": [
            "Add a search box that matches name / slug / owner email.",
            "Add a Schedule deletion action on the row alongside Suspend (currently only available inside the tenant's own Settings → Danger Zone).",
            "Show owner email and member count as extra columns.",
            "Add a 'Force re-verify domain' action for tenants on a custom domain.",
        ],
    },
    {
        "no": "32.10",
        "category": "Admin / Team Lead Extras",
        "feature": "Platform Admin — Tenant detail (internal Velvet Elves staff only)",
        "route": "/platform/tenants/<tenantId> (platform admins only)",
        "how_to_test": [
            "Open a tenant detail by clicking Details on /platform/tenants or by pasting the URL.",
            "Confirm the page shows the tenant name, slug, created date, status (Active, Suspended, Legal hold, or Deletion scheduled), and an All tenants back link.",
            "Confirm the Identity panel lists ID, slug, custom domain (if any), domain verification status and timestamp, owner user id, and the invite base URL.",
            "Confirm the Plan & lifecycle panel lists plan name, seat limit, staff seats used, trial-ends date (if any), scheduled-deletion timestamp (if any), and the legal-hold reason (if any).",
            "Sign in as any non-platform user and try the URL directly — confirm you get a 404.",
            "Open the URL with an invalid tenant id and confirm the page shows a clear 'Tenant not found' message with a back link.",
        ],
        "expected_result": [
            "All read-only data renders without errors.",
            "Non-platform users cannot reach this page even with a direct URL.",
            "An invalid or deleted tenant id shows a clean fallback, not a broken page.",
        ],
        "future_ideas": [
            "Add inline edit for tenant name and plan from this detail page.",
            "Show the tenant's recent audit-log events (last 50) directly on this page.",
            "Add a Reset domain verification control for tenants stuck on unverified.",
            "Add a Set / clear legal hold control on this page (currently the field is read-only).",
        ],
    },
    {
        "no": "32.11",
        "category": "Admin / Team Lead Extras",
        "feature": "Vendor email templates (Admin / Team Lead)",
        "route": "/admin/vendor-templates",
        "how_to_test": [
            "Sign in as Admin or Team Lead and open Team → Vendor Templates.",
            "Confirm five system templates ship with every tenant: Inspection — Schedule Visit, Inspection — Reschedule, Appraisal — Schedule Visit, Title — Document Request, Generic Vendor — Scheduling.",
            "Open any system template. Confirm its body includes the required reply footer 'Reply with: Scheduled: YYYY-MM-DD'. Tune the subject or body and click Save.",
            "Click New template, fill in the name, category, subject, and body, then save. Confirm the new template appears with a 'Custom' label.",
            "Sign out and back in as an Agent, then open the Send Vendor Request modal from a vendor's contact card — confirm the new custom template appears in the template picker.",
            "Deactivate a custom template and confirm it no longer appears for agents.",
        ],
        "expected_result": [
            "Every tenant has the five system templates available out of the box.",
            "Admins and Team Leads can add, edit, and deactivate custom templates; agents can use them but cannot edit them.",
            "System template names and categories are locked, but their subject and body can still be tuned.",
        ],
        "future_ideas": [
            "Show a live preview of the rendered email with a sample transaction filled in.",
            "Allow importing and exporting templates as a single file.",
            "Track how often each template is used so the team can retire low-value ones.",
        ],
    },
    {
        "no": "32.12",
        "category": "Admin / Team Lead Extras",
        "feature": "Communication audit page",
        "route": "/admin/communications (the legacy /communications URL still redirects here)",
        "how_to_test": [
            "Sign in as Team Lead or Admin and open Team → Communication audit.",
            "Confirm two tabs: 'Audit log' (visible to Team Lead and Admin) and 'Export requests' (visible to Admin only).",
            "On the Audit log tab, use the filter row: search, channel, direction, date range, AI-only, vendor-only, and party email.",
            "Filter to a single transaction and click Download CSV — a single-transaction CSV downloads.",
            "Open Export requests (Admin only) and submit a multi-transaction export request. Confirm it appears in the list and can be downloaded once it finishes.",
            "Try to open /admin/communications as a regular Agent — the page should redirect to Unauthorized.",
        ],
        "expected_result": [
            "Team Lead and Admin can audit every communication across every transaction.",
            "Single-transaction CSV downloads work in the foreground; multi-transaction exports go through the request queue.",
            "Agents and lower roles cannot reach the page.",
        ],
        "future_ideas": [
            "Add a saved-search feature so admins can revisit the same filter quickly.",
            "Email the requester automatically when a multi-transaction export is ready.",
        ],
    },

    # ============================================================
    # SECTION 5 — ROLE-SPECIFIC WORKSPACES
    # ============================================================
    {
        "no": 33,
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
        "no": 34,
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
        "no": 35,
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
        "no": 36,
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
