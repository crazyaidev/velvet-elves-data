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


TARGET_BUILDERS = {
    "requirements": create_requirements_doc,
    "milestones": create_milestones_doc,
    "design-feedback": create_design_feedback_doc,
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
