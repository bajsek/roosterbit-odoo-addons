# Statement of Open Items (IOS)

Module `account_ios_hr`, version 18.0.1.2.0. Depends only on the standard Odoo
modules `account` and `mail`. License LGPL-3.

A statement of open items (IOS, Croatian *izvod otvorenih stavki*) is a letter sent
to a business partner to confirm the open balance between the two companies on a
given date. It is common practice in Croatia and the region, typically at year end.

For a partner and a date, the module lists open receivables and payables **as they
stood on that date**. Payments and reconciliations dated after the statement date
are ignored, so a statement for 31 December prepared in January still shows the
balance on 31 December.

---

## 1. Setup

| What | Where |
|---|---|
| **Reply deadline** (default 10 days, per company) | Invoicing → Configuration → Settings → *Statements of Open Items* → **Reply deadline** |
| **Company tax number** | VAT field of the company (`HR12345678903` or `12345678903` for Croatia) |
| **Partner tax number** | VAT field of the partner |
| **IBAN on the letter** | first bank account of the company |
| **Language of the letter** | partner's language (contact → *Sales & Purchase* → Language) |
| **Numbering** | Settings → Technical → Sequences → *Statement of Open Items* (`IOS/2026/0001`) |

### Tax numbers on the letter

| Partner | Printed as |
|---|---|
| Country Croatia, or VAT starting with `HR` | **OIB:** VAT number without `HR` |
| Any other partner | **VAT:** full VAT number, e.g. `DE123456788` |
| No VAT number | nothing |

### Language

The letter is printed in the **partner's language**, including the balance
sentence, amounts and dates. A partner set to English gets an English letter; a
partner set to Croatian gets a Croatian one. Check the language of domestic
partners before sending statements.

---

## 2. Statement for one partner

1. Open the partner and click the **IOS** button at the top right. The first click
   creates a draft.
2. Set **As of**. The lines are filled automatically.
3. Check **Reply Within (Days)**. It comes from the settings and can be changed on
   this statement while it is a draft.
4. **Print → Statement of Open Items** and send the letter to the partner.
5. Click **Mark as Sent**. The statement is now locked and its lines no longer
   change.
6. When the partner replies:
   - **Partner Agrees** → status *Confirmed*;
   - **Partner Disagrees** → status *Disputed*; enter the stated difference in
     **Reply Note**.

The reply date is filled automatically.

---

## 3. Statements for many partners (year end)

1. **Invoicing → Statements of Open Items → Prepare Statements**.
2. Enter the date, e.g. 31 December.
3. **Partners**:
   - empty: every partner with an open item on that date;
   - filled: only the selected partners.
4. **Prepare**. One draft is created per partner.

Running the wizard again for the same date refreshes the existing drafts instead
of creating duplicates.

---

## 4. Statuses

| Status | Meaning | What can be done |
|---|---|---|
| **Draft** | being prepared | change date, partner, reply deadline; **Refresh Lines** |
| **Sent** | sent to the partner | waiting for the reply; lines are locked |
| **Confirmed** | the partner agrees | nothing |
| **Disputed** | the partner disagrees | record the difference |

**Reset to Draft** unlocks a statement. **Refresh Lines** then recalculates it.

---

## 5. The letter (PDF)

- Header: company address, tax number, IBAN, statement number and date.
- Recipient: partner address and tax number.
- Balance sentence: "you owe us", "we owe you" or "the balance is zero".
- Tables **Our receivables** and **Our payables**. Payables start on a new page and
  are followed by the balance.
- Footer: reply deadline from the statement, and lines for signature, place and
  date, and the difference if any.

---

## 6. Multi-company

Statements and their lines are visible only in the companies selected by the user.
The **IOS** button on a partner counts the statements of the current company. The
reply deadline is set per company.

---

## 7. Troubleshooting

| Problem | Cause and fix |
|---|---|
| A paid invoice still appears | The payment is dated after the statement date. Correct, by design. |
| The letter is in the wrong language | Change the partner's language and print again. |
| "OIB" shown for a foreign partner | The partner's VAT starts with `HR` or its country is Croatia. Correct the contact. |
| Lines do not change after a new invoice | The statement is not a draft. **Reset to Draft**, then **Refresh Lines**. |
| "The reply deadline must be at least one day" | Enter 1 or more in **Reply Within (Days)**. |

---

## 8. Technical notes

| Item | Where |
|---|---|
| Models `account.ios`, `account.ios.line` | `models/account_ios.py` |
| Balance on a date | `_residual_to_date(line, date)` |
| Tax number label | `account.ios.tax_id_lines(partner)` |
| Reply deadline | `res.company.ios_reply_days`, `account.ios.reply_days` |
| Wizard | `wizard/ios_prepare.py` |
| Letter | `report/ios_templates.xml` |
| Translations | `i18n/account_ios_hr.pot`, `i18n/hr.po` |

`_oib` and `_residual_to_date` are public helpers used by other modules (for
example a payment reminder module). Keep their names.

### Tests

`tests/test_ios.py`, 19 tests: balance on a date, later payments, fully paid
invoices, payables and balance, contacts rolled up to the company, numbering,
workflow and locking, balance sentences, PDF content, foreign partner VAT, reply
deadline from settings and per statement, Croatian translation, partner button,
wizard, multi-company.

Run on a test database:

```bash
odoo -d <database> -i account_ios_hr --test-enable --test-tags /account_ios_hr --stop-after-init
```
