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
            ("Check that every field is visible.", [
                "Full name, Organization (optional), Email, Password, Confirm Password, Phone (optional), and the Terms / Privacy checkbox.",
                "A Google sign-up button at the top of the form.",
                "Important: there is no Role dropdown anymore. The first person to register for an organization is automatically the Admin (and the workspace Owner) of that brand-new workspace. To join an existing brokerage, ask one of its admins to send you an invite — typing their name in the Organization field will NOT join you to them; it creates a separate, brand-new workspace.",
            ]),
            ("Try the Organization field.", [
                "Leave it blank and confirm the page accepts the form (the workspace just gets a default name based on your email).",
                "Type a name and confirm the helper text under it explains that this creates a new organization with you as its Admin.",
            ]),
            ("Watch the email-availability check while you type.", [
                "A small spinner appears in the email field while the page checks the address.",
                "Once the check is done, the icon switches to a green check (available) or a red alert (already in use).",
                "If the email is already in use, an inline message under the field offers a 'Sign in instead' link that goes straight to /login.",
            ]),
            ("Watch the password-strength panel while you type.", [
                "Five rules are listed: 8+ characters, an uppercase letter, a lowercase letter, a number, and a symbol. Each rule has a tick that flips from grey to green as it is met.",
                "A coloured strength bar fills as more rules are met (Very weak → Weak → Fair → Good → Strong).",
            ]),
            ("Try invalid inputs and make sure the page stops you.", [
                "An invalid email address (for example 'abc' with no @).",
                "A weak password — confirm the five rule ticks and the strength meter update live.",
                "Mismatched Password and Confirm Password — a live 'Passwords do not match' message appears under Confirm Password; when they match, a green 'Passwords match' message replaces it.",
                "Leaving the Terms / Privacy box unchecked.",
            ]),
            ("Submit a valid registration using a real email you can check.", []),
        ],
        "expected_result": [
            "Each invalid case shows a clear inline message next to the field.",
            "The Create Account button stays disabled while the email is already in use or the passwords do not match.",
            ("After a successful submission, one of two things should happen.", [
                "You are signed in automatically and taken to the /onboarding page. A brand-new workspace is created for you and you are its Admin (and Owner).",
                "Or you are taken to /login with a message asking you to confirm your email first.",
            ]),
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
            ("Open the invite link from your email.", [
                "Either form of the URL works: '/invite/<token>' (clean) or '/invite/accept?token=<token>' (the format used in invitation emails).",
                "While the page checks the token, a centred spinner says 'Verifying your invitation...'.",
            ]),
            ("Confirm the invite page contents once the check is done.", [
                "An orange-circle check icon at the top, with the headline 'You're invited!'.",
                "A line beneath the headline that reads 'Complete your account to join as {Role}', where the role is whatever the admin invited you for — for example Agent, Transaction Coordinator, Team Lead, Attorney, Client, FSBO Customer, or Vendor.",
                "The invited email shown in small grey text just below the role.",
            ]),
            ("Fill in the form.", [
                "Full name (required).",
                "Create password (required — must be at least 8 characters and include at least one number).",
                "Phone (optional).",
            ]),
            ("Try invalid inputs and confirm the page blocks them.", [
                "Empty full name.",
                "A password under 8 characters or with no number — an inline red message appears.",
            ]),
            ("Click 'Join Velvet Elves' to submit.", [
                "The button label changes to a small spinner while it works.",
            ]),
            ("Separately, open a bad invite URL to confirm the error path.", [
                "Paste a fake token (e.g. /invite/some-fake-token) in the browser bar.",
                "Confirm an 'Invalid Invitation' screen appears with a red warning icon, a clear message ('This invitation is invalid or has expired.'), and a 'Go to login' link.",
            ]),
        ],
        "expected_result": [
            "A valid invite signs the new user in, shows a green 'Account created successfully!' toast, and takes them to /onboarding.",
            "On /onboarding, the wizard automatically detects the invitee and skips the 'Company / brokerage' step (see feature 12), showing a read-only 'Joining: {brokerage name}' banner instead.",
            "An invalid or expired token shows the 'Invalid Invitation' screen with a 'Go to login' link rather than a broken page.",
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
        "feature": "Onboarding wizard (rewritten — role-aware flow)",
        "route": "/onboarding",
        "how_to_test": [
            ("How you arrive on this page.", [
                "Brand-new accounts are sent here automatically right after sign-up, after accepting an invite, and on every login until the wizard is finished.",
                "If you sign in with an account that already finished onboarding, the page detects that on its own and forwards you to /dashboard.",
            ]),
            ("Wizard layout.", [
                "Dark left rail with the Velvet Elves logo, a numbered step list, and a short privacy note.",
                "White right panel that holds the active step's content.",
                "Footer with a Back button on the left and a Continue (or 'Skip for now') button on the right. The final step hides the footer.",
                "On a phone-sized screen the rail collapses into a thin orange progress strip across the top.",
            ]),
            ("Founder vs. invitee branch (NEW).", [
                "If you signed up by accepting an invite email (see feature 11), the wizard runs in 'invitee mode'. On Step 2 the 'Company / brokerage' field and the 'Brand logo' drag-drop zone are HIDDEN, and a read-only 'Joining: {brokerage name}' banner takes their place. This prevents an invitee from accidentally renaming or rebranding the workspace they just joined.",
                "If you self-registered on /register, the wizard runs in 'founder mode' and you DO see the Company / brokerage and Brand logo fields on Step 2.",
                "The wizard reads this signal from your account on the server, not from the URL. Re-signing in, or transferring ownership later, does not flip you back into founder mode by accident — see feature 32.5 for the ownership-transfer behaviour.",
            ]),
            ("Step 1 — Welcome.", [
                "Confirm a personal greeting that uses your first name (for example 'Hi Jake, let's set up your workspace').",
                "Read the role-personalised intro line ('we'll personalise the workspace for you as a {your role}').",
                "Internal roles (Agent, Transaction Coordinator, Team Lead, Attorney, Admin) see four value cards: Tell us about you, Connect inbox, E-sign with DocuSign, Land in dashboard.",
                "External roles (Client, FSBO, Vendor) see only two value cards (no inbox or e-sign cards).",
                "Click 'Let's go' to advance.",
            ]),
            ("Step 2 — Your Profile.", [
                "Confirm Full name (pre-filled from your account) and Phone (optional, auto-formats to (555) 123-4567 as you type) appear.",
                "Confirm a Role dropdown is present with every supported role.",
                "Founders only (internal roles, NOT invitees): confirm a 'Company / brokerage' field and a 'Brand logo' drag-drop zone are also present.",
                "Invitees: confirm the read-only 'Joining: {brokerage name}' banner shows the brokerage you accepted the invite for, and that the company / logo fields are NOT shown.",
                "Logo rules (founders only): PNG, JPEG, WEBP, SVG, or GIF, max 2 MB. Upload a wrong type or an oversize file and confirm a clear error toast appears (no silent failure).",
                "Upload a valid logo and confirm the preview appears immediately, plus an Upload/Replace button and a Remove button.",
                "Change the Role dropdown to an external role (e.g. Client). Confirm a hint appears under it ('You'll be updated to this role after this step') and that the email + e-sign steps disappear from the rail. Change it back and confirm those steps come back.",
                "Click Continue. The button shows 'Saving…' while it persists your name, phone, role, and — for founders only — your company and logo.",
            ]),
            ("Step 3 — Email Inbox (internal roles only).", [
                "Confirm two provider cards are visible: Gmail (Google OAuth) and Outlook (Microsoft 365 OAuth).",
                "Click Gmail. A real Google sign-in popup should open. After approving, the card flips to a green 'Connected' badge.",
                "Repeat for Outlook with a Microsoft account if you have one.",
                "If you cancel the popup or the OAuth handshake fails, a red toast appears and the card stays in the 'Connect' state — try again or move on.",
                "Confirm the bottom safety blurb mentions encrypted-at-rest tokens and that you can disconnect later from Settings.",
                "Click 'Skip for now' to confirm you can advance without connecting.",
            ]),
            ("Step 4 — E-signature (Agent / TC / Team Lead / Attorney only — Admin and external roles skip this step).", [
                "Confirm a single DocuSign card with a bullet list of perks.",
                "Click Connect. A real DocuSign OAuth popup opens. Approve to flip the card to Connected.",
                "Click 'Skip for now' to confirm skipping is allowed.",
            ]),
            ("Final step — All set.", [
                "Confirm a short confetti burst plays once, plus a 'You're all set, {first name}.' headline.",
                "Internal roles see TWO action cards. The recommended one is 'Create your first transaction'. The other is 'Go straight to your dashboard'.",
                "External roles see only the dashboard card (relabelled 'Recommended').",
                "Click 'Create your first transaction'. Confirm the full New Transaction wizard opens layered on top of the onboarding screen — onboarding only completes once you create a transaction (or close that wizard).",
                "Separately, click 'Go straight to your dashboard'. Confirm a small success step happens, you land on /dashboard with the URL replaced (back button does NOT re-open onboarding), and the product tour fires automatically on top of the dashboard (see feature 13).",
            ]),
            ("Save / resume / refresh behaviour.", [
                "After clicking Continue on Step 2, refresh the browser. Your name, phone, role, company, and logo should auto-populate (the data was saved to the server).",
                "However, the wizard always restarts at Step 1 on refresh — there is no 'finish later' bookmark yet.",
                "Until you click one of the final-step CTAs, every login forwards you back to /onboarding.",
                "Clicking a previous step in the rail jumps you back; jumping forward is intentionally blocked (you must use Continue so saves run).",
            ]),
        ],
        "expected_result": [
            "Each step shows the correct fields and validation for the role you selected.",
            "Internal roles see 4–5 steps; external roles see 3 steps.",
            "Founders see the Company / brokerage and Brand logo fields on Step 2; invitees see a read-only 'Joining: {brokerage name}' banner instead.",
            "Gmail / Outlook / DocuSign connections are real OAuth — connecting one shows a green 'Connected' badge that persists into Settings → Integrations.",
            "Logo files outside the allowed types or larger than 2 MB are rejected with a clear toast.",
            "Either final-step CTA marks onboarding complete on the server and triggers the product tour the next time the dashboard mounts.",
        ],
        "future_ideas": [
            "Add a 'Save and finish later' option that remembers the current step (today only the field values are remembered).",
            "Pre-flight check for popup-blocked browsers and offer a fallback redirect-based OAuth path.",
            "Preview the uploaded logo at the exact size it will appear in the app's sidebar.",
            "Let a user preview which value cards / steps an external role will see before they switch the dropdown.",
            "Add an invitee-only 'Welcome from {inviter name}' message under the Joining banner so the invitee knows who brought them in.",
        ],
    },
    {
        "no": 13,
        "category": "First-Time User Experience",
        "feature": "Product Tour overlay (rebuilt — role-aware spotlight tour)",
        "route": "/dashboard (and any other signed-in page once the tour is started)",
        "how_to_test": [
            ("First-time auto-start.", [
                "Finish the onboarding wizard with a fresh test account, then click 'Go to Dashboard' (or 'Create your first transaction' and complete that flow). The product tour should fire automatically the moment the dashboard loads.",
                "If you sign in with an existing account that has never seen the tour, the tour should also auto-start the first time the dashboard mounts.",
            ]),
            ("Manual replay.", [
                "Open Settings → Help & Tour → 'Replay the guided walkthrough' and click 'Start tour'.",
                "Confirm the tour restarts immediately for whichever role you are signed in as.",
            ]),
            ("Step list — Agent / Transaction Coordinator / Team Lead / Admin.", [
                "Step 1 — Welcome card (centered, no spotlight).",
                "Step 2 — Spotlights the four KPI tiles in the sidebar ('Your week, in four numbers').",
                "Step 3 — Spotlights 'Active Transactions' in the sidebar.",
                "Step 4 — Spotlights 'My Task Queue' in the sidebar.",
                "Step 5 — Spotlights 'All Documents' in the sidebar.",
                "Step 6 — Spotlights the top-bar 'Today's AI Briefing' button.",
                "Step 7 — Spotlights the top-bar search ('Search ⌘K').",
                "Step 8 — Spotlights the top-bar notifications bell.",
                "Step 9 — Spotlights the '+ New Transaction' button.",
                "Final — Centered finale card; the 'Next' button changes to 'Finish'.",
            ]),
            ("Step list — Attorney (5 steps).", [
                "Welcome → Matter Queue (sidebar transactions, relabelled) → Documents → Today's AI briefing → Finale.",
            ]),
            ("Step list — FSBO Customer / Client / Vendor (5 steps).", [
                "Welcome → My Properties (sidebar transactions, relabelled) → Documents → Ask Velvet Elves AI (sidebar AI item) → Finale.",
            ]),
            ("Tour controls.", [
                "Next / Finish — primary orange button on the right.",
                "Back — ghost button (disabled on step 1).",
                "Skip — small X in the top-right of the tooltip card. Clicking the dimmed area outside the spotlight also skips.",
                "Progress dots and step counter (for example '2/9') appear inside the tooltip. Click any earlier dot to jump back. Forward jumps are blocked.",
                "Keyboard: → or Enter to advance, ← to go back, Esc to skip. ⌘K / Ctrl+K is intentionally passed through so global search still works mid-tour.",
            ]),
            ("Persistence.", [
                "Only clicking 'Finish' on the final step (or pressing Esc on the final step) marks the tour complete.",
                "Skipping mid-tour does NOT mark it complete — open Settings → Help & Tour and click Start tour to resume from the beginning.",
                "Once complete, the tour does not reappear automatically on the next login. You can always replay it from Settings.",
            ]),
        ],
        "expected_result": [
            "The tour spotlights the right element for each step, with an orange border, a soft halo, and a slow pulse ring.",
            "Tooltips auto-flip to whichever side has room (top / bottom / left / right) and stay inside the viewport.",
            "Internal roles see a 9-step tour. Attorney and external roles see 5-step tours with role-specific copy.",
            "Skipping does not lock the tour; only Finish marks it complete.",
            "The Settings → Help & Tour 'Start tour' button always replays the role-appropriate tour.",
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
        "feature": "All Documents page — overview, access, and deep-link entry",
        "route": "/documents",
        "how_to_test": [
            ("Open /documents and check the header.", [
                "The page title reads 'All Documents' (with a small 'Workflow > All Documents' breadcrumb on wide screens).",
                "Next to the title, an orange count pill shows '{N} files'. When there is at least one missing required document it extends to '{N} files / {N} missing'.",
                "While the document list is fetching, the count pill is replaced by a smaller pill that reads 'Loading' with a spinner.",
            ]),
            ("Check the top-right header buttons.", [
                "'Upload Document' (or just 'Upload' on a narrow screen) is always visible.",
                "'Send for Signature' is visible. The text label collapses to a pen icon on narrow screens.",
                "'Deletion Queue' is visible only when you are signed in as an internal role (Agent, Transaction Coordinator, Team Lead, Attorney, or Admin). The text label collapses to a flag icon on narrow screens.",
            ]),
            ("Check the underline-style filter tabs directly below the title row.", [
                "Tabs: All, Signed, Pending Review, Sent for Sig., Missing — each shows a count badge.",
                "The active tab is highlighted with an orange underline and orange text.",
                "The 'Missing' badge turns red when the count is greater than zero.",
            ]),
            ("Try opening /documents as a non-internal role (for example as a For-Sale-By-Owner Customer if that account is available).", [
                "You should be redirected to /dashboard instead of seeing the page.",
                "Note: as a result, the 'Flag for Deletion' path no longer applies on this page — non-internal flagging now happens only inside a transaction's documents tab.",
            ]),
            ("Confirm the page loads every document, not just the most recent 100.", [
                "If your tenant has more than 100 documents, scroll down or use the search box to find an older one — it should still appear (the page paginates through every page on load).",
            ]),
            ("Test the Cmd/Ctrl+K global search deep-link entry.", [
                "Press Cmd+K (Mac) or Ctrl+K (Windows) anywhere in the app to open the global search palette.",
                "Search for a document by name and press Enter on the matching result.",
                "/documents opens with the matching transaction's drawer expanded, the matching row scrolled into view, and a brief amber flash animation on that row.",
                "Confirm the 'focus' and 'tx' query parameters are stripped from the URL afterwards (so a refresh does not re-flash forever).",
                "If the document was deleted or filtered out, a toast appears: 'Document not found in the current view'.",
            ]),
            ("Force the empty state.", [
                "Apply filters that return no results — confirm 'No documents match this filter' with a 'Clear filters' button.",
            ]),
            ("Force the error state.", [
                "Briefly turn off your internet and reload — the page should show 'Failed to load documents' with a 'Retry' button.",
            ]),
        ],
        "expected_result": [
            "The title, count pill, filter tabs, and header buttons all render correctly for the signed-in role and screen size.",
            "Client / non-internal users cannot reach this page.",
            "Cmd+K deep-links open the right transaction, scroll to the matching row, flash it, and then clean the URL.",
            "Empty and error states are clear and give a way forward.",
        ],
        "future_ideas": [
            "Show a small tooltip on the count pill that explains what 'missing' means in plain language.",
            "On the redirect for non-internal users, briefly explain why they cannot see this page.",
            "Add a 'Report an issue' link on the error state so clients can flag problems directly.",
            "Persist the last opened transaction drawer between visits, so users do not lose their place when navigating away and back.",
        ],
    },
    {
        "no": "27.1",
        "category": "Daily Agent / Elf Workflow",
        "feature": "All Documents — unified command bar (search, side filters, view toggle)",
        "route": "/documents (Unified Command Bar — second tier, directly below the AI Briefing)",
        "how_to_test": [
            ("Locate the Unified Command Bar. It is a single white card with two tiers — the bottom tier holds the controls described here (Tier 1 is covered in 27.2).", [
                "Scroll the document list down. The Unified Command Bar should stick to the top of the scroll area with a soft frosted-glass backdrop so the search and filters stay reachable while you scan a long list.",
            ]),
            ("Use the search box on the left of Tier 2.", [
                "The placeholder reads 'Search documents, addresses, types...'.",
                "Type a partial document name, a transaction address, or a document type and confirm the list narrows as you type.",
                "Confirm the search field gains an orange focus ring when selected.",
                "Click the small 'x' inside the search box to clear it.",
            ]),
            ("Use the side filter pills.", [
                "Options: All, Buyer Side, Listing Side.",
                "Each pill shows a transaction count.",
                "The active pill has an orange background and bold amber text.",
                "On narrow screens the pills scroll horizontally rather than wrapping.",
            ]),
            ("Use the view toggle at the far right of the command bar.", [
                "Hover each toggle to see a tooltip: 'View grouped by transaction' or 'View grouped by status'.",
                "On wide screens each toggle shows its icon plus the text 'By Transaction' / 'By Status'.",
                "On narrow screens only the icons are visible (the text is hidden for accessibility but still read by screen readers).",
                "The active toggle has an amber background and the inactive toggle is plain white.",
            ]),
            ("Confirm the filter tabs in the page header still work together with these controls.", [
                "Header tabs: All, Signed, Pending Review, Sent for Sig., Missing.",
                "The header filter tabs and the Tier 1 status chips (see 27.2) always stay in sync — switching one updates the other.",
            ]),
            ("Combine multiple controls at once.", [
                "For example: search 'inspection' + Buyer Side + Signed tab + By Status view. Confirm the list still makes sense.",
            ]),
        ],
        "expected_result": [
            "Search updates the list in real time and the focus ring confirms the input is active.",
            "Side filter pills, view toggle, header filter tabs, and Tier 1 status chips each change what is shown.",
            "All controls can be used together without the list breaking.",
        ],
        "future_ideas": [
            "Remember the last-used view (By Transaction vs. By Status) per user.",
            "Let the user save filter presets such as 'My overdue reviews'.",
            "Add an 'Export this filtered list' button so the user can share the current view as CSV.",
            "Add text labels under the view-toggle icons on narrow screens so new users know what the icons mean without hovering.",
        ],
    },
    {
        "no": "27.2",
        "category": "Daily Agent / Elf Workflow",
        "feature": "All Documents — AI Briefing, status quick-filters, and completion progress",
        "route": "/documents (AI Briefing strip + Tier 1 of the Unified Command Bar, at the top of the content area)",
        "how_to_test": [
            ("Look at the AI Briefing strip at the top of the list (redesigned on April 20, 2026).", [
                "A small 'AI BRIEFING' tag with an orange sparkle icon is visible on the left.",
                "On wide screens, a muted 'Updated {date}' (or 'No recent document activity') timestamp sits at the far right of the badge row; on narrow screens that same timestamp appears below the summary paragraph instead.",
                "A bold one-line headline and a slightly lighter one-sentence summary are shown below the badge row.",
                "A blue primary action button sits on the right on wide screens and centres below the text on narrow screens. Its label changes based on what is most urgent — for example 'Focus missing docs', 'Review signature queue', 'Review pending docs', or 'Review signed docs'.",
                "While the briefing is loading, the strip shows the AI Briefing badge with a spinner plus two skeleton lines (no layout jump when it resolves).",
            ]),
            ("Click the primary action button.", [
                "The view resets to 'By Transaction' and the matching filter tab / status chip activates.",
            ]),
            ("Directly below the briefing, find the Unified Command Bar. Focus on Tier 1 (the top row of the bar).", [
                "Tier 1 contains four status quick-filter chips followed by the completion progress bar.",
                "Chips, in order: 'Signed' (green number), 'Pending' (blue number), 'Sent' (amber number), 'Missing' (red number) — each with a large count and a small label.",
                "On narrow screens the four chips sit in a 2x2 or 4-column grid; on wide screens they sit in a single row.",
            ]),
            ("Click one of the status chips.", [
                "The chip gains a coloured border and tinted background matching its number colour (green, blue, amber, or red).",
                "The list below filters to only that status, and the header filter tab with the matching name also becomes active — the two controls stay in sync.",
                "Hovering a chip shows a tooltip such as 'Filter by missing' when inactive, or 'Showing missing — click to clear' when active.",
            ]),
            ("Click the already-active chip a second time.", [
                "The chip returns to its transparent state and the filter resets to 'All'.",
            ]),
            ("Look at the completion progress bar on the right side of Tier 1.", [
                "The label 'Completion' appears to the left of the bar on screens at least 640 px wide (hidden on small phones to save space).",
                "A thin green-gradient bar shows the percentage of tracked documents that are fully signed.",
                "The numeric percentage is shown in bold green on the right of the bar.",
                "On wide screens a thin vertical divider separates the chip group from the completion bar.",
            ]),
        ],
        "expected_result": [
            "The AI briefing headline and summary reflect the most urgent state of your document portfolio right now, and the timestamp tells you how fresh the underlying data is.",
            "Clicking the primary action button switches to the matching filter tab and 'By Transaction' view.",
            "Each status quick-filter chip filters the list and stays in sync with the header filter tabs; clicking an active chip clears the filter.",
            "The percentage on the progress bar matches the ratio of signed documents to the total of signed + pending + sent (missing rows are excluded from the denominator).",
        ],
        "future_ideas": [
            "Show a small trend indicator next to the completion percentage (up / down vs. last week).",
            "Make the whole briefing sentence clickable, not just the action button.",
            "Add a 'Email this briefing to my manager' one-click action.",
            "Let the user pin a favourite status chip so it is always pre-filtered on page load.",
        ],
    },
    {
        "no": "27.3",
        "category": "Daily Agent / Elf Workflow",
        "feature": "All Documents — Transaction View (documents grouped by transaction)",
        "route": "/documents with 'By Transaction' selected",
        "how_to_test": [
            ("Switch the view toggle to 'By Transaction'.", []),
            ("Inspect each transaction card header when it is collapsed.", [
                "Property address on the left.",
                "A side badge: 'BUYER SIDE' (blue), 'LISTING SIDE' (amber), or 'BOTH SIDES' (purple).",
                "Closing date shown as 'Close: {date}'.",
                "Status pills: red '{N} missing doc(s)' if any are missing, or amber 'Sig. Pending' when signatures are outstanding.",
                "A mini progress bar on the right showing {signed}/{total}, green when all signed, amber when at or above 50%, red below 50%.",
            ]),
            ("Click a transaction card to expand it.", [
                "The drawer contains up to four sections (only shown when they have items): 'SIGNED / EXECUTED' (green), 'NEEDS ATTENTION' (amber), 'SENT FOR SIGNATURE' (amber), and 'MISSING / REQUIRED' (red).",
                "Each section shows its own count badge.",
            ]),
            ("At the bottom of the expanded drawer, check the extra controls.", [
                "A '+ Add another document to this transaction' button opens the Upload Document modal with this transaction already selected.",
                "A footer row shows close date, full address, side, and an 'Open Transaction' button that navigates to the transaction detail page.",
            ]),
            ("Scroll to the bottom of the whole list.", [
                "If any document has not been assigned to a transaction, an 'UNASSIGNED DOCUMENTS' group appears with those rows.",
            ]),
        ],
        "expected_result": [
            "The header summarises each transaction's document state at a glance.",
            "Only sections that contain items appear in the expanded drawer.",
            "'Add another document' pre-fills the correct transaction.",
            "'Open Transaction' navigates to the transaction detail page for that deal.",
        ],
        "future_ideas": [
            "Add 'Expand all' and 'Collapse all' buttons at the top of the list.",
            "Show the assigned agent and elf on the card header for team lead visibility.",
            "Add a 'Resend client-facing packet' shortcut inside the card footer.",
        ],
    },
    {
        "no": "27.4",
        "category": "Daily Agent / Elf Workflow",
        "feature": "All Documents — Status View (grouped by signature status)",
        "route": "/documents with 'By Status' selected",
        "how_to_test": [
            ("Switch the view toggle to 'By Status'.", []),
            ("Confirm the four status groups appear in this order, each with a coloured icon.", [
                "Signed / Executed (green check).",
                "Sent for Signature (amber diamond).",
                "Pending Review (blue dot).",
                "Missing / Required (red exclamation).",
            ]),
            ("Each group header shows the status title plus '{N} items across {M} transactions'.", []),
            ("Click a group to expand and confirm each document row shows the transaction address it belongs to.", []),
        ],
        "expected_result": [
            "All four groups render in the correct order.",
            "Groups align with whatever search, side filter, and filter tab are currently active.",
        ],
        "future_ideas": [
            "Add a 'Group by document type' option alongside 'Group by status'.",
            "Let the user drag-reorder groups for personal preference.",
        ],
    },
    {
        "no": "27.5",
        "category": "Daily Agent / Elf Workflow",
        "feature": "All Documents — missing required documents and 'Upload Now'",
        "route": "/documents (MISSING / REQUIRED rows in both views)",
        "how_to_test": [
            ("The app automatically flags certain required documents based on the transaction. Examples you can test:", [
                "'Appraisal Report' — appears for a buyer-side deal that is financed.",
                "'Counter Offer Addendum' — appears for a listing-side deal that has a counter offer on file.",
                "'Wire Instructions' — appears for a listing-side deal with a title/escrow closing mode.",
            ]),
            ("Confirm the visual style of a missing row.", [
                "Dashed pink/red border.",
                "Light red background.",
                "A 'MISSING' status badge.",
            ]),
            ("Click the 'Upload Now' button on a missing row.", [
                "The Upload Document modal opens with the transaction, suggested document type, and document label pre-filled.",
                "A 'SUGGESTED DOCUMENT' banner appears at the top of the modal with the label.",
            ]),
        ],
        "expected_result": [
            "Missing documents appear according to the rules above.",
            "'Upload Now' pre-fills the transaction, document type, and label correctly so the user can upload without retyping.",
        ],
        "future_ideas": [
            "Let admins customise the missing-document rules per tenant.",
            "Show a short reason next to each missing row ('Required because financing is conventional', etc.) so users understand why.",
        ],
    },
    {
        "no": "27.6",
        "category": "Daily Agent / Elf Workflow",
        "feature": "All Documents — Upload Document modal",
        "route": "Opens from 'Upload Document' header button, 'Upload Now' on missing rows, or '+ Add another document…' inside a transaction card",
        "how_to_test": [
            ("Open the Upload Document modal from the header button.", []),
            ("Check the 'ASSIGN TO TRANSACTION' dropdown.", [
                "It lists all active transactions by full address.",
                "Leaving it blank is allowed (the document becomes an unassigned upload).",
            ]),
            ("Check the 'DOCUMENT TYPE' selector.", [
                "Shows toggle chips for each type: Purchase Agreement, Inspection Report, Appraisal, Amendment, and others.",
                "At most one type can be selected at a time.",
            ]),
            ("Check the 'FILE' drop zone.", [
                "The hint underneath the drop zone reads 'PDF, DOC, DOCX, JPG, PNG, WEBP, GIF, TXT · Max 20 MB'.",
                "Drag and drop a file, or click 'Click to browse' to pick a file.",
                "Allowed types: .pdf, .doc, .docx, .jpg, .jpeg, .png, .webp, .gif, .txt.",
                "Max size: 20 MB. Try a file larger than 20 MB and confirm the modal surfaces a clear backend error.",
                "Note: spreadsheet types (.csv, .xlsx, .xls) are no longer accepted by the upload endpoint.",
            ]),
            ("Confirm a spinner appears in the drop zone while the file uploads, and that the primary button text changes to 'Uploading...'.", []),
            ("Click Cancel to close without uploading, and Upload Document to save.", []),
        ],
        "expected_result": [
            "The new file appears in both Transaction View and Status View.",
            "The upload is tagged with the chosen transaction and document type.",
            "Files over 20 MB or of unsupported types are rejected with a clear message.",
        ],
        "future_ideas": [
            "Suggest the document type automatically using AI on upload.",
            "Allow multi-file drag-and-drop in a single action.",
            "Add an 'Upload later' queue for users who are offline.",
        ],
    },
    {
        "no": "27.7",
        "category": "Daily Agent / Elf Workflow",
        "feature": "All Documents — Preview and Download",
        "route": "/documents (row actions on each document)",
        "how_to_test": [
            ("Click the eye (Preview) icon on a document row.", [
                "The Preview modal shows the file name in the header.",
                "For PDFs and images, the file renders inline.",
                "For other file types, the modal says 'Preview not available — download to view.'",
            ]),
            ("In the Preview modal header, click the green 'Download' button.", []),
            ("On any document row, click the standalone Download icon without opening preview first.", []),
            ("Inside the Preview footer, click the orange 'Send for Signature' button.", [
                "The Send for Signature modal opens with this document already selected.",
            ]),
        ],
        "expected_result": [
            "PDFs and images preview inline. Unsupported types prompt the user to download.",
            "Download always opens or saves the file.",
            "Send for Signature from the preview hands off cleanly to the signature flow.",
        ],
        "future_ideas": [
            "Add inline annotations on the preview (highlight, comment) for collaborative review.",
            "Remember the last zoom level between previews.",
            "Allow side-by-side comparison of two versions in the preview window.",
        ],
    },
    {
        "no": "27.8",
        "category": "Daily Agent / Elf Workflow",
        "feature": "All Documents — Send for Signature (live DocuSign integration)",
        "route": "'Send for Signature' header button, row action (pen icon), or Preview footer",
        "how_to_test": [
            ("Open the Send for Signature modal from each of the three entry points at least once.", [
                "Header button: opens with no document pre-selected.",
                "Row pen icon: opens with both transaction and document pre-selected.",
                "Preview footer 'Send for Signature' button: opens with the previewed document already selected and the preview modal closed in the background.",
            ]),
            ("If you opened the modal from the header (no document pre-selected), confirm the extra picker fields appear.", [
                "A 'TRANSACTION' dropdown listing every active transaction by full address.",
                "A 'DOCUMENT' dropdown that filters its options by the chosen transaction (or shows everything when no transaction is selected).",
                "Switching the transaction after picking a document that belongs to a different file clears the document selection.",
            ]),
            ("Confirm the DocuSign connection check at the top of the modal body.", [
                "If your DocuSign account is not yet connected, a red alert banner appears: 'No e-signature provider connected'.",
                "The banner has a 'Connect DocuSign' button that opens the inline DocuSign Connect wizard (covered in 27.14).",
                "Once connected, the red banner is replaced with a green confirmation: 'Connected to {provider}' with a one-line note that envelopes are sent from your account and that signed copies replace the original automatically.",
            ]),
            ("Configure the signers using the new manual recipient list.", [
                "Suggested-party chips appear above the list when the chosen transaction has parties on file (buyer, co-buyer, listing agent, etc.). Each chip shows '+ {name} ({party_role})'.",
                "Click a suggested chip to add that party as a signer with their name and email pre-filled. Clicking the same chip a second time is a no-op (duplicate emails are ignored).",
                "Click '+ Add signer' on the right of the SIGNERS label to add a blank row and type a name and email manually.",
                "Each signer row shows '#1', '#2', '#3' on the left so the routing order is obvious; rows can be removed with the small red X on the right.",
                "Confirm the empty-state message reads 'Add signers from the transaction's parties, or use \"Add signer\" to enter one manually.' when no signers have been added.",
            ]),
            ("Edit the 'SUBJECT' field at the bottom.", [
                "Pre-filled with 'Please sign the attached document' (250-character limit).",
                "Whatever you type here becomes the email subject DocuSign sends to the recipients.",
            ]),
            ("Optionally write a note in 'MESSAGE TO SIGNERS'.", []),
            ("Confirm Send button validation.", [
                "The Send button stays disabled until: a document and transaction are selected, every signer row has both a non-empty name and a syntactically valid email, AND DocuSign is connected.",
                "Try saving with a malformed email — confirm an inline red error appears: 'Each signer needs a name and a valid email address.'",
                "While sending, the button label changes to 'Sending...'.",
            ]),
            ("Click Send for Signature.", []),
        ],
        "expected_result": [
            "A success toast reads 'Sent for signature' with the document name and transaction address.",
            "The matching document row in the list flips to the 'Sent for Sig.' status badge and gains an 'Awaiting: {names}' line under the metadata.",
            "If the Send call fails, a red 'Send for signature failed' toast appears AND the error is shown inline at the bottom of the modal so the user does not have to re-open it.",
            "The DocuSign envelope is created in your linked account; signers receive the email immediately.",
        ],
        "future_ideas": [
            "Let the sender pick a signing order explicitly (sequential vs. parallel) — currently the order is the order the signers were added.",
            "Add support for additional providers (DotLoop, Authentisign, Adobe Sign) alongside DocuSign.",
            "Show live signature status updates inside the modal as each signer completes their part, instead of waiting for the row to refresh.",
            "Persist subject/message templates per user so common envelopes (e.g. 'Inspection addendum sign request') can be re-used in one click.",
        ],
    },
    {
        "no": "27.9",
        "category": "Daily Agent / Elf Workflow",
        "feature": "All Documents — Email Document modal",
        "route": "Three-dot menu on any document row (internal roles only)",
        "how_to_test": [
            ("Sign in as an internal role (Agent, Transaction Coordinator, Team Lead, Attorney, or Admin).", []),
            ("Open the three-dot menu on a document and click 'Email Document'.", []),
            ("Check the modal fields.", [
                "Attached document name is shown at the top (readonly, light orange background).",
                "'TO' field: accepts addresses separated by commas, semicolons, or spaces.",
                "'CC' field: optional, same format.",
                "'SUBJECT' field: pre-filled with 'Document: {filename}'.",
                "'MESSAGE' field: pre-filled with a ready-to-use template.",
            ]),
            ("Try to send with no recipient and confirm an inline error appears.", []),
            ("Add one or more valid recipients and click 'Send Email'.", []),
        ],
        "expected_result": [
            "A success toast reads 'Email queued' with the recipient count.",
            "The email is queued on the backend and will be logged in the communication history.",
        ],
        "future_ideas": [
            "Offer saved templates such as 'Client intro', 'Lender hand-off', 'Title company request'.",
            "Offer a 'Schedule for later' option.",
            "Flag invalid email addresses live as the user types.",
        ],
    },
    {
        "no": "27.10",
        "category": "Daily Agent / Elf Workflow",
        "feature": "All Documents — Rename / Reclassify modal",
        "route": "Three-dot menu on any document row (internal roles only)",
        "how_to_test": [
            ("Sign in as an internal role.", []),
            ("Open the three-dot menu and click 'Rename / Reclassify'.", []),
            ("Check the modal fields.", [
                "'FILE NAME' (required) is pre-filled with the current file name.",
                "'DISPLAY LABEL (optional)' — example placeholder: 'Executed PA — Smith'.",
                "'DOCUMENT TYPE' dropdown shows the current type selected, with all other types available.",
            ]),
            ("Try to save with an empty file name and confirm it is blocked.", []),
            ("Change one or more fields and click Save.", []),
        ],
        "expected_result": [
            "The document row updates its name, label, and type immediately after save.",
        ],
        "future_ideas": [
            "Use AI to suggest the correct document type based on the file content.",
            "Preview how the new name will appear in email subjects and the client portal before saving.",
        ],
    },
    {
        "no": "27.11",
        "category": "Daily Agent / Elf Workflow",
        "feature": "All Documents — Version History (and Upload New Version)",
        "route": "Three-dot menu on any document row",
        "how_to_test": [
            ("Open the three-dot menu and click 'Version History'.", []),
            ("Check the modal content.", [
                "Loading skeletons appear while versions load.",
                "Each version is listed with a label such as 'v1', 'v2', etc., the file name, size, upload date, and a 'Download' button.",
                "The newest version has a green 'Current' badge; older versions have a grey 'Legacy' badge.",
                "Empty state if no versions yet: 'No versions yet'.",
            ]),
            ("Click 'Upload New Version' and pick a replacement file.", [
                "A success toast appears: 'New version uploaded — v{N+1} is now current.'",
            ]),
            ("Reopen the modal and confirm the new version is marked Current.", []),
            ("Click Download on any historical version to confirm it still downloads.", []),
        ],
        "expected_result": [
            "All versions are listed in chronological order.",
            "Uploading a new version moves the previous Current version to Legacy.",
            "Downloads work for any version in the list.",
        ],
        "future_ideas": [
            "Show a side-by-side diff between two versions.",
            "Allow rolling back to a prior version and marking it current again.",
        ],
    },
    {
        "no": "27.12",
        "category": "Daily Agent / Elf Workflow",
        "feature": "All Documents — Archive (internal-only on this page)",
        "route": "Three-dot menu on any document row (/documents)",
        "how_to_test": [
            ("Sign in as an internal role (Agent, Transaction Coordinator, Team Lead, Attorney, or Admin).", [
                "Open the three-dot menu and click 'Archive Document' at the bottom (red text).",
                "Confirm the dialog: 'Archive this document? The document will be archived (soft-deleted) and can be restored by an authorized user.'",
                "Click Archive and confirm the document disappears from the list and a 'Document archived' toast appears.",
            ]),
            ("Confirm the non-internal flagging path is no longer reachable from /documents.", [
                "Non-internal users (For-Sale-By-Owner Customers, etc.) are redirected to /dashboard before they can reach the page, so the 'Flag for Deletion' modal does not open here.",
                "If the client wants to flag a document, they must do it from the documents tab inside an individual transaction (covered in section 23 / Documents window on a transaction card).",
            ]),
        ],
        "expected_result": [
            "Internal users can archive directly, with a confirmation dialog to prevent accidents and a toast on success.",
            "Non-internal users never see the dropdown action on /documents because the page redirects them away.",
        ],
        "future_ideas": [
            "Add a 'Restore archived document' area for admins so they can undo accidental archives.",
            "Add an undo toast immediately after archiving so an accidental click can be reverted in one tap.",
        ],
    },
    {
        "no": "27.13",
        "category": "Daily Agent / Elf Workflow",
        "feature": "All Documents — Deletion Approval Queue",
        "route": "'Deletion Queue' header button on /documents (internal roles only)",
        "how_to_test": [
            ("Sign in as an internal role and click 'Deletion Queue' in the page header.", []),
            ("Check each queued request card.", [
                "Document name (bold) and flagged date.",
                "Document type badge, if set.",
                "The reason the requester gave, in a light grey box.",
                "A 'DECISION NOTES (optional)' textarea for the reviewer.",
                "Two buttons: 'Reject' and 'Approve & Archive'.",
            ]),
            ("Check the empty state.", [
                "When there are no requests, the panel reads 'No pending deletion requests.'",
            ]),
            ("Approve one request and confirm the toast: 'Deletion approved — Document archived.'", []),
            ("Reject another request and confirm the toast: 'Deletion rejected — Document remains active.'", []),
        ],
        "expected_result": [
            "All flagged requests from non-internal users appear in order.",
            "Approve archives (soft-deletes) the document. Reject leaves it active.",
            "Both decisions are recorded for audit purposes.",
        ],
        "future_ideas": [
            "Notify the original requester automatically when their request is approved or rejected.",
            "Allow bulk approve / bulk reject for high-volume cleanup.",
            "Show the reviewer who flagged the document (requester name) alongside the reason.",
        ],
    },
    {
        "no": "27.14",
        "category": "Daily Agent / Elf Workflow",
        "feature": "All Documents — Connect DocuSign wizard (inline OAuth)",
        "route": "'Connect DocuSign' button inside the Send for Signature modal (only when no provider is connected yet)",
        "how_to_test": [
            ("Make sure your DocuSign account is NOT connected, then open the Send for Signature modal (header button is fine).", [
                "The red 'No e-signature provider connected' banner appears.",
                "Click the 'Connect DocuSign' button on the banner — a new modal opens on top.",
            ]),
            ("Inspect the wizard's intro step.", [
                "Header reads 'Connect DocuSign' on a soft amber gradient with a pen icon.",
                "Subheading: 'Link your DocuSign account so you can send documents for signature.'",
                "Body has three explainer rows: 'Tokens are encrypted at rest', 'Envelopes are sent from your DocuSign account', 'You can disconnect anytime'.",
                "A three-dot step indicator near the top shows you are on step 1 of 3.",
                "Footer buttons: Cancel and 'Continue to DocuSign' (with an external-link icon).",
            ]),
            ("Click 'Continue to DocuSign'.", [
                "The wizard advances to the authorize step. A spinner and the message 'Complete the sign-in in the DocuSign window' appear.",
                "A new browser popup opens pointing at DocuSign's OAuth screen.",
                "Helper text below the spinner: 'Popup blocked? Enable popups for this site and click Retry.'",
            ]),
            ("Complete the DocuSign login in the popup.", [
                "DocuSign closes the popup automatically and the wizard advances to the 'Done' step.",
                "A green check icon, the headline 'DocuSign connected', and a one-line summary 'Connected to {account_name} as {email}' (or just the email if the account name is not available) are shown.",
                "The footer button changes to 'Back to Send for Signature' (green).",
            ]),
            ("Click 'Back to Send for Signature'.", [
                "The wizard closes. The Send for Signature modal underneath now shows the green 'Connected to {provider}' confirmation, and the Send button enables once you add a valid signer.",
                "A page-level toast 'DocuSign connected — You can now send documents for signature.' confirms success.",
            ]),
            ("Test the failure path.", [
                "Cancel the DocuSign popup before it finishes.",
                "The wizard stays on the authorize step, the spinner is replaced by the message 'Waiting for a response from DocuSign…' and 'If the window closed without finishing, click Retry below.'",
                "If the OAuth handshake itself fails, a red 'Connection failed' banner shows the underlying error and the Retry button stays enabled.",
            ]),
        ],
        "expected_result": [
            "Connecting to DocuSign happens entirely inside Velvet Elves — the user never has to leave the documents page.",
            "On success, a toast confirms the connection and the Send for Signature flow becomes usable without a page refresh.",
            "If the user cancels or hits an OAuth error, they can retry without re-opening the wizard from scratch.",
            "Tokens are stored encrypted at rest on the user's profile (not visible in app logs).",
        ],
        "future_ideas": [
            "Detect popup-blocked browsers up-front and offer a fallback redirect flow instead of a popup.",
            "After a successful connection, auto-send a tiny test envelope to the signed-in user's own email so they can verify the link works.",
            "Surface the connected DocuSign account name in the profile menu (so users can tell at a glance which account is linked).",
        ],
    },
    {
        "no": "27.15",
        "category": "Daily Agent / Elf Workflow",
        "feature": "All Documents — Manage in-flight envelopes (Refresh, Void, Declined / Voided states)",
        "route": "Document rows whose signature status is sent / pending / declined / voided",
        "how_to_test": [
            ("Send a document for signature (see 27.8) but do not let the recipients sign yet.", [
                "Confirm the row's status badge changes to 'Sent for Sig.' and a new 'Awaiting: {name1}, {name2} +{N} more' line appears under the metadata.",
                "Hover the awaiting line — a tooltip lists every recipient with their role (e.g. 'Jane Smith (signer)').",
                "On wide screens the pen icon in the row's action strip is replaced with a circular Refresh icon (with the tooltip 'Refresh signature status'). On narrow screens the same action lives inside the three-dot menu as 'Refresh Signature Status'.",
            ]),
            ("Open the page (or refresh it) and confirm the auto-sync behaviour.", [
                "On every page load, the page silently calls DocuSign in the background for every in-flight envelope. This heals docs whose webhook was missed.",
                "Auto-sync runs at most once per document per page mount; failures are silent (the manual Refresh button stays available as the user's escape hatch).",
            ]),
            ("Click the Refresh icon on an in-flight envelope.", [
                "While the call is in flight, the icon spins and is disabled.",
                "On success a toast appears: 'Signature status refreshed — {Document name} - {Signature complete | Envelope voided | Envelope declined | Status: {raw status}}'.",
                "If the envelope finished, the row immediately flips to 'Signed' (green) without a manual refresh.",
            ]),
            ("Open the three-dot menu on an in-flight envelope and click 'Void Envelope'.", [
                "A toast appears: 'Envelope voided — {Document name} - recipients will no longer be able to sign.'",
                "The row gains a soft pink background, a red '! Voided' pill next to the status badge, and an inline message: 'Previous envelope voided. Send a new one when ready.'",
                "The pen icon is restored on the row (replacing the Refresh icon) and its tooltip becomes 'Resend for Signature (previous voided)'. The dropdown's send option label also updates to 'Resend for Signature'.",
            ]),
            ("Simulate a declined envelope (the recipient clicks Decline in DocuSign).", [
                "After the next sync, the row turns the same soft-pink background and shows a '! Declined' pill plus the inline message: 'A signer declined the previous envelope. Resend to try again.'",
                "Just like the voided case, the action becomes 'Resend for Signature' so the user can immediately recover.",
            ]),
            ("Click 'Resend for Signature' from a declined or voided row.", [
                "The Send for Signature modal opens with the same document already selected so the user can adjust signers / message and re-send.",
            ]),
        ],
        "expected_result": [
            "Awaiting recipients are visible at a glance without having to open DocuSign in another tab.",
            "Refresh and Void are reachable from both the row's action strip (wide screens) and the three-dot menu (mobile).",
            "Declined and voided envelopes are surfaced clearly with red styling, a descriptive inline message, and a one-click 'Resend' path so a stuck file never feels permanent.",
            "Auto-sync on page load means most stuck envelopes heal themselves before the user notices.",
        ],
        "future_ideas": [
            "Add a 'Why did this fail?' link to the declined/voided message that opens the DocuSign envelope page in a new tab.",
            "When voiding an envelope, prompt the user for a short reason and pass it to DocuSign so signers see context.",
            "Surface awaiting recipients on the transaction card header (not just on the document row) so a team lead can see which deal is stuck on whom from the list view.",
            "Add a manual 'Force-sync all' button that runs the sync logic across every in-flight envelope without a page reload.",
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
        "feature": "Settings page — overview and layout (rebuilt)",
        "route": "/settings",
        "how_to_test": [
            ("Open /settings and confirm the new layout.", [
                "The page is a single scrolling document — there are no tabs at the top any more.",
                "A hero panel at the top shows the title 'Settings' with an orange-gradient stripe.",
                "Below the title, four 'Snapshot' tiles are visible: Inbox, E-Sign, Credits, Templates. Each tile is clickable.",
                "On screens wide enough, a sticky left-rail nav titled 'Sections' is visible. The active section is highlighted in orange and updates as you scroll.",
            ]),
            ("Snapshot tile jump behaviour.", [
                "Click each Snapshot tile in turn. Each one should scroll-jump the page to the matching section header below.",
                "The 'Inbox' tile shows a 'connected/total' count (e.g. 1/2) — confirm the number matches what is shown in the Email Integrations card below.",
                "The 'Credits' and 'Templates' tiles currently show hardcoded numbers (250 of 1,000 and 5 templates) — flag if the values change unexpectedly.",
            ]),
            ("Section nav scroll-spy.", [
                "Scroll the page slowly. As each section enters the viewport, the matching item in the left-rail nav should highlight orange.",
                "Click any item in the left-rail nav. The page should jump to that section.",
            ]),
            ("Per-section deep-test.", [
                "Each Settings section is covered in its own feature entry below: 29.1 Email Integrations (Milestone 4.1), 29.2 E-Signature, 29.3 Branding, 29.4 AI Configuration, 29.5 Task Templates, 29.6 Help & Tour.",
            ]),
        ],
        "expected_result": [
            "Settings is a single scrolling page with a hero, four Snapshot tiles, and seven sections (Company, Email Integrations, E-Signature, Branding, AI Configuration, Task Templates, Help & Tour).",
            "Snapshot tiles and the left-rail nav both jump cleanly to the correct section.",
            "Scroll-spy keeps the left-rail nav highlight in sync with whichever section the user is reading.",
            "Every signed-in role sees the same Settings page (no role-gating on individual sections today).",
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
        "feature": "Settings — Email Integrations (Milestone 4.1 — required for AI Email Review)",
        "route": "/settings (Email Integrations section)",
        "how_to_test": [
            ("Confirm the section header.", [
                "Section title reads 'Email Integrations' with a small kicker label like 'Connections'.",
                "Top-right of the card has a 'Refresh' button — click it and confirm a brief spinner appears while the integrations list reloads.",
            ]),
            ("Confirm the provider rows.", [
                "Two rows are visible by default: Gmail and Outlook. Each shows the brand glyph, provider name, and the connected email address (or help text 'Connect via Google sign-in' / 'Connect via Microsoft 365 sign-in').",
                "An iCloud row is intentionally hidden right now (feature flag).",
                "Each connected provider shows a green 'Connected' pill and the date you connected.",
            ]),
            ("Connect Gmail.", [
                "Click 'Connect' on the Gmail row. A real Google sign-in popup opens.",
                "After approving, the popup closes and the Gmail row flips to a 'Connected' pill plus a Disconnect button. A success toast 'Gmail connected!' appears at the bottom.",
                "Cancel the popup before approving — the row should stay in the 'Connect' state with no error.",
            ]),
            ("Connect Outlook.", [
                "Repeat the same flow on the Outlook row using a Microsoft 365 account.",
            ]),
            ("Disconnect a provider.", [
                "On a connected row, click 'Disconnect'. A browser confirm dialog warns: 'Disconnecting … will stop syncing inbound mail and AI email automation will not be able to send …'.",
                "Click Cancel — nothing changes.",
                "Click OK / Confirm — the row flips back to the unconnected state and a toast confirms the disconnect.",
            ]),
            ("Error handling.", [
                "If the integrations API returns an error (for example during planned downtime), a red banner appears at the top of the card with the error message.",
                "Click Refresh to retry.",
            ]),
        ],
        "expected_result": [
            "Connecting Gmail or Outlook through the OAuth popup successfully links the account and shows a green 'Connected' pill.",
            "Tokens are stored encrypted at rest (no password is ever typed into Velvet Elves).",
            "Disconnecting always asks for confirmation first.",
            "At least one provider must be connected for the AI Email Review queue (feature 29.7+) to send replies — flag this if the user is confused.",
        ],
        "future_ideas": [
            "Surface a 'Last synced' timestamp and a manual 'Sync now' button per provider.",
            "Re-enable the iCloud row once the Apple app-specific-password flow is reviewed by the client.",
            "Show a small badge on the row when the linked mailbox has unread AI drafts waiting in /ai-emails.",
            "Detect popup-blocked browsers and offer a redirect-based fallback OAuth path.",
        ],
    },
    {
        "no": "29.2",
        "category": "Daily Agent / Elf Workflow",
        "feature": "Settings — E-Signature (DocuSign)",
        "route": "/settings (E-Signature section)",
        "how_to_test": [
            ("Confirm the section.", [
                "A single DocuSign tile is visible with the DocuSign logo, account email if connected, and the date you connected.",
                "If not connected, a 'Connect' button is visible. If connected, a 'Disconnect' button is visible instead.",
            ]),
            ("Connect DocuSign.", [
                "Click Connect. A 3-step wizard modal opens (Intro → Authorize via popup → Done) — same wizard described in feature 27.14.",
                "Complete the OAuth and confirm the tile flips to Connected with the DocuSign account name shown.",
            ]),
            ("Disconnect DocuSign.", [
                "Click Disconnect. A browser confirm dialog appears warning that future Send-for-Signature attempts will fail.",
                "Confirm and the tile reverts to the unconnected state.",
            ]),
        ],
        "expected_result": [
            "DocuSign connect/disconnect works without leaving the Settings page (the OAuth happens in a popup).",
            "Once connected, the green pill and account email match what is shown inside the Send for Signature modal in /documents.",
        ],
        "future_ideas": [
            "Add support for additional providers (DotLoop, Authentisign, Adobe Sign) alongside DocuSign in this section.",
            "Show monthly envelope count remaining on the connected tile so users do not hit DocuSign quota by surprise.",
        ],
    },
    {
        "no": "29.3",
        "category": "Daily Agent / Elf Workflow",
        "feature": "Settings — Branding (visual-only — please do NOT rely on this yet)",
        "route": "/settings (Branding section)",
        "how_to_test": [
            ("Inspect the Branding card.", [
                "A logo upload tile (dashed placeholder + Upload logo button) is visible.",
                "A Primary Color field defaults to the orange brand colour (#E26812) and shows a swatch preview.",
                "A Display Name field defaults to 'Velvet Elves AI'.",
                "A 'Save branding' button is visible at the bottom of the card.",
            ]),
            ("Try the controls.", [
                "Click Upload logo, type a different display name, and try changing the colour. Click Save branding.",
                "Refresh the page and confirm the changes did NOT persist — every field resets to the defaults.",
            ]),
        ],
        "expected_result": [
            "The Branding card is currently visual-only. No fields persist. This is a planned area not yet wired to the backend.",
            "Please flag clearly if any client expects this section to be live — we will move it earlier in the roadmap.",
        ],
        "future_ideas": [
            "Wire all three Branding fields to the tenant settings backend.",
            "Add live preview cards showing the branded sidebar and a sample email so the user sees the changes before saving.",
            "Add a tenant-wide 'Reset to Velvet Elves defaults' button.",
        ],
    },
    {
        "no": "29.4",
        "category": "Daily Agent / Elf Workflow",
        "feature": "Settings — AI Configuration (visual-only toggles)",
        "route": "/settings (AI Configuration section)",
        "how_to_test": [
            ("Inspect the AI Configuration card.", [
                "A hero strip reads 'AI Credits — 250 of 1,000 remaining' with a 25% progress bar and an Upgrade plan button.",
                "Three toggle rows are visible: 'Auto-parse uploaded documents' (on by default), 'Task recommendations' (on by default), 'Smart email drafts' (off by default).",
            ]),
            ("Try the controls.", [
                "Flip each toggle. Confirm the toggle visually flips.",
                "Refresh the page. Confirm the toggle resets to its default — settings are not yet persisted.",
                "Click Upgrade plan. Nothing happens — this is a placeholder button.",
            ]),
        ],
        "expected_result": [
            "Toggles flip visually but do not persist on refresh.",
            "AI Credits numbers are hardcoded and do NOT reflect real usage — please flag if a stakeholder expects them to.",
        ],
        "future_ideas": [
            "Wire each toggle to the tenant AI settings (tone, disclaimer, escalation hours, auto-send threshold) so admins can actually configure AI behaviour.",
            "Replace the hardcoded credit count with a real meter pulled from the AI usage backend.",
            "Add a 'Smart email drafts' explainer link that opens a preview of what the AI Email Review queue will look like.",
        ],
    },
    {
        "no": "29.5",
        "category": "Daily Agent / Elf Workflow",
        "feature": "Settings — Task Templates (visual-only)",
        "route": "/settings (Task Templates section)",
        "how_to_test": [
            ("Inspect the card.", [
                "A list of five hardcoded templates is shown: Buyer Standard (12 tasks), Seller Standard (14), Dual Agency (18), Lease (8), Commercial (22).",
                "Each row has an 'Edit' button. The card header has an 'Import' button.",
            ]),
            ("Try the buttons.", [
                "Click Edit on any row — nothing happens.",
                "Click Import — nothing happens.",
            ]),
            ("Compare with the real Task Templates admin page.", [
                "The fully-wired Task Templates page lives at /admin/task-templates (covered in features 30 and 31). The version on this Settings card is a quick visual placeholder only.",
            ]),
        ],
        "expected_result": [
            "The Task Templates section on the Settings page is a placeholder — neither Edit nor Import is wired.",
            "Use /admin/task-templates for real template management.",
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
            ("Confirm the card.", [
                "A 'Replay the guided walkthrough' card is visible with a brief description and a 'Start tour' button.",
            ]),
            ("Click Start tour.", [
                "The page should reset the tour-completed flag for your user and immediately launch the role-aware product tour (see feature 13).",
                "Confirm the tour fires whether or not you have already finished it once before.",
            ]),
        ],
        "expected_result": [
            "Start tour always launches the product tour for the role you are signed in as (9-step internal, 5-step Attorney / FSBO).",
            "This is the only fully-wired control in the AI Configuration / Branding / Templates / Help cluster — please test it for every role.",
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
        "feature": "AI Email Review — overview, list, and filter tabs (Milestone 4.2)",
        "route": "/ai-emails",
        "how_to_test": [
            ("Reach the page.", [
                "Open the sidebar → Intelligence → 'AI Email Review' (the entry only shows for Agent / TC / Team Lead / Admin — FSBO and Attorney do not see it).",
                "You can also click the 'N AI drafts awaiting review' callout in the top-bar Notifications panel.",
                "Confirm the URL is /ai-emails. The legacy deep-link /ai-emails/:logId currently still loads the page but does NOT pre-select that draft (planned).",
            ]),
            ("Confirm the page header.", [
                "Breadcrumb 'Intelligence > AI Email Review'.",
                "Title 'AI Email Review' with an orange count pill (e.g. '3 drafts' or '1 draft').",
                "Right side: a muted 'Updated Xm ago' timestamp on wide screens, and a 'Refresh' button (spinner while fetching).",
            ]),
            ("Confirm the filter tabs.", [
                "Five tabs in this order: All, Needs Review, Ready to Send, Low Confidence, Escalated.",
                "Each tab has a numeric count badge.",
                "'Needs Review' and 'Escalated' badges turn red when their count is greater than zero.",
                "Click each tab in turn and confirm the list narrows to the matching subset.",
            ]),
            ("Auto-refresh and bell sync.", [
                "Leave the page open for 60+ seconds. The list silently refetches every minute.",
                "If a new draft lands while you have the page open, it appears in the list without a manual refresh.",
                "Open the top-bar bell on any page — the unread count should match the All tab count here.",
            ]),
            ("Empty / loading / error states.", [
                "When the list is loading, four pulsing grey skeleton rows are shown.",
                "When there are no drafts at all, the right pane reads 'Inbox is clear — When the AI prepares a reply that needs your sign-off, it will land here for review before sending.'",
                "When the current filter has no matches but other tabs do, the right pane reads 'Nothing in this view — Try a different filter, or wait for the next AI-prepared reply to land here.'",
                "If the list fails to load, a centered 'Couldn't load drafts.' card is shown with a 'Try again' link.",
            ]),
        ],
        "expected_result": [
            "Sidebar navigation, breadcrumb, count pill, filter tabs, and refresh button all render correctly.",
            "The list only contains drafts your role is allowed to act on (server-enforced).",
            "Auto-refresh runs every 60 seconds; immediate invalidation happens after every Approve / Edit / Discard / Regenerate action.",
            "Empty, loading, and error states all give the user a clear way forward.",
        ],
        "future_ideas": [
            "Add an inline search box and sort control inside the list pane.",
            "Add a per-row checkbox + bulk Approve / Discard so a reviewer can clear a backlog quickly.",
            "Wire the deep-link /ai-emails/:logId so notifications open the exact draft in question.",
            "Stream live updates over websocket so the list does not have to poll every minute.",
        ],
    },
    {
        "no": "29.8",
        "category": "Daily Agent / Elf Workflow",
        "feature": "AI Email Review — list pane row anatomy",
        "route": "/ai-emails (left list pane)",
        "how_to_test": [
            ("Inspect any draft row.", [
                "Status dot at the start: green for high-confidence drafts, amber for medium, red for low or escalated, grey when the AI could not score itself.",
                "Subject line, bolded when the row is selected, falls back to '(no subject)' if missing.",
                "Recipient email(s) shown beneath the subject in monospaced text.",
                "Pill row beneath the recipient: a 'kind' label (Factual question / Document request / Vendor reply / Uncertain — review carefully / Other), a confidence percent, and an 'Escalated' red pill if past the escalation deadline.",
                "Right side: relative timestamp (for example '12m ago') and a chevron that becomes visible on hover or when the row is selected.",
            ]),
            ("Click a row.", [
                "The row gains an orange left edge bar and the detail pane on the right loads (see 29.9).",
            ]),
            ("Confirm there is no list-pane search / sort / bulk-action UI yet.", [
                "Filter tabs at the top of the page are the ONLY filtering surface. Flag if the client expects per-row checkboxes or a search field.",
            ]),
        ],
        "expected_result": [
            "Every row exposes confidence, kind, recipient, subject, escalation status, and timestamp at a glance.",
            "Selection persists across the 60-second auto-refetch as long as the draft is still in the filtered slice.",
        ],
        "future_ideas": [
            "Expose the underlying transaction address on each row so a reviewer can scan deals without opening each draft.",
            "Show a small 'Has attachments' icon (planned alongside attachment support).",
            "Offer a compact / comfortable density toggle for high-volume reviewers.",
        ],
    },
    {
        "no": "29.9",
        "category": "Daily Agent / Elf Workflow",
        "feature": "AI Email Review — detail pane (AI Verified From + Original Inbound + flagged assumptions)",
        "route": "/ai-emails (right detail pane)",
        "how_to_test": [
            ("Open any draft and inspect the detail pane.", [
                "Hero header: pill row showing AI Draft badge (sparkles icon), Kind pill, a Confidence meter (label + tiny progress bar + percent), and an Escalated pill if past the deadline. Relative timestamp on the right.",
                "Subject line in serif type below the pill row.",
                "'To:' line (always shown, monospaced). 'Cc:' line only appears if the AI has CC'd anyone — by default the file owner agent is auto-CC'd so they keep a copy in Sent.",
            ]),
            ("Body grid — left.", [
                "AI-drafted reply rendered as plain text.",
                "Phrases the AI hedged on are wrapped in amber highlights so your eye lands on them first.",
                "If any flagged assumptions exist, an amber-bordered 'Flagged assumptions' panel lists each one explicitly below the body.",
            ]),
            ("Right rail — AI Verified From.", [
                "An orange-eyebrowed card lists every key/value the AI cited (address, closing_date, status, document names, etc.).",
                "If the rail is empty, an orange dashed warning card reads 'No source data was cited for this draft. Treat the body as a generic response and verify each fact manually.'",
            ]),
            ("Right rail — Original Inbound.", [
                "A separate small card shows the inbound sender, timestamp, subject, and body that triggered this AI draft.",
                "While loading, a small skeleton renders. If the original cannot be loaded, the card reads 'Couldn't load the original inbound message.'",
            ]),
        ],
        "expected_result": [
            "Confidence percent, kind, and escalation pill in the hero header always match what the list pane shows.",
            "Highlighted assumption phrases inside the body match the explicit list under 'Flagged assumptions'.",
            "AI Verified From only contains keys the AI actually cited — never guess values.",
            "Original Inbound is the email that triggered this reply, NOT the entire thread (full-thread view is a future improvement).",
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
        "feature": "AI Email Review — actions (Approve & Send, Edit & Send, Regenerate, Discard)",
        "route": "/ai-emails (action footer on the detail pane)",
        "how_to_test": [
            ("View-mode actions.", [
                "Approve & Send (orange primary) — sends the AI draft as-is. A success toast 'Sent — AI reply approved and delivered.' appears.",
                "Edit (ghost) — switches the body card into editable mode (see below).",
                "Regenerate (ghost) — discards this draft and asks the AI to redraft from the original inbound. Toast 'Regenerated — A fresh draft is ready for review.'",
                "Discard (ghost, red) — opens an AlertDialog: 'Discard this AI draft? The draft will be removed from your review queue. The original inbound message stays in your communication log.' Click Cancel or Discard.",
            ]),
            ("Edit-mode actions.", [
                "Edit makes the Subject and Body editable, with a live character counter beneath the body.",
                "Send Edit (orange primary) — sends your edited version. Editing also clears the AI's flagged assumptions on the server. Toast 'Sent — Edited reply delivered.'",
                "Cancel — discards local edits and returns to view mode.",
            ]),
            ("Failure cases — confirm each action surfaces a clear error.", [
                "If you have not connected an email provider (Settings → Email Integrations), Approve & Send fails with a red toast 'Send failed — No active gmail integration.'",
                "If the API errors for any other reason, the toast shows the underlying error message verbatim — please copy it into your feedback so the team can debug.",
            ]),
            ("Confirm the actions that are NOT present yet.", [
                "There is no Decline / Ignore button (Discard is the only 'no' action today).",
                "There is no Reassign or 'Mark Reviewed' button.",
                "There is no attachment chip area or attachment uploader.",
                "There is no scheduled-send option or send-from identity picker (sends always come from the file owner's connected mailbox).",
            ]),
        ],
        "expected_result": [
            "Approve & Send, Edit & Send, Regenerate, and Discard all complete in the foreground with a toast and immediate list invalidation.",
            "Editing a draft clears its flagged assumptions on the server because the human reviewer just rewrote the content.",
            "Discard preserves the original inbound message in the communication log — only the draft disappears.",
            "All four actions are server-role-enforced; an unauthorized user gets an error toast on click rather than a hidden button.",
        ],
        "future_ideas": [
            "Add a Reassign button so a Team Lead can hand a draft to a colleague without opening it.",
            "Add a Mark Reviewed (no-send) status for drafts the human read but does not want to send.",
            "Add support for attachments when replying so contracts and addenda can ride out with the AI reply.",
            "Add a per-tenant 'Auto-send when confidence is over X%' threshold (backend already supports it; no UI yet).",
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
        "route": "/admin/users/<userId> (reachable from any avatar tile on /team or any row on /admin/users)",
        "how_to_test": [
            ("Reach the page from the new Team Members admin list.", [
                "From /admin/users, click a member's avatar, name, or 'View profile' button. The detail page opens with a 'Team › Members › {name}' breadcrumb and a back arrow.",
                "From /team, click any avatar tile in 'Recently added members' to open the same detail page.",
            ]),
            ("Confirm the page renders.", [
                "A profile card on the left with name, email, phone, joined date, last sign-in, and role.",
                "A side-rail with a status snapshot (active / inactive) and the role badge.",
                "If the user is the workspace owner, the avatar has a small orange crown badge.",
            ]),
            ("Try a problem URL.", [
                "Paste /admin/users/some-fake-id directly in the browser. A clear 'Failed to load user' error card should appear, NOT a white screen.",
            ]),
        ],
        "expected_result": [
            "A valid user id renders the profile card without errors.",
            "An invalid or deleted user id shows a clean error state with a way to navigate back.",
        ],
        "future_ideas": [
            "Add an audit trail showing the user's recent actions (logins, role changes, transactions worked).",
            "Add an inline Edit form so an Admin can update name, phone, or role from this page (today edits happen via Settings or other admin tools).",
            "Show recent transactions assigned to this user so a Team Lead has full context.",
        ],
    },
    {
        "no": "32.1",
        "category": "Admin / Team Lead Extras",
        "feature": "Team Overview page",
        "route": "/team (Team Lead and Admin only)",
        "how_to_test": [
            ("Reach the page.", [
                "Sign in as a Team Lead or Admin. Open the sidebar and click 'Team', or paste /team in the browser bar.",
                "If you are signed in below Team Lead (Agent, TC, Client, FSBO, Vendor, or Attorney), opening /team should redirect to /unauthorized.",
            ]),
            ("Confirm the page header.", [
                "A breadcrumb 'Team › Overview' on wide screens.",
                "Title 'Team Overview' next to an orange count pill ('{N} members').",
                "An orange 'Manage team' button on the right that opens /admin/users (feature 32.2).",
            ]),
            ("Look at the four KPI tiles across the top.", [
                "Active Members — total active members, plus a small hint with the number of roles covered.",
                "Pending Invites — count of invitations still waiting to be accepted.",
                "Seats Used — '{used} / {limit}' if your plan has a seat limit, just the count if seats are unlimited.",
                "Recently Active — how many people signed in within the last week.",
            ]),
            ("Inspect the 'Recently added members' card.", [
                "Up to 12 members are shown as small avatar tiles with role-tinted initials and their role label.",
                "The workspace owner has a small orange crown badge on their avatar.",
                "Click any avatar tile to open that member's detail page (feature 32).",
                "If you are the only member, the card shows a friendly empty state pointing at Team Members.",
            ]),
            ("Look at the 'Role Coverage' rows at the bottom of the same card.", [
                "Five rows (Admin, Team Lead, TC, Agent, Attorney) each show a role chip, a coverage bar, and 'count / total'.",
            ]),
            ("Inspect the three side-rail cards.", [
                "Pending Invites — up to four pending invitations. Each row shows the email, role, and a coloured chip with how much time is left ('6h', '2d', or red 'Expired'). A '+ N more' link jumps to the Pending Invitations tab.",
                "Last Seen — up to six recently active members with their relative last-sign-in time.",
                "Seat Usage — only appears if your plan has a seat limit. Shows 'X / Y seats' plus a fill bar that turns amber over 75% and red over 90%.",
            ]),
            ("Try the two quick-link cards at the bottom.", [
                "Team Members — opens /admin/users.",
                "Task Templates — opens /admin/task-templates (feature 30).",
            ]),
        ],
        "expected_result": [
            "The page is reachable for Team Lead and Admin roles only; lower roles are redirected to /unauthorized.",
            "All four KPI tiles, the roster, the role coverage rows, and the three side-rail cards reflect real data from the workspace.",
            "Clicking an avatar tile or 'Manage team' navigates without a full page reload.",
        ],
        "future_ideas": [
            "Let the user filter Team Members by clicking a role chip on the Role Coverage row.",
            "Surface a 7-day-activity sparkline on the KPI tiles for at-a-glance trend.",
            "Allow pinning a favourite member for quick contact from the side rail.",
        ],
    },
    {
        "no": "32.2",
        "category": "Admin / Team Lead Extras",
        "feature": "Team Members admin — Active members tab",
        "route": "/admin/users (Team Lead and Admin only)",
        "how_to_test": [
            ("Reach the page.", [
                "From /team click 'Manage team', or open /admin/users directly.",
                "Lower roles than Team Lead should be redirected to /unauthorized when they try this URL.",
            ]),
            ("Confirm the page header.", [
                "Breadcrumb 'Team › Members'.",
                "Title 'Team Members' plus a seat pill — '{used} / {limit} seats' on paid plans, '{N} members' otherwise.",
                "An orange 'Invite teammate' button on the right (visible to Agent and above).",
            ]),
            ("Confirm the two tabs.", [
                "'Active members' tab with a count badge.",
                "'Pending invitations' tab with a separate count badge that turns amber when invites are pending.",
                "Click each tab and confirm the body switches between the members list and the invitations list.",
            ]),
            ("Use the filter toolbar on the Active members tab.", [
                "Type in the search box — the list filters by name and email as you type.",
                "Open the role dropdown ('All roles' default) — pick a role and confirm only members with that role remain.",
                "Combine search + role filter; confirm both apply at once.",
            ]),
            ("Inspect a member card in the collapsed view.", [
                "Role-tinted avatar with white initials and a soft halo. The workspace owner has a small orange crown badge.",
                "Member name in serif type, with the email and last sign-in date shown alongside.",
                "A role chip on the right (Admin, Team Lead, TC, Agent, Attorney, Client, FSBO, Vendor).",
                "A round chevron control that flips the card open.",
                "A three-dot actions menu on the right (visible only to Admin / owner; see features 32.5 and 32.6).",
            ]),
            ("Click a card to expand it.", [
                "An orange accent stripe and a 'MEMBER PROFILE' kicker fade in.",
                "Four info tiles: Email (clickable mailto), Phone (clickable tel, or 'Not provided'), Joined date, Last sign-in.",
                "A footer with a 'View full profile' button. If you are the owner, a 'Transfer ownership' button appears here too. If you are Admin, a 'Deactivate' button appears on the right for everyone except yourself and the current owner.",
            ]),
            ("Confirm the empty / filter-empty states.", [
                "Apply a search term with no matches — the body shows a clean 'No members match this filter' card with a hint to try a different term.",
            ]),
        ],
        "expected_result": [
            "Members render as expandable cards with role-tinted styling, an owner crown on the right avatar, and a chevron indicator.",
            "Search and role filter narrow the list in real time.",
            "Action buttons only appear for users who have permission (Admin / owner) and never on your own card.",
        ],
        "future_ideas": [
            "Show a 'last active' relative timestamp directly on the collapsed card (today only the date shows).",
            "Add bulk selection so an Admin can deactivate or change role for multiple members at once.",
            "Add an inline 'Resend welcome email' action on members who never signed in.",
        ],
    },
    {
        "no": "32.3",
        "category": "Admin / Team Lead Extras",
        "feature": "Team Members admin — Pending invitations tab",
        "route": "/admin/users → 'Pending invitations' tab",
        "how_to_test": [
            ("Switch to the Pending invitations tab on /admin/users.", []),
            ("Confirm the list rendering.", [
                "If there are no pending invitations, the empty state reads 'No pending invitations' with a hint to use the 'Invite teammate' button.",
                "Each pending invitation row shows: a mail-icon avatar, the invited email (bold), the invited role chip ('Invited as Agent', etc.), and a clock chip on the right showing how much time is left ('6h left', '2d left', or red 'Expired').",
                "The time chip turns red when under 12 hours, amber under 48 hours, otherwise neutral grey.",
            ]),
            ("Use the row actions.", [
                "'Copy link' button (desktop) or the same option inside the three-dot menu (mobile) — copies the invite URL to your clipboard and shows a 'Link copied' toast. The link uses your workspace's invite-base URL so white-labelled subdomains are honoured.",
                "Three-dot menu → 'Resend email' — re-sends the original invitation email and shows an 'Invite resent' toast.",
                "Three-dot menu → 'Extend by 72h' — pushes the expiry 72 hours into the future and shows an 'Expiry extended' toast.",
                "Three-dot menu → 'Revoke invitation' (red) — asks for confirmation, then disables that invite link entirely and shows an 'Invitation revoked' toast.",
            ]),
            ("Try the failure paths.", [
                "If the clipboard is blocked by the browser, the Copy-link toast switches to 'Could not copy — Clipboard access was blocked.'",
                "If an invite has no token attached (very rare — only happens on data created before this feature shipped), the Copy-link option is disabled with a tooltip explaining the issue.",
            ]),
        ],
        "expected_result": [
            "All four actions (Copy link, Resend, Extend, Revoke) work for invitations that are still pending and not yet accepted.",
            "Accepted invitations do not appear in this tab.",
            "Revoking an invitation immediately removes it from the list and prevents the invitee from accepting.",
        ],
        "future_ideas": [
            "Add a 'Bulk revoke expired' button so cleanup is one click instead of N.",
            "Show who originally sent each invitation, so a Team Lead can see which Admin invited a particular email.",
            "Add a tooltip on the Copy-link button that previews the full URL before copying.",
        ],
    },
    {
        "no": "32.4",
        "category": "Admin / Team Lead Extras",
        "feature": "Invite teammate modal",
        "route": "/admin/users → 'Invite teammate' button",
        "how_to_test": [
            ("Click 'Invite teammate' on the /admin/users header.", [
                "The modal opens with an orange accent stripe at the top and a 'SEND A ONE-TIME INVITATION' kicker.",
                "Body fields: Email address (required), Role dropdown (required), plus a one-line role hint that updates as you change the role.",
            ]),
            ("Try the Role dropdown.", [
                "Sign in as different inviter roles (Agent, Team Lead, Admin) and confirm the dropdown contents change. For example, only Admins can invite new Admins.",
                "Pick each role and read the helper line below the dropdown — for example 'Owns their deals end-to-end with AI assistance' for Agent.",
            ]),
            ("Try valid and invalid emails.", [
                "Empty email — Send is blocked with an inline 'Enter a valid email address' message.",
                "An email that already belongs to a member — Send fails with '{email} already has an account.'",
                "A brand-new email on a free plan above the seat cap — Send fails with the seat-limit copy, mentioning the current plan.",
                "A valid new email — click Send invite. The button label switches to 'Sending…'.",
            ]),
            ("After a successful send.", [
                "An 'Invite sent' toast appears with the recipient's email.",
                "The modal closes.",
                "The Pending invitations tab refreshes with the new row.",
            ]),
        ],
        "expected_result": [
            "Roles you cannot grant are filtered out of the dropdown automatically.",
            "Each failure mode (existing user, seat limit, plan-too-low, generic) surfaces a clear inline error instead of breaking the modal.",
            "A successful invite appears in the Pending invitations list immediately, ready for the invitee to accept.",
        ],
        "future_ideas": [
            "Allow inviting multiple emails at once (comma-separated) so an admin can bulk-onboard a team.",
            "Show a 'view what the invitee will see' preview link before sending.",
            "Let the admin pick a team or attach a transaction at invite time (planned for Phase 5).",
        ],
    },
    {
        "no": "32.5",
        "category": "Admin / Team Lead Extras",
        "feature": "Transfer workspace ownership",
        "route": "/admin/users → member three-dot menu (visible to the workspace owner only)",
        "how_to_test": [
            ("Sign in as the current workspace owner.", [
                "Confirm only your row shows the small orange crown badge.",
            ]),
            ("Find a different member's row.", [
                "Open the three-dot menu (or expand the card) — a 'Transfer ownership' option with a crown icon should be visible. You should NOT see this option on your own row, or on a member who is already the owner.",
            ]),
            ("Click Transfer ownership.", [
                "A confirmation dialog appears with the target's name and current role.",
                "If the target is not already an Admin, the dialog explicitly says 'they will be promoted to Admin'.",
                "The dialog warns that you will stay as Admin but lose owner-only abilities (schedule deletion, transfer ownership again) and that the action is logged.",
            ]),
            ("Confirm the transfer.", [
                "On success, an 'Ownership transferred' toast appears.",
                "The crown badge moves from your avatar to the new owner's avatar.",
                "Refresh /admin/users — the new ownership state persists on the server.",
            ]),
            ("Try as a non-owner.", [
                "Sign in as a regular Admin (not the owner) and confirm the 'Transfer ownership' option is hidden from every member's menu.",
            ]),
        ],
        "expected_result": [
            "Only the current owner sees the Transfer ownership control.",
            "The confirmation dialog clearly describes the side effects before you commit.",
            "After transfer, the previous owner can no longer schedule deletion or transfer ownership again — those controls disappear from Settings.",
        ],
        "future_ideas": [
            "Send an automatic email to the new owner immediately so they know responsibility has moved.",
            "Add an undo window (e.g. 30 minutes) on a recently-transferred ownership.",
            "Show the full audit trail of past ownership transfers on the Team Overview page.",
        ],
    },
    {
        "no": "32.6",
        "category": "Admin / Team Lead Extras",
        "feature": "Deactivate a member",
        "route": "/admin/users → member three-dot menu (Admin only)",
        "how_to_test": [
            ("Sign in as an Admin who is NOT the target.", [
                "Open the member's three-dot menu (or expand the card) — a red 'Deactivate' option should be visible.",
                "The option should NOT appear on the workspace owner's row, nor on your own row.",
            ]),
            ("Click Deactivate.", [
                "A confirmation dialog appears: 'Deactivate {name}? They will no longer be able to sign in. Re-activate later from this page.'",
                "Cancel and confirm the member is still listed.",
                "Re-open and click 'Deactivate' to confirm. A 'Member deactivated' toast appears.",
            ]),
            ("Re-fetch the list.", [
                "The deactivated member disappears from the Active members tab (because the list only shows active members).",
                "Any pending invitations created by that user remain unaffected — they are still in the Pending invitations tab.",
            ]),
        ],
        "expected_result": [
            "Deactivation requires confirmation and updates the list immediately.",
            "The owner cannot be deactivated — that option is hidden on their row.",
            "Deactivating yourself is also blocked (the action is hidden on your own row).",
        ],
        "future_ideas": [
            "Add a paired 'Re-activate' control that surfaces deactivated members in a separate sub-list.",
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
            ("Open /settings as different roles to see the difference.", [
                "As an Admin: the 'Organization Name' field is editable and an orange 'Save changes' button appears under the field.",
                "As any non-Admin (Team Lead, Agent, TC, Attorney, Client, FSBO, Vendor): the field is read-only with a soft grey background and a helper line 'Only an Admin can change the organization name. Ask your workspace owner if this needs to be updated.'",
            ]),
            ("As an Admin, edit the field.", [
                "Type a new name. 'Save changes' becomes enabled.",
                "Click Save. The button shows 'Saving…' briefly, then the change is persisted.",
            ]),
            ("Verify the change is shared across the brokerage.", [
                "Sign in as another member of the same workspace and open /settings — the new organization name should already be visible.",
                "Outbound emails and the invitation email subject/body will use the updated name on the next send.",
            ]),
            ("Try a problem case.", [
                "Leave the name empty and click Save — the server should reject the change with an inline red banner explaining the failure.",
                "Disconnect your network mid-save — the page should show a clear error message rather than silently failing.",
            ]),
        ],
        "expected_result": [
            "Admins can edit the organization name; everyone else sees a read-only field with a clear explanation.",
            "The new name persists for every member of the brokerage on the next page load.",
            "Errors from the server appear in a red banner above the field, with no white-screen failure.",
        ],
        "future_ideas": [
            "Show a small preview of how the organization name will appear in the sidebar logo, the invitation email subject, and outbound transaction emails before saving.",
            "Add a 'Tenant slug' field so admins can claim a unique subdomain (e.g. acme.velvetelves.com).",
            "Surface the workspace owner's name and email on this card so members know who to ask for changes.",
        ],
    },
    {
        "no": "32.8",
        "category": "Admin / Team Lead Extras",
        "feature": "Settings — Danger Zone (schedule / cancel deletion)",
        "route": "/settings (Danger Zone section, at the very bottom — visible only to the workspace owner or a platform admin)",
        "how_to_test": [
            ("Sign in as the workspace owner and scroll to the bottom of /settings.", [
                "Confirm a red-bordered 'Danger Zone' card with a 'Delete organization' button.",
                "Sign in as any other role on the same workspace and confirm the Danger Zone section is hidden completely — neither the left-rail nav entry nor the card appears.",
            ]),
            ("Click 'Delete organization' (owner only).", [
                "The button reveals a confirmation field that reads 'Type {workspace name} to confirm.'",
                "The 'Schedule deletion' button stays disabled until you type the workspace name exactly.",
                "A 'Keep organization' button is available to back out.",
            ]),
            ("Type the workspace name and click Schedule deletion.", [
                "A 'Deletion scheduled' toast appears.",
                "The card switches to a filled-red panel saying 'Deletion scheduled' with the exact date / time deletion will run.",
                "A note explains that audit logs and a full snapshot are archived per the platform's 2-year retention policy.",
                "A 'Cancel deletion' button is available — clicking it restores the workspace and shows a 'Deletion cancelled' toast.",
            ]),
            ("Try the legal-hold path.", [
                "If a platform admin has placed legal hold on your workspace, the Delete button is disabled and an amber banner reads 'This organization is on legal hold and cannot be scheduled for deletion. Contact platform support.'",
            ]),
            ("Try as a non-owner Admin.", [
                "Confirm the Danger Zone section does not appear at all in Settings (it is hidden, not just disabled).",
            ]),
        ],
        "expected_result": [
            "Only the owner sees the Danger Zone section; everyone else sees no trace of it.",
            "Scheduling deletion requires typing the workspace name exactly, which prevents accidental clicks, and the action is reversible during the grace period.",
            "While deletion is scheduled, the workspace remains usable and members can still sign in to cancel it.",
            "Legal hold disables the button with a clear, plain-language explanation.",
        ],
        "future_ideas": [
            "Show the exact UTC + local time the deletion will run, plus how many days are left, on a banner that follows the owner on every page.",
            "Send a daily reminder email to the owner while deletion is scheduled.",
            "Let the owner customise the grace-period length (current default is 30 days, set on the server).",
            "Add a 'Download a full export before I leave' button next to the schedule-deletion CTA.",
        ],
    },
    {
        "no": "32.9",
        "category": "Admin / Team Lead Extras",
        "feature": "Platform Admin — Tenants list (internal Velvet Elves staff only)",
        "route": "/platform/tenants (visible only to accounts flagged as platform admin)",
        "how_to_test": [
            ("Sign in as a platform admin and browse to /platform/tenants.", [
                "Non-platform users hitting this URL directly get a clean 404 page — the route does not even hint that it exists.",
            ]),
            ("Confirm the page header.", [
                "Title 'Tenants' and a short subtitle: 'Cross-tenant operations. Visible to platform admins only.'",
                "Card title 'All tenants (N)' showing the total count.",
            ]),
            ("Use the filter dropdown.", [
                "Options: All, Active, Suspended, On legal hold.",
                "Confirm the table narrows correctly when each filter is chosen.",
            ]),
            ("Inspect each tenant row.", [
                "Columns: Name (bold), Slug (mono code), Status badge, Plan badge, Actions.",
                "Status badges: 'Active' (green), 'Suspended' (grey), red 'Legal hold' badge with a shield icon, or red 'Scheduled deletion' badge if deletion is pending.",
            ]),
            ("Try each Actions button.", [
                "'Details' — opens the tenant detail page (feature 32.10).",
                "'Suspend' — opens a confirmation 'Members will be unable to sign in. You can reactivate later'. On confirm, the row flips to Suspended and a toast appears. The Suspend button is disabled when the tenant is on legal hold.",
                "'Reactivate' — appears in place of Suspend on suspended tenants. Confirms before reactivating.",
            ]),
        ],
        "expected_result": [
            "Non-platform users hitting /platform/tenants get a 404 (not a 403) — the route's existence is not leaked.",
            "Filter narrows the list correctly; the count badge stays accurate.",
            "Suspending / reactivating a tenant immediately updates the row and is logged in the platform audit log.",
        ],
        "future_ideas": [
            "Add a search box that matches name / slug / owner email.",
            "Add a 'Schedule deletion' action on the row alongside Suspend (currently only available from inside the tenant's own Settings → Danger Zone).",
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
            ("Open the page.", [
                "Click 'Details' on a row in /platform/tenants, or paste the URL directly.",
            ]),
            ("Confirm the page header.", [
                "A 'All tenants' back button at the top.",
                "Tenant name in large serif, slug + created date below.",
                "Status badges on the right: 'Active' / 'Suspended', plus red 'Legal hold' and / or 'Deletion scheduled' badges when applicable.",
            ]),
            ("Confirm the Identity card.", [
                "ID, Slug, Domain (custom domain if any), Domain status (verified / unverified), Verified at timestamp, Owner user id, and the Invite base URL (the white-label URL that invitation links will use).",
            ]),
            ("Confirm the Plan & lifecycle card.", [
                "Plan name (Solo, Team, etc.), Seat limit (or 'unlimited'), Staff seats currently used, Trial-ends date if any, Deletion-scheduled timestamp if any, and Legal hold reason if the tenant is on hold.",
            ]),
            ("Confirm the safety rails.", [
                "Non-platform users hitting /platform/tenants/<id> directly get a clean 404 page.",
                "If the tenant id is invalid or deleted, the page shows 'Tenant not found.' with a 'Back to list' link.",
            ]),
        ],
        "expected_result": [
            "All read-only data renders without errors.",
            "Non-platform users cannot reach this page even with a direct URL.",
            "Deleted or invalid tenant ids show a clean fallback rather than a broken page.",
        ],
        "future_ideas": [
            "Add inline edit for tenant name and plan from this detail page.",
            "Surface the tenant's recent audit-log events (last 50) directly on this page.",
            "Add a 'Reset domain verification' control for tenants stuck on unverified.",
            "Add a 'Set / clear legal hold' control directly on this page (currently only the field is visible, not editable).",
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
