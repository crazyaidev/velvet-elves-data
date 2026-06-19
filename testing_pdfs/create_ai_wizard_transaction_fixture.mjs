import fs from 'fs'

const output = 'C:/Projects/velvet-elves-data/ai_wizard_transaction_test_fixture.pdf'

const pageWidth = 612
const pageHeight = 792
const marginX = 50
const topY = 744
const bottomY = 54
const maxWidth = pageWidth - marginX * 2

const title = 'REAL ESTATE PURCHASE AGREEMENT'
const subtitle = 'AI Wizard Transaction Test Fixture - Not For Real Transaction Use'

const sections = [
  {
    heading: '1.0 SELLER INFORMATION',
    rows: [
      ['Seller(s)', 'Avery Morgan and Priya Morgan'],
      ['Marital status', 'Married'],
      ['Current address', '9821 Lakeshore Drive, Westerville, OH 43082'],
      ['Home phone', '614-555-6677'],
      ['Work phone', '614-555-6678'],
      ['Email', 'avery.morgan@minafter.com; priya.morgan@minafter.com'],
    ],
  },
  {
    heading: '1.1 BUYER INFORMATION',
    rows: [
      ['Buyer(s)', 'Jordan Ellis and Maya Ellis'],
      ['Marital status', 'Married'],
      ['Current address', '1189 Maple Crest Drive, Dublin, OH 43017'],
      ['Home phone', '614-555-8899'],
      ['Work phone', '614-555-9900'],
      ['Email', 'jordan.ellis@minafter.com; maya.ellis@minafter.com'],
    ],
  },
  {
    heading: '2.0 PROPERTY',
    rows: [
      ['Property address', '4567 Meadowridge Avenue'],
      ['City, state, ZIP', 'Boardman, OH 44512'],
      ['County', 'Mahoning'],
      ['Permanent parcel / tax ID', '41-12345-678-000'],
      ['Also included', 'Kitchen appliances, washer, dryer, window blinds, ceiling fans'],
      ['Not included', "Seller's personal furniture, garage workbench, outdoor shed"],
    ],
  },
  {
    heading: '3.0 PRICE AND FINANCING',
    rows: [
      ['Purchase price', '$342,500.00'],
      ['Earnest money deposit', '$7,500.00, payable to escrow within 3 days of acceptance'],
      ['Anticipated down payment', '$35,000.00'],
      ['Anticipated loan amount', '$300,000.00'],
      ['Financing type', 'Conventional mortgage'],
      ['Owner occupancy', 'Buyer intends to occupy the property as a primary residence'],
    ],
  },
  {
    heading: '4.0 FINANCING CONTINGENCY',
    paragraphs: [
      'Buyer shall make written loan application within five (5) calendar days after the Contract Acceptance Date. Buyer shall obtain loan approval on or before July 24, 2026. If Buyer cannot obtain loan approval despite good-faith efforts, Seller may extend the deadline in writing or the agreement may be terminated according to the earnest money provisions.',
      'The lender-ordered appraisal is expected on or before July 31, 2026. Buyer shall provide evidence of homeowner insurance commitment on or before August 4, 2026.',
    ],
  },
  {
    heading: '5.0 CLOSING AND ESCROW',
    rows: [
      ['Escrow / title company', 'Reliable Title & Escrow, Inc.'],
      ['Title contact', 'Elena Ruiz'],
      ['Title email', 'elena.ruiz@minafter.com'],
      ['Title phone', '330-555-4100'],
      ['Closing mode', 'Title / escrow closing'],
      ['Title ordered by', 'Seller'],
      ['Contract acceptance date', 'July 1, 2026'],
      ['Closing date', 'August 14, 2026'],
      ['Possession date', 'August 16, 2026'],
      ['Possession time', '5:00 PM'],
      ['Holdover rent', '$150.00 per day after possession date'],
    ],
  },
  {
    heading: '6.0 TITLE, PRORATIONS, AND CHARGES',
    paragraphs: [
      'Seller shall convey marketable and insurable title by general warranty deed, free and clear of liens except permitted exceptions of record. Seller shall pay the title exam, owner title policy premium, deed preparation, lien discharge costs, transfer tax, conveyance fees, and public authority inspection certificates required of Seller.',
      'Buyer shall pay costs incident to Buyer obtaining financing, the lender policy, deed and mortgage recording fees, inspection costs requested by Buyer, and any mortgage location survey required by the lender.',
    ],
  },
  {
    heading: '7.0 HOME WARRANTY AND HOA',
    rows: [
      ['Home warranty', 'Included'],
      ['Warranty ordered by', 'Seller'],
      ['Warranty provider', 'SafeNest Home Warranty'],
      ['Warranty email', 'safenest.support@minafter.com'],
      ['HOA', 'Oak Ridge Homeowners Association'],
      ['HOA document delivery', 'Seller shall deliver HOA documents within seven (7) days of acceptance'],
      ['HOA document deadline', 'July 8, 2026'],
    ],
  },
  {
    heading: '8.0 CONDITION OF PROPERTY AND INSPECTION',
    paragraphs: [
      'Buyer acknowledges that Buyer has been advised to engage, at Buyer expense, a professional property inspector to inspect the property and improvements. Buyer will have a home inspection.',
      'The general home inspection must be completed on or before July 8, 2026. Buyer shall approve, disapprove, or request repairs in writing no later than July 10, 2026. If the inspection results are not satisfactory and the parties do not reach a written resolution within the time specified, escrow shall return the earnest money deposit to Buyer and this agreement shall become null and void.',
    ],
  },
  {
    heading: '9.0 ADDITIONAL CONTINGENCIES',
    rows: [
      ['Survey review', 'Buyer may review a survey or mortgage location survey on or before July 12, 2026'],
      ['Final walk-through', 'Buyer may complete a final walk-through on or before August 13, 2026'],
      ['Lead-based paint', 'Disclosure required because the home was built before 1978'],
    ],
  },
  {
    heading: '10.0 CONTACT DIRECTORY ADDENDUM',
    rows: [
      ["Listing agent", 'Nora Patel, North Coast Realty, nora.patel@minafter.com, 330-555-1201'],
      ["Buyer's agent", 'Luis Romero, MetroKey Realty, luis.romero@minafter.com, 614-555-2210'],
      ['Loan officer', 'Tessa Grant, Buckeye Home Loans, tessa.grant@minafter.com, 614-555-3109'],
      ['Title / escrow rep', 'Elena Ruiz, Reliable Title & Escrow, Inc., elena.ruiz@minafter.com, 330-555-4100'],
      ['Closing attorney', 'Marcus Lee, Lee & Chen Law, marcus.lee@minafter.com, 330-555-7788'],
      ['Inspector', 'Owen Brooks, ClearView Inspections, owen.brooks@minafter.com, 330-555-8822'],
      ['Appraiser', 'Riley Hayes, Mahoning Appraisal Group, riley.hayes@minafter.com, 330-555-9920'],
    ],
  },
  {
    heading: '11.0 DATE SUMMARY FOR TESTING',
    rows: [
      ['Contract acceptance date', 'July 1, 2026'],
      ['Earnest money due', 'July 4, 2026'],
      ['Loan application due', 'July 6, 2026'],
      ['Inspection deadline', 'July 8, 2026'],
      ['HOA documents deadline', 'July 8, 2026'],
      ['Inspection response deadline', 'July 10, 2026'],
      ['Survey review deadline', 'July 12, 2026'],
      ['Financing deadline', 'July 24, 2026'],
      ['Appraisal expected date', 'July 31, 2026'],
      ['Insurance binder due', 'August 4, 2026'],
      ['Final walk-through', 'August 13, 2026'],
      ['Closing date', 'August 14, 2026'],
      ['Possession date', 'August 16, 2026'],
    ],
  },
  {
    heading: '12.0 BINDING AGREEMENT',
    paragraphs: [
      'Acceptance of this offer and any attached addenda shall create a legal agreement binding on Buyer and Seller and their heirs, executors, administrators, successors, and assigns. All amendments, addenda, and other alterations must be in writing, dated, and signed by both Buyer and Seller.',
      'This fixture intentionally leaves the original signature section unsigned. Use it to test the AI wizard signature review, e-signature queue decision, Active Transactions card, and transaction detail workspace.',
    ],
  },
]

function escapePdfText(text) {
  return text
    .replaceAll('\\', '\\\\')
    .replaceAll('(', '\\(')
    .replaceAll(')', '\\)')
}

function widthOf(text, size) {
  let width = 0
  for (const char of text) {
    if (char === ' ') width += 0.28
    else if ('ilI.,;:!|[]'.includes(char)) width += 0.24
    else if ('mwMW'.includes(char)) width += 0.82
    else if ('ABCDEFGHJKLMNOPQRSTUVWXYZ'.includes(char)) width += 0.63
    else if ('0123456789'.includes(char)) width += 0.52
    else width += 0.5
  }
  return width * size
}

function wrapText(text, size, width) {
  const words = text.split(/\s+/).filter(Boolean)
  const lines = []
  let line = ''

  for (const word of words) {
    const candidate = line ? `${line} ${word}` : word
    if (line && widthOf(candidate, size) > width) {
      lines.push(line)
      line = word
    } else {
      line = candidate
    }
  }

  if (line) lines.push(line)
  return lines
}

const pages = []
let current = []
let y = topY
let pageNo = 0

function addRaw(raw) {
  current.push(raw)
}

function addText(text, x, yPos, size = 9.4, font = 'F1') {
  addRaw(`BT /${font} ${size.toFixed(2)} Tf ${x.toFixed(2)} ${yPos.toFixed(2)} Td (${escapePdfText(text)}) Tj ET`)
}

function addRule(x1, y1, x2, y2, width = 0.7) {
  addRaw(`${width.toFixed(2)} w ${x1.toFixed(2)} ${y1.toFixed(2)} m ${x2.toFixed(2)} ${y2.toFixed(2)} l S`)
}

function addHeader() {
  pageNo += 1
  const titleSize = pageNo === 1 ? 15 : 10.5
  const titleX = Math.max(marginX, (pageWidth - widthOf(title, titleSize)) / 2)
  addText(title, titleX, topY, titleSize, 'F2')
  const subSize = 8.5
  const subX = Math.max(marginX, (pageWidth - widthOf(subtitle, subSize)) / 2)
  addText(subtitle, subX, topY - 15, subSize, 'F1')
  addText(`Page ${pageNo}`, pageWidth - marginX - 32, bottomY - 20, 8, 'F1')
  y = topY - 36
}

function newPage() {
  pages.push(current.join('\n'))
  current = []
  addHeader()
}

function ensure(space) {
  if (y - space < bottomY) newPage()
}

function addWrapped(text, options = {}) {
  const size = options.size ?? 9.4
  const font = options.font ?? 'F1'
  const x = options.x ?? marginX
  const width = options.width ?? maxWidth
  const lineHeight = options.lineHeight ?? 11.6
  const lines = wrapText(text, size, width)
  ensure(lines.length * lineHeight + (options.after ?? 4))
  for (const line of lines) {
    addText(line, x, y, size, font)
    y -= lineHeight
  }
  y -= options.after ?? 4
}

function addRow(label, value) {
  const labelWidth = 142
  const lines = wrapText(String(value), 9.2, maxWidth - labelWidth - 10)
  ensure(Math.max(lines.length, 1) * 11.2 + 3)
  addText(`${label}:`, marginX, y, 9.2, 'F2')
  for (let i = 0; i < lines.length; i += 1) {
    addText(lines[i], marginX + labelWidth, y - i * 11.2, 9.2, 'F1')
  }
  y -= Math.max(lines.length, 1) * 11.2 + 2
}

function addSection(section) {
  ensure(28)
  addWrapped(section.heading, { size: 9.8, font: 'F2', lineHeight: 12, after: 2 })
  if (section.rows) {
    for (const [label, value] of section.rows) addRow(label, value)
  }
  if (section.paragraphs) {
    for (const paragraph of section.paragraphs) addWrapped(paragraph)
  }
  y -= 4
}

function addSignatureBlocks() {
  ensure(250)
  addWrapped('13.0 SIGNATURE SECTION', { size: 10, font: 'F2', after: 8 })
  addWrapped('Original signature marks were removed. Each signature and printed-name field below is an underlined blank space for testing unsigned-document handling.', { size: 9.2, after: 12 })

  const leftX = marginX
  const rightX = marginX + 300
  const lineLen = 210
  const rowGap = 42

  addText('BUYER(S) SIGNATURE', leftX, y, 9.2, 'F2')
  addText('PRINT NAME', rightX, y, 9.2, 'F2')
  y -= 22
  for (let i = 1; i <= 2; i += 1) {
    addText(`${i})`, leftX, y + 3, 9.2, 'F1')
    addRule(leftX + 18, y, leftX + lineLen, y, 0.8)
    addRule(rightX, y, rightX + lineLen, y, 0.8)
    y -= rowGap
  }
  addText('DATED:', leftX, y + 3, 9.2, 'F2')
  addRule(leftX + 44, y, leftX + 180, y, 0.8)
  addText('TIME:', rightX, y + 3, 9.2, 'F2')
  addRule(rightX + 38, y, rightX + 170, y, 0.8)
  y -= 46

  addText('SELLER(S) SIGNATURE', leftX, y, 9.2, 'F2')
  addText('PRINT NAME', rightX, y, 9.2, 'F2')
  y -= 22
  for (let i = 1; i <= 2; i += 1) {
    addText(`${i})`, leftX, y + 3, 9.2, 'F1')
    addRule(leftX + 18, y, leftX + lineLen, y, 0.8)
    addRule(rightX, y, rightX + lineLen, y, 0.8)
    y -= rowGap
  }
  addText('DATED:', leftX, y + 3, 9.2, 'F2')
  addRule(leftX + 44, y, leftX + 180, y, 0.8)
  addText('TIME:', rightX, y + 3, 9.2, 'F2')
  addRule(rightX + 38, y, rightX + 170, y, 0.8)
  y -= 30
}

addHeader()
for (const section of sections) addSection(section)
addSignatureBlocks()
pages.push(current.join('\n'))

const objects = []
function reserveObject() {
  objects.push(null)
  return objects.length
}
function addObject(content) {
  objects.push(content)
  return objects.length
}

const catalogId = reserveObject()
const pagesId = reserveObject()
const fontRegularId = addObject('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>')
const fontBoldId = addObject('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>')
const pageIds = []

for (const content of pages) {
  const length = Buffer.byteLength(content, 'latin1')
  const contentId = addObject(`<< /Length ${length} >>\nstream\n${content}\nendstream`)
  const pageId = addObject(`<< /Type /Page /Parent ${pagesId} 0 R /MediaBox [0 0 ${pageWidth} ${pageHeight}] /Resources << /Font << /F1 ${fontRegularId} 0 R /F2 ${fontBoldId} 0 R >> >> /Contents ${contentId} 0 R >>`)
  pageIds.push(pageId)
}

objects[catalogId - 1] = `<< /Type /Catalog /Pages ${pagesId} 0 R >>`
objects[pagesId - 1] = `<< /Type /Pages /Kids [${pageIds.map((id) => `${id} 0 R`).join(' ')}] /Count ${pageIds.length} >>`

let pdf = '%PDF-1.4\n%\xE2\xE3\xCF\xD3\n'
const offsets = [0]
for (let i = 0; i < objects.length; i += 1) {
  offsets.push(Buffer.byteLength(pdf, 'latin1'))
  pdf += `${i + 1} 0 obj\n${objects[i]}\nendobj\n`
}
const xrefOffset = Buffer.byteLength(pdf, 'latin1')
pdf += `xref\n0 ${objects.length + 1}\n`
pdf += '0000000000 65535 f \n'
for (let i = 1; i < offsets.length; i += 1) {
  pdf += `${offsets[i].toString().padStart(10, '0')} 00000 n \n`
}
pdf += `trailer\n<< /Size ${objects.length + 1} /Root ${catalogId} 0 R >>\nstartxref\n${xrefOffset}\n%%EOF\n`

fs.writeFileSync(output, Buffer.from(pdf, 'latin1'))
console.log(`Wrote ${output} (${pages.length} pages)`)
