import { readFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const API = 'https://api.stage.velvetelves.com'
const EMAIL = process.env.QA_EMAIL || 'crazyaidev20500519@gmail.com'
const PASSWORD = process.env.QA_PASSWORD || 'QWE!@#asd234'
const seed = JSON.parse(readFileSync(path.join(__dirname, 'artifacts_feature14_32/seed.json'), 'utf8'))

const form = new URLSearchParams({ username: EMAIL, password: PASSWORD }).toString()
const auth = await fetch(`${API}/api/v1/users/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: form,
}).then((r) => r.json())
const token = auth.access_token
for (const key of ['pine', 'cedar', 'noContract']) {
  const id = seed.files[key].id
  const res = await fetch(`${API}/api/v1/transactions/${id}/automation`, {
    method: 'PUT',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ posture: 'assisted' }),
  })
  console.log(key, res.status, (await res.text()).slice(0, 180))
}
