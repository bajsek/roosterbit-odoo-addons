=============================
Statement of Open Items (IOS)
=============================

.. |badge1| image:: https://img.shields.io/badge/licence-LGPL--3-blue.png
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3
.. |badge2| image:: https://img.shields.io/badge/odoo-18.0-875A7B.png
    :alt: Odoo 18.0

|badge1| |badge2|

Statement of open items (IOS, *izvod otvorenih stavki*) for reconciling balances
with business partners, as used in Croatia and the region.

For a partner and a date, the module lists open receivables and payables, as they
stood on that date. Reconciliations dated after the statement date are ignored, so a
year-end statement prepared in January still shows the balance on 31 December.

The statement is printed as a letter with the company and partner tax numbers, the
company IBAN, both tables, the balance sentence, the reply deadline and fields for
the partner's confirmation. The letter is printed in the partner's language.

The partner's reply is tracked on the statement: sent, confirmed or disputed, with
the reply date and the difference stated by the partner.

**Table of contents**

.. contents::
   :local:

Configuration
=============

- **Reply deadline:** Invoicing > Configuration > Settings > *Statements of Open
  Items* > **Reply deadline** (default 10 days, per company). Each statement copies
  the value into **Reply Within (Days)**, which can be changed while the statement
  is a draft.
- **Numbering:** sequence *Statement of Open Items* (``IOS/<year>/0001``). Change the
  prefix in Settings > Technical > Sequences.
- **Bank account:** the IBAN printed is the first bank account of the company.
- **Tax numbers:** Croatian partners (country Croatia or VAT starting with ``HR``)
  show the **OIB** (VAT number without ``HR``). Other partners show **VAT** with the
  full VAT number.
- **Language:** set the partner's language to print the letter in that language.

Usage
=====

For one partner:

1. Open the partner and click the **IOS** button. The first click creates a draft.
2. Set **As of** to the statement date. Lines are filled automatically.
3. Check **Reply Within (Days)** and change it if needed.
4. Print the letter from **Print > Statement of Open Items** and send it.
5. Click **Mark as Sent**. The statement is now locked.
6. When the partner replies, click **Partner Agrees** or **Partner Disagrees** and
   enter the stated difference in **Reply Note**.

For many partners, for example at year end:

1. Go to **Invoicing > Statements of Open Items** and click **Prepare
   Statements**.
2. Enter the date. Leave **Partners** empty to include every partner with an open
   item on that date.
3. One draft is created per partner. Running the wizard again refreshes existing
   drafts for the same date instead of creating duplicates.

**Reset to Draft** unlocks a statement and **Refresh Lines** recalculates it.

Changelog
=========

18.0.1.2.0
----------

- Configurable reply deadline: default in the accounting settings, editable on each
  statement before printing (was fixed at 10 days).
- Foreign partners show **VAT** with the full VAT number instead of **OIB**.
- Code style: ruff and pylint-odoo clean.

18.0.1.1.0
----------

- English source texts with a complete Croatian translation.
- The letter is printed in the partner's language.
- Multi-company record rules for statements and lines.
- Faster IOS counter on partners.
- More tests: workflow, balance sentence, language, wizard and multi-company.

Credits
=======

Authors
-------

- Roosterbit

Contributors
------------

- Roosterbit <https://www.roosterbit.com.hr>
