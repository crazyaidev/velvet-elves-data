/** Minimal PDF fixtures for Jake TME E2E (PA + amendment). */
import { writeFileSync } from 'fs'
import path from 'path'

export function writePaPdf(outPath, { address, accept, close }) {
  writePdf(outPath, buildPdf([
    { heading: 'PURCHASE AGREEMENT', rows: [
      ['Property', address],
      ['Date of Acceptance', accept],
      ['Closing Date', close],
      ['Possession Date', 'October 16, 2026'],
      ['Purchase Price', '$425,000.00'],
    ]},
  ]))
}

export function writeAmendmentPdf(outPath, { newClose, fuzzy = false }) {
  const body = fuzzy
    ? 'Closing may occur on or about November 1, 2026, subject to lender approval and mutual agreement.'
    : `The Closing Date in the Purchase Agreement is hereby amended and changed to ${newClose}.`
  writePdf(outPath, buildPdf([
    { heading: 'AMENDMENT TO PURCHASE AGREEMENT', paragraphs: [body, 'All other terms remain unchanged.'] },
  ]))
}

function buildPdf(sections) {
  const pageWidth = 612
  const pageHeight = 792
  const marginX = 50
  let y = 744
  const lines = []
  const add = (text, size = 11, font = 'F1') => {
    lines.push(`BT /${font} ${size} Tf ${marginX} ${y} Td (${esc(text)}) Tj ET`)
    y -= size + 8
  }
  const esc = (s) => String(s).replace(/\\/g, '\\\\').replace(/\(/g, '\\(').replace(/\)/g, '\\)')
  for (const sec of sections) {
    add(sec.heading, 13, 'F2')
    for (const row of sec.rows || []) add(`${row[0]}: ${row[1]}`)
    for (const p of sec.paragraphs || []) {
      for (const chunk of p.match(/.{1,90}/g) || [p]) add(chunk)
    }
    y -= 10
  }
  return { content: lines.join('\n'), pageWidth, pageHeight }
}

function writePdf(outPath, { content, pageWidth, pageHeight }) {
  const objects = []
  const reserve = () => { objects.push(null); return objects.length }
  const addObj = (c) => { objects.push(c); return objects.length }
  const catalogId = reserve()
  const pagesId = reserve()
  const fontR = addObj('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>')
  const fontB = addObj('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>')
  const len = Buffer.byteLength(content, 'latin1')
  const contentId = addObj(`<< /Length ${len} >>\nstream\n${content}\nendstream`)
  const pageId = addObj(`<< /Type /Page /Parent ${pagesId} 0 R /MediaBox [0 0 ${pageWidth} ${pageHeight}] /Resources << /Font << /F1 ${fontR} 0 R /F2 ${fontB} 0 R >> >> /Contents ${contentId} 0 R >>`)
  objects[catalogId - 1] = `<< /Type /Catalog /Pages ${pagesId} 0 R >>`
  objects[pagesId - 1] = `<< /Type /Pages /Kids [${pageId} 0 R] /Count 1 >>`
  let pdf = '%PDF-1.4\n%\xE2\xE3\xCF\xD3\n'
  const offsets = [0]
  for (let i = 0; i < objects.length; i++) {
    offsets.push(Buffer.byteLength(pdf, 'latin1'))
    pdf += `${i + 1} 0 obj\n${objects[i]}\nendobj\n`
  }
  const xref = Buffer.byteLength(pdf, 'latin1')
  pdf += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`
  for (let i = 1; i < offsets.length; i++) pdf += `${offsets[i].toString().padStart(10, '0')} 00000 n \n`
  pdf += `trailer\n<< /Size ${objects.length + 1} /Root ${catalogId} 0 R >>\nstartxref\n${xref}\n%%EOF\n`
  writeFileSync(outPath, Buffer.from(pdf, 'latin1'))
}

if (process.argv[1] && process.argv[1].endsWith('jake_tme_pdf_fixtures.mjs')) {
  const out = path.join(path.dirname(process.argv[1]), 'artifacts_jake_tme_e2e')
  writePaPdf(path.join(out, 'pa.pdf'), { address: 'Test', accept: 'September 1, 2026', close: 'October 15, 2026' })
  writeAmendmentPdf(path.join(out, 'amd.pdf'), { newClose: 'November 1, 2026' })
  console.log('wrote pa.pdf amd.pdf')
}
