/**
 * Diagnose Needs You load: API status/timing + layout height.
 */
import { createRequire } from 'module'
import { mkdirSync, writeFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const require = createRequire('c:/Projects/velvet-elves-frontend/package.json')
const { chromium } = require('playwright')

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const OUT = path.join(__dirname, 'artifacts_2026-08-13_diag')
mkdirSync(OUT, { recursive: true })

async function main() {
  const browser = await chromium.launch({ channel: 'chrome', headless: false, args: ['--start-maximized'] })
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } })
  const page = await context.newPage()
  const responses = []

  page.on('response', async (res) => {
    const url = res.url()
    if (!url.includes('/automation/')) return
    const rec = { url, status: res.status(), ok: res.ok(), method: res.request().method() }
    try {
      if (url.includes('/needs-you') && !url.includes('/approve') && !url.includes('/send')) {
        const json = await res.json()
        rec.counts = json?.counts
        rec.n = json?.items?.length
        rec.kinds = {}
        for (const i of json?.items || []) rec.kinds[i.kind] = (rec.kinds[i.kind] || 0) + 1
        rec.sample = (json?.items || []).slice(0, 3).map((i) => ({ kind: i.kind, title: i.title, tx: i.transaction_id }))
        writeFileSync(path.join(OUT, 'needs_you_api.json'), JSON.stringify(json, null, 2))
      }
    } catch (err) {
      rec.parseError = err.message
    }
    responses.push(rec)
    console.log('RESP', rec.status, rec.method, rec.url, rec.counts || rec.parseError || '')
  })

  await page.goto('http://localhost:5173/login', { waitUntil: 'domcontentloaded' })
  await page.locator('#login-email').fill('shyna.elene@minafter.com')
  await page.locator('#login-password').fill('QWE!@#asd234')
  await page.getByRole('button', { name: /sign in/i }).click()
  await page.waitForURL((u) => !u.pathname.includes('/login'), { timeout: 20000 })
  await page.waitForTimeout(800)

  const started = Date.now()
  const waitResp = page.waitForResponse(
    (r) => r.url().includes('/api/v1/automation/needs-you') && !r.url().includes('/approve') && !r.url().includes('/send'),
    { timeout: 90000 },
  )
  await page.goto('http://localhost:5173/needs-you', { waitUntil: 'domcontentloaded' })
  let respInfo = { error: 'none' }
  try {
    const r = await waitResp
    respInfo = { status: r.status(), ok: r.ok(), ms: Date.now() - started, url: r.url() }
  } catch (err) {
    respInfo = { error: err.message, ms: Date.now() - started }
  }
  console.log('waitForResponse', respInfo)
  await page.waitForTimeout(2000)
  await page.screenshot({ path: path.join(OUT, 'diag.png') })

  const layout = await page.evaluate(() => {
    const main = document.getElementById('main-content')
    const pageRoot = main?.firstElementChild?.nextElementSibling || main?.querySelector(':scope > div')
    const header = [...document.querySelectorAll('header')].find((h) => /Needs You/.test(h.innerText || ''))
    const body = header?.nextElementSibling
    const rect = (el) => {
      if (!el) return null
      const r = el.getBoundingClientRect()
      return { tag: el.tagName, class: el.className?.toString?.().slice(0, 120), w: Math.round(r.width), h: Math.round(r.height), y: Math.round(r.y) }
    }
    return {
      main: rect(main),
      pageRoot: rect(pageRoot),
      header: rect(header),
      body: rect(body),
      heading: document.querySelector('h1')?.innerText,
      hasWaiting: /waiting on you|Nothing needs you|ready to send|To handle|To review/i.test(document.body.innerText),
      skeleton: document.querySelectorAll('[class*="skeleton"]').length,
    }
  })

  const token = await page.evaluate(() => localStorage.getItem('token') || localStorage.getItem('access_token') || sessionStorage.getItem('token'))
  let keys = await page.evaluate(() => Object.keys(localStorage))
  console.log('storage keys', keys)
  console.log('layout', layout)

  writeFileSync(path.join(OUT, 'diag.json'), JSON.stringify({ respInfo, layout, responses, keys }, null, 2))
  await browser.close()
}

main().catch((e) => { console.error(e); process.exit(1) })
