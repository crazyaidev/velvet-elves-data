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
    lines.append("**Last Updated:** April 15, 2026  ")
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
    lines.append("- **Team Lead or Admin** — needed to see the Delete button on transactions, the admin-only Task Templates pages, and the Deletion Queue on the Documents page.")
    lines.append("- **Attorney** — loads the attorney-specific workspace at /transactions.")
    lines.append("- **FSBO Customer** — verifies the FSBO sidebar layout.")
    lines.append("- **Admin with a known user ID** — needed only for the direct user-detail link at /admin/users/<userId>.")
    lines.append("")
    lines.append("### Suggested order of testing")
    lines.append("")
    lines.append("1. Public pages and sign-in / sign-up")
    lines.append("2. Onboarding and the first-time tutorial")
    lines.append("3. Standard Agent or Elf workflow (dashboard, new transaction, transactions list, documents)")
    lines.append("4. Team Lead or Admin extras (delete permission, task templates, deletion queue)")
    lines.append("5. Attorney workspace")
    lines.append("6. FSBO-customer sidebar")
    lines.append("7. Direct links and error pages")
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
