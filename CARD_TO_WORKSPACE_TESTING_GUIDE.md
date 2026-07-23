# Testing Guide — Deal card and the Transaction Detail page

> For testers: everything below is done with the mouse, in the app, with no
> developer tools. Updated 2026-07-22 after the Transaction Detail page was
> redesigned. Companion to TRANSACTION_WORKSPACE_TESTING_GUIDE.md.

## What changed, in one paragraph

The expanded deal card on Active Transactions is unchanged — tasks, key
dates, contacts, invoices, and the footer actions all still work exactly
where they always were. What changed is the **Transaction Detail page** (the
page you get when you click a deal's name, its expand icon, or "Open
workspace"). It was rebuilt to look and behave like a normal record page: it
opens on an Overview of where the deal stands, the sections sit in one clean
row of tabs, and the AI assistant is a panel you open when you want it
instead of taking half the screen.

---

## 1. The list page should feel identical

Nothing here should have changed. If any of it behaves differently, that is a
bug worth reporting.

1. Expand a card with the ⌄ chevron. You get the three columns: **Tasks**,
   **Key Dates**, **Contacts**.
2. Tick a task checkbox — it completes, with an **Undo** in the toast.
3. Click a Key Date row (e.g. "Inspection Response") — the small date popover
   opens and saves.
4. Expand a contact — phone and email are one click each; "+ Add" on a group
   opens the Add Contact form.
5. The footer still offers: Open workspace · View/Add Docs · Print · History ·
   Comms · Client access · Client Q&A · Invoice · Delete (Team Lead / Admin).
6. Filters, sort, search, Export CSV / Excel / Print Report all behave as
   before.

---

## 2. The Transaction Detail page — ten-minute walkthrough

Open any deal (click its name on a card, or the ⤢ icon).

1. **You land on Overview.** Four panels: **Needs you**, **Key dates**,
   **Progress**, **People**. This is the page telling you where the deal
   stands before asking you to change anything.
2. **Needs you** lists what is overdue or due today. Click a row — it takes
   you to the Tasks tab with that task highlighted. If a deal is missing
   documents, a line at the bottom says how many and takes you to Documents.
3. **Key dates** shows the seven tracking dates as colored chips (red =
   overdue, green = set, plain = not set yet). Clicking one takes you to
   Timeline, where dates are edited.
4. **The header** carries the deal name, its stage, and the facts that decide
   urgency: address, days to close, overdue count, price. These must match
   what the card on the list says for the same deal.
5. **Tabs**: Overview · Timeline · Tasks · Documents · People · Billing ·
   Activity (plus Email). There is no longer a separate "Compliance" tab —
   open **Documents** and you will see two views, **Files** and **Checklist**.
   The checklist is exactly what Compliance used to be.
6. **Timeline** shows the tracking-date chips at the top, then the plan. Click
   "Inspection Response" and set a date. Now click **Closing Date**: you get a
   preview of every deadline that moves before you apply it, then Undo.
7. **Documents › Checklist**: attach, waive, or request a required document.
   **Documents › Files**: upload, download, print the closing checklist.
8. **Billing** lists the invoices raised on this deal and lets you create one.
9. **The "⋯" menu** (top right) prints the closing checklist, and — for a
   Team Lead or Admin only — deletes the transaction, with a confirmation
   naming the address.
10. **Ask AI** (top right) slides the assistant in on the right side. Click it
    again to close. Reopen the deal: it remembers your choice.

---

## 3. Role checks

| Action | Agent | Coordinator | Team Lead | Admin |
| --- | --- | --- | --- | --- |
| Open a deal, use every tab | yes | yes | yes | yes |
| Edit tracking dates / run the cascade | yes | yes | yes | yes |
| See the Billing tab | yes | yes | yes | yes |
| "Create invoice" | only with invoicing enabled | only with invoicing enabled | yes | yes |
| Manage client access / Assign team | yes | no | yes | yes |
| **Delete transaction** (card footer and "⋯" menu) | **no** | **no** | yes | yes |

An Attorney gets the Matter Workspace on the same URL. Client, FSBO, and
Vendor users cannot reach either surface.

---

## 4. Links from elsewhere

Each should land on the right part of the right deal in one click:

- Notification bell → the deal's **Tasks** tab with that task highlighted.
- Closing Calendar → the deal's **Timeline**.
- My Task Queue → the deal's **Tasks** tab at that task.
- Clients hub → "Q&A" and "Access" open the deal's **People** tab with the
  right panel already open.
- An invoice / payment / payout → the deal's **Billing** tab.
- Dashboard priority cards, action queue, analytics → the deal.
- Older links ending in `?expand=…` or `?highlight=…` still open the list
  with that card expanded, as they always did.

---

## 5. Things that should NOT happen

- The AI assistant takes half the page before you ask for it.
- A deal opens straight into the plan editor with no summary.
- The list card's drawer is missing anything it used to do.
- Changing the Closing Date applies with no preview of what moves.
- The list and the detail page disagree about days to close, price, or a date
  you just edited.
- A "Compliance" tab appears alongside Documents (it is a view inside it).
- An Agent or Coordinator sees "Delete transaction".
- Any number appears with no source behind it.

---

## 6. Mobile pass (phone width)

- The list card and its drawer stack into one column and stay usable.
- The detail page's tab row scrolls sideways; every tab is reachable.
- The assistant appears as the **Agent** tab rather than a side panel.
- Print and Delete are in the detail page's "⋯" menu.
