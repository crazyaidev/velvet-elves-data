import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const output = path.join(__dirname, 'willowbrook_purchase_agreement.pdf')

const pageWidth = 612
const pageHeight = 792
const marginX = 50
const topY = 744
const bottomY = 54
const maxWidth = pageWidth - marginX * 2

const title = 'REAL ESTATE PURCHASE AGREEMENT'
const subtitle = 'Demo video fixture — 1842 Willowbrook Lane, Carmel, IN — not for a real closing'

const sections = [
  {
    heading: '1.0 SELLER INFORMATION',
    rows: [
      ['Seller', 'Harper Devlin'],
      ['Marital status', 'Single'],
      ['Current address', '2201 Meridian Street, Indianapolis, IN 46202'],
      ['Home phone', '317-555-0142'],
      ['Email', 'happydev0705@gmail.com'],
    ],
  },
  {
    heading: '1.1 BUYER INFORMATION',
    rows: [
      ['Buyer', 'James L. Selman'],
      ['Marital status', 'Single'],
      ['Current address', '891 Keystone Parkway, Carmel, IN 46032'],
      ['Home phone', '317-555-0188'],
      ['Email', 'james.l.selman13@gmail.com'],
    ],
  },
  {
    heading: '2.0 PROPERTY',
    rows: [
      ['Property address', '1842 Willowbrook Lane'],
      ['City, state, ZIP', 'Carmel, IN 46032'],
      ['County', 'Hamilton'],
      ['Permanent parcel / tax ID', '29-10-15-003-012.000-001'],
      ['Legal description', 'Lot 12, Willowbrook Estates, Section 3, Hamilton County, Indiana'],
      ['Also included', 'Kitchen appliances, washer, dryer, window treatments, garage door openers'],
      ['Not included', "Seller's dining set, workshop tools, potted plants"],
      ['Match key', 'WILLOWBROOK-1842-DEMO'],
    ],
  },
  {
    heading: '3.0 PRICE AND FINANCING',
    rows: [
      ['Purchase price', '$485,000.00'],
      ['Earnest money deposit', '$10,000.00, payable to escrow within 3 days of acceptance'],
      ['Anticipated down payment', '$97,000.00'],
      ['Anticipated loan amount', '$388,000.00'],
      ['Financing type', 'Conventional mortgage'],
      ['Owner occupancy', 'Buyer intends to occupy the property as a primary residence'],
    ],
  },
  {
    heading: '4.0 FINANCING CONTINGENCY',
    paragraphs: [
      'Buyer shall make written loan application within five (5) calendar days after the Contract Acceptance Date. Buyer shall obtain loan approval on or before September 5, 2026. If Buyer cannot obtain loan approval despite good-faith efforts, Seller may extend the deadline in writing or the agreement may be terminated according to the earnest money provisions.',
      'The lender-ordered appraisal is expected on or before September 8, 2026. Buyer shall provide evidence of homeowner insurance commitment on or before September 12, 2026.',
    ],
  },
  {
    heading: '5.0 CLOSING AND ESCROW',
    rows: [
      ['Escrow / title company', 'Hamilton Title & Escrow'],
      ['Title contact', 'James L. Selman (test mailbox)'],
      ['Title email', 'james.l.selman13@gmail.com'],
      ['Title phone', '317-555-0188'],
      ['Closing mode', 'Title / escrow closing'],
      ['Title ordered by', 'Seller'],
      ['Contract acceptance date', 'August 8, 2026'],
      ['Closing date', 'September 25, 2026'],
      ['Possession date', 'September 25, 2026'],
      ['Possession time', '5:00 PM'],
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
      ['HOA', 'Willowbrook Estates Homeowners Association'],
      ['HOA document delivery', 'Seller shall deliver HOA documents within seven (7) days of acceptance'],
      ['HOA document deadline', 'August 15, 2026'],
    ],
  },
  {
    heading: '8.0 CONDITION OF PROPERTY AND INSPECTION',
    paragraphs: [
      'Buyer acknowledges that Buyer has been advised to engage, at Buyer expense, a professional property inspector to inspect the property and improvements. Buyer will have a home inspection.',
      'The general home inspection must be completed on or before August 22, 2026. Buyer shall approve, disapprove, or request repairs in writing no later than August 24, 2026. If the inspection results are not satisfactory and the parties do not reach a written resolution within the time specified, escrow shall return the earnest money deposit to Buyer and this agreement shall become null and void.',
    ],
  },
  {
    heading: '9.0 ADDITIONAL CONTINGENCIES',
    rows: [
      ['Survey review', 'Buyer may review a survey or mortgage location survey on or before August 20, 2026'],
      ['Final walk-through', 'Buyer may complete a final walk-through on or before September 24, 2026'],
      ['Lead-based paint', 'No lead-based paint disclosure required because the home was built in 2004'],
    ],
  },
  {
    heading: '10.0 CONTACT DIRECTORY',
    rows: [
      ['Listing agent', 'Devin Forrester, Forrester Realty, developer.defi0782@gmail.com, 317-555-0210'],
      ["Buyer's agent", 'Morgan Goto, Higher Path Realty, gotohigher0705@gmail.com, 317-555-0330'],
      ['Loan officer', 'Harper Devlin (test mailbox), First River Lending, happydev0705@gmail.com, 317-555-0142'],
      ['Title / escrow rep', 'James L. Selman (test mailbox), Hamilton Title & Escrow, james.l.selman13@gmail.com, 317-555-0188'],
    ],
  },
  {
    heading: '11.0 DATE SUMMARY FOR TESTING',
    rows: [
      ['Contract acceptance date', 'August 8, 2026'],
      ['Earnest money due', 'August 11, 2026'],
      ['Loan application due', 'August 13, 2026'],
      ['HOA documents deadline', 'August 15, 2026'],
      ['Survey review deadline', 'August 20, 2026'],
      ['Inspection deadline', 'August 22, 2026'],
      ['Inspection response deadline', 'August 24, 2026'],
      ['Financing deadline', 'September 5, 2026'],
      ['Appraisal expected date', 'September 8, 2026'],
      ['Insurance binder due', 'September 12, 2026'],
      ['Final walk-through', 'September 24, 2026'],
      ['Closing date', 'September 25, 2026'],
      ['Possession date', 'September 25, 2026'],
    ],
  },
  {
    heading: '12.0 BINDING AGREEMENT',
    paragraphs: [
      'Acceptance of this offer and any attached addenda shall create a legal agreement binding on Buyer and Seller and their heirs, executors, administrators, successors, and assigns. All amendments, addenda, and other alterations must be in writing, dated, and signed by both Buyer and Seller.',
      'This fixture is unsigned on purpose so the AI wizard can be tested end to end. Contact emails are mailboxes controlled by the tester for Gmail receipt checks.',
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
  const subSize = 8.2
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
  addWrapped(
    'Original signature marks were removed. Each signature and printed-name field below is an underlined blank space for testing unsigned-document handling.',
    { size: 9.2, after: 12 },
  )

  const leftX = marginX
  const rightX = marginX + 300
  const lineLen = 210
  const rowGap = 42

  addText('BUYER SIGNATURE', leftX, y, 9.2, 'F2')
  addText('PRINT NAME', rightX, y, 9.2, 'F2')
  y -= 22
  addText('1)', leftX, y + 3, 9.2, 'F1')
  addRule(leftX + 18, y, leftX + lineLen, y, 0.8)
  addRule(rightX, y, rightX + lineLen, y, 0.8)
  y -= rowGap
  addText('DATED:', leftX, y + 3, 9.2, 'F2')
  addRule(leftX + 44, y, leftX + 180, y, 0.8)
  addText('TIME:', rightX, y + 3, 9.2, 'F2')
  addRule(rightX + 38, y, rightX + 170, y, 0.8)
  y -= 46

  addText('SELLER SIGNATURE', leftX, y, 9.2, 'F2')
  addText('PRINT NAME', rightX, y, 9.2, 'F2')
  y -= 22
  addText('1)', leftX, y + 3, 9.2, 'F1')
  addRule(leftX + 18, y, leftX + lineLen, y, 0.8)
  addRule(rightX, y, rightX + lineLen, y, 0.8)
  y -= rowGap
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
const fontRegularId = addObject(
  '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>',
)
const fontBoldId = addObject(
  '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>',
)
const pageIds = []

for (const content of pages) {
  const length = Buffer.byteLength(content, 'latin1')
  const contentId = addObject(`<< /Length ${length} >>\nstream\n${content}\nendstream`)
  const pageId = addObject(
    `<< /Type /Page /Parent ${pagesId} 0 R /MediaBox [0 0 ${pageWidth} ${pageHeight}] /Resources << /Font << /F1 ${fontRegularId} 0 R /F2 ${fontBoldId} 0 R >> >> /Contents ${contentId} 0 R >>`,
  )
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
