# Frontend UI Testing Guidelines

*Velvet Elves frontend (`velvet-elves-frontend`). Last reconciled with the test
setup: 2026-05-22.*

These are the conventions for writing UI tests in this project. They are
grounded in the stack that is actually configured, not aspirational tooling.

---

## 1. Stack & layout

- **Runner:** Vitest (`vite.config.ts` → `test` block; `environment: 'jsdom'`,
  `globals: true`, `setupFiles: ['./src/tests/setup.ts']`, `testTimeout: 20000`).
- **Rendering:** `@testing-library/react` + `@testing-library/jest-dom`
  matchers + `@testing-library/user-event`.
- **Network mocking:** MSW (`msw`). The server is started in
  `src/tests/setup.ts` (`server.listen` / `resetHandlers` after each test /
  `close` after all). Handlers and shared mock fixtures live in
  `src/tests/mocks/handlers.ts`.
- **Layout:**
  - `src/tests/unit/` — component/unit tests (`*.test.tsx`).
  - `src/tests/integration/` — flows that render larger trees (`*.test.tsx`).
  - `src/tests/mocks/` — MSW `handlers.ts`, `server.ts`, shared fixtures.
  - `src/tests/setup.ts` — global setup (jest-dom, MSW, `matchMedia` shim).

### Commands

```bash
npx vitest run                              # full suite, once
npx vitest run src/tests/unit/Foo.test.tsx  # one file
npx vitest                                  # watch mode
npm run test:coverage                       # coverage
```

Type-check and lint are separate gates and must also pass:

```bash
npx tsc --noEmit -p tsconfig.app.json
npx eslint <changed files>
```

---

## 2. When to write a UI test (and when not)

Write a test when the component has **logic the eye can't verify from the diff**:

- conditional rendering (loading / error / empty / populated),
- derived/computed display values (status pills, day counts, tone selection),
- enforcement rules (a Submit button that must stay disabled until valid),
- role-aware or permission-aware rendering,
- accessibility contracts (an explicit action link, an `aria-label`).

Don't write a test for pure static markup, or to assert exact Tailwind class
strings as a proxy for "it looks right" — that couples the test to styling and
breaks on every restyle. Visual correctness is verified by running the app, not
by snapshotting class names.

---

## 3. The four states are mandatory

Any component that consumes data must be tested in all four states it can be in:

1. **Loading** — skeleton/placeholder renders, no crash.
2. **Error** — error affordance + retry renders.
3. **Empty** — the empty-state copy/CTA renders (not a blank box).
4. **Populated** — the real content renders with correct derived values.

Most regressions in this codebase are an empty/loading branch that renders
`undefined`, a broken `mailto:`, or a `0` where an em-dash was meant. Cover the
branches.

---

## 4. Never compute expectations from `new Date()`

Day-count and "closing soon" logic (`daysUntil`, `days_to_close`, the FSBO
status chip, deadline badges) is time-relative. A test that hardcodes
"3 days" against a fixed fixture date will pass today and fail next week.

- Feed **explicit** dates into the component/fixture and assert the **derived
  label**, or
- freeze time with `vi.setSystemTime(new Date('2026-05-22T12:00:00Z'))` in a
  `beforeEach` and restore with `vi.useRealTimers()` in `afterEach`.

Don't assert against a value that depends on the wall clock at test-run time.

---

## 5. Mock at the right layer

- **Prefer MSW** (network layer) for anything that goes through `apiFetch` /
  `useApiFetch` / React Query. Add/extend handlers in
  `src/tests/mocks/handlers.ts` so the data shape stays centralized and reused.
- **Mock a hook with `vi.mock`** only when the hook has side effects you don't
  want to exercise (e.g. `useUploadDocument`'s mutation, `useToast`) and the
  test is about the component's own logic, not the network round-trip. Example
  from `FsboUploadModal.test.tsx`:

  ```ts
  vi.mock('@/hooks/useDocuments', () => ({
    useUploadDocument: () => ({ mutateAsync: vi.fn() }),
  }))
  vi.mock('@/hooks/use-toast', () => ({ useToast: () => ({ toast: vi.fn() }) }))
  ```

- Reuse the shared fixtures (`mockUser`, `mockTransaction`, …) from the mocks
  module rather than re-declaring objects per test.

---

## 6. Provide the providers a component actually needs

A component that calls a context hook will throw if rendered without its
provider. This is the single most common cause of red tests here. For example,
anything reaching `useAuth` (directly, or transitively via `useApiFetch` /
`useCurrentTenant`) must be wrapped in the auth provider, and anything calling
`useFsboShare` needs `FsboShareProvider`, etc.

- Trace the hook chain before rendering. `Component → useCurrentTenant →
  useApiFetch → useAuth` means you need the AuthProvider, even though the
  component never names `useAuth`.
- Build a small `renderWithProviders` helper (QueryClientProvider +
  AuthProvider + MemoryRouter + any feature context) and use it consistently,
  rather than hand-wrapping per test.
- Routing-aware components need `MemoryRouter` (see `AdminActionQueue.test.tsx`
  for the pattern). Seed the URL with `initialEntries` when the component reads
  route params.

A bare `render(<Component />)` for a context-dependent component is a bug in the
test, not the component.

---

## 7. Query the way a user perceives the UI

Priority order for queries:

1. `getByRole` (with `name`) — buttons, links, headings, listitems.
2. `getByLabelText` / `getByPlaceholderText` — form fields.
3. `getByText` — visible copy.
4. `getByTestId` — last resort, only when nothing above works.

Avoid `container.querySelector('.some-class')` and DOM-structure traversal —
they couple tests to markup and styling. Assert on roles, labels, and text.

Accessibility is part of the contract: when a card must expose an explicit
action (per the project's "no whole-card click target" rule), assert the
`role="link"`/`role="button"` with its accessible name and `href`/handler — not
a click on the card wrapper.

---

## 8. Radix primitives (Dialog, Select) are portaled

`@/components/ui/*` wrap Radix. Two consequences for tests:

- **Portals render outside the component subtree** — query with `screen.*`
  (which searches `document.body`), not within a scoped `container`.
- **Radix `Select` is pointer-driven and portaled.** Driving it through the
  full open→click-option flow in jsdom is brittle. Prefer to:
  - pass a pre-selected value (e.g. `defaultPropertyId`) and assert the
    visible trigger value, and
  - assert the **enforcement outcome** (button stays disabled until all
    required fields are set) rather than scripting every dropdown interaction.

  See `FsboUploadModal.test.tsx`: it verifies the Upload button is disabled with
  no doc_type/file, stays disabled when only a file is attached, and that the
  property label renders — without fighting the Radix listbox.
- A `DialogContent` warning about a missing `Description`/`aria-describedby` is
  noise in tests; it does not fail the assertion.

---

## 9. Respect data boundaries in assertions

- **PII / encrypted fields:** UI fed by the backend receives already-decrypted
  values; if you seed a fixture, seed the **plain** value the component will
  render. Don't assert on ciphertext.
- **Role/portal isolation:** when testing a customer-facing surface (FSBO,
  Client, Vendor), assert the **absence** of internal affordances too — e.g. no
  internal task queue, no other parties' data, no internal notes. A portal test
  that only checks the happy path can miss a leak.

---

## 10. FSBO-specific patterns

- **Status/tone logic** (`fsboPropertyStatus`, the topbar chip, deadline
  badges): feed explicit `missing_docs_count` + `closing_date` and assert the
  label and tone, across the red/amber/green boundaries. Use frozen time (§4).
- **Document board:** assert the five-column mapping (Missing / In progress /
  Uploaded / Verified / Complete) and especially the Verified-vs-Complete split
  (approved-but-signature-pending → Verified). Backed by
  `classify_document_board_state` semantics.
- **Upload modal:** lock the required-fields rule (property + doc_type + file)
  so a silent default can't regress.
- **Unread dot:** assert the dot renders for `seen === false` and is absent for
  `seen === true`; the mark-seen mutation can be mocked (§5).
- **Boundary notice:** assert it renders exactly **once** per page (the shell
  footer owns it) — a duplicate boundary notice was a real regression.

---

## 11. Common pitfalls (seen in this repo)

- **Missing provider** → `useX must be used within YProvider`. Fix the test
  wrapper, not the component (§6).
- **Stale component vs. test** → a shared display component is updated but its
  unit test still asserts the old copy. Update the test in the same change as
  the component.
- **Wall-clock assertions** → time-relative values asserted against `new Date()`
  (§4).
- **Class-name assertions** → break on restyle; assert behavior/role/text
  instead (§7, §2).
- **Over-mocking** → mocking the network *and* the hook *and* the context for
  one component usually means the test no longer verifies anything real; mock
  the minimum.

---

## 12. Minimum bar before calling a UI change done

1. `npx tsc --noEmit -p tsconfig.app.json` — clean.
2. `npx eslint <changed files>` — clean.
3. Relevant `npx vitest run <file>` — green, covering the four states (§3).
4. The feature exercised in a browser for golden path + an edge case (type-check
   and tests verify code correctness, not feature correctness).
5. If you couldn't verify it in a browser, say so explicitly rather than
   claiming success.
