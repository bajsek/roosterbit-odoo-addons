from odoo import Command, fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import new_test_user, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountIos(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.partner_id.vat = "HR12345678903"
        bank_vals = {
            "acc_number": "HR1210010051863000160",
            "partner_id": cls.company.partner_id.id,
            "company_id": cls.company.id,
        }
        if "allow_out_payment" in cls.env["res.partner.bank"]._fields:
            bank_vals["allow_out_payment"] = True
        # sudo: setup data only; access add-ons may restrict bank accounts.
        bank = cls.env["res.partner.bank"].sudo().create(bank_vals)
        cls.company.partner_id.bank_ids = [Command.link(bank.id)]
        cls.partner = cls.partner_a
        cls.partner.write(
            {
                "vat": "HR98765432106",
                "lang": "en_US",
                "property_payment_term_id": False,
                "property_supplier_payment_term_id": False,
            }
        )
        cls.product = cls.product_a

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _invoice(self, move_type, partner, amount, invoice_date):
        vals = {
            "move_type": move_type,
            "partner_id": partner.id,
            "invoice_date": invoice_date,
            "date": invoice_date,
            "invoice_payment_term_id": False,
            "invoice_line_ids": [
                Command.create(
                    {
                        "product_id": self.product.id,
                        "quantity": 1,
                        "price_unit": amount,
                        "tax_ids": [Command.clear()],
                    }
                )
            ],
        }
        move = self.env["account.move"]
        # Extra fields required when a Croatian invoice module is installed.
        if "hr_payment_method" in move._fields and move_type in (
            "out_invoice",
            "out_refund",
        ):
            vals.update(
                {
                    "invoice_datetime": fields.Datetime.to_datetime(
                        f"{invoice_date} 10:00:00"
                    ),
                    "invoice_date_due": invoice_date,
                    "hr_delivery_date": invoice_date,
                    "hr_payment_method": "bank",
                    "hr_issue_location": "Zagreb",
                }
            )
        invoice = move.create(vals)
        invoice.action_post()
        return invoice

    def _pay(self, invoice, amount, payment_date):
        wizard = (
            self.env["account.payment.register"]
            .with_context(active_model="account.move", active_ids=invoice.ids)
            .create({"amount": amount, "payment_date": payment_date})
        )
        return wizard._create_payments()

    def _ios(self, date, partner=None):
        return self.env["account.ios"].create(
            {
                "partner_id": (partner or self.partner).id,
                "company_id": self.company.id,
                "date": date,
            }
        )

    def _render(self, ios):
        return (
            self.env["ir.actions.report"]
            ._render_qweb_html("account_ios_hr.report_account_ios", ios.ids)[0]
            .decode()
        )

    # ------------------------------------------------------------------
    # Open items and balance
    # ------------------------------------------------------------------

    def test_open_invoice_and_later_payment(self):
        invoice = self._invoice("out_invoice", self.partner, 100.0, "2026-01-15")
        before = self._ios("2026-01-31")
        self.assertAlmostEqual(before.amount_receivable, 100.0)
        self.assertAlmostEqual(before.balance, 100.0)
        self.assertEqual(before.line_ids.move_id, invoice)
        self.assertEqual(before.line_ids.side, "receivable")

        # A payment after the statement date does not change that statement.
        self._pay(invoice, 40.0, "2026-02-01")
        before.action_refresh()
        self.assertAlmostEqual(before.amount_receivable, 100.0)

        after = self._ios("2026-02-01")
        self.assertAlmostEqual(after.amount_receivable, 60.0)
        self.assertAlmostEqual(after.line_ids.amount_original, 100.0)
        self.assertAlmostEqual(after.line_ids.amount_open, 60.0)

    def test_fully_paid_invoice_is_not_listed(self):
        invoice = self._invoice("out_invoice", self.partner, 50.0, "2026-01-10")
        self._pay(invoice, 50.0, "2026-01-20")
        ios = self._ios("2026-01-31")
        self.assertFalse(ios.line_ids)
        self.assertTrue(ios.currency_id.is_zero(ios.balance))

    def test_payable_and_balance(self):
        self._invoice("out_invoice", self.partner, 100.0, "2026-03-01")
        self._invoice("in_invoice", self.partner, 70.0, "2026-03-02")
        ios = self._ios("2026-03-31")
        self.assertAlmostEqual(ios.amount_receivable, 100.0)
        self.assertAlmostEqual(ios.amount_payable, 70.0)
        self.assertAlmostEqual(ios.balance, 30.0)

    def test_contact_invoice_goes_to_company(self):
        contact = self.env["res.partner"].create(
            {"name": "IOS contact", "parent_id": self.partner.id, "type": "invoice"}
        )
        self._invoice("out_invoice", contact, 15.0, "2026-04-01")
        ios = self._ios("2026-04-30", partner=contact)
        self.assertEqual(ios.partner_id, self.partner)
        self.assertAlmostEqual(ios.amount_receivable, 15.0)

    def test_sequence_number(self):
        ios = self._ios("2026-04-30")
        self.assertTrue(ios.name.startswith("IOS/"))

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------

    def test_sent_statement_is_locked_and_keeps_reply(self):
        self._invoice("out_invoice", self.partner, 10.0, "2026-05-01")
        ios = self._ios("2026-05-31")
        ios.action_mark_sent()
        with self.assertRaises(UserError):
            ios.action_refresh()
        with self.assertRaises(UserError):
            ios.date = "2026-06-30"
        ios.reply_note = "Difference of 1 EUR"
        ios.action_disagree()
        self.assertEqual(ios.state, "disputed")
        self.assertTrue(ios.reply_date)

    def test_agree_and_reset_to_draft(self):
        invoice = self._invoice("out_invoice", self.partner, 30.0, "2026-05-01")
        ios = self._ios("2026-05-31")
        ios.action_mark_sent()
        ios.action_agree()
        self.assertEqual(ios.state, "confirmed")
        ios.action_draft()
        self._pay(invoice, 30.0, "2026-05-20")
        ios.action_refresh()
        self.assertFalse(ios.line_ids)

    def test_date_change_on_draft_refreshes_lines(self):
        self._invoice("out_invoice", self.partner, 20.0, "2026-06-15")
        ios = self._ios("2026-06-01")
        self.assertFalse(ios.line_ids)
        ios.date = "2026-06-30"
        self.assertAlmostEqual(ios.amount_receivable, 20.0)

    # ------------------------------------------------------------------
    # Balance sentence and PDF
    # ------------------------------------------------------------------

    def test_balance_sentence(self):
        ios = self._ios("2026-01-01")
        self.assertIn("zero", ios.saldo_sentence())
        self._invoice("in_invoice", self.partner, 12.0, "2026-01-05")
        ios.date = "2026-01-31"
        self.assertIn("we owe you", ios.saldo_sentence())
        self._invoice("out_invoice", self.partner, 40.0, "2026-01-06")
        ios.action_refresh()
        self.assertIn("you owe us", ios.saldo_sentence())

    def test_pdf_contains_oib_iban_and_invoice_number(self):
        invoice = self._invoice("out_invoice", self.partner, 25.0, "2026-06-01")
        html = self._render(self._ios("2026-06-30"))
        self.assertIn("Statement of Open Items", html)
        self.assertIn("12345678903", html)
        self.assertIn("98765432106", html)
        # Other add-ons may print the IBAN in groups of four.
        self.assertIn("HR1210010051863000160", html.replace(" ", ""))
        self.assertIn(invoice.name, html)
        self.assertIn("you owe us", html)

    def test_pdf_foreign_partner_shows_vat_not_oib(self):
        foreign = self.env["res.partner"].create(
            {
                "name": "Foreign GmbH",
                "vat": "DE123456788",
                "country_id": self.env.ref("base.de").id,
                "lang": "en_US",
            }
        )
        self._invoice("out_invoice", foreign, 10.0, "2026-06-01")
        html = self._render(self._ios("2026-06-30", partner=foreign))
        self.assertIn("VAT: DE123456788", html)
        # Our own company is Croatian and keeps the OIB.
        self.assertIn("OIB: 12345678903", html)
        self.assertNotIn("OIB: DE", html)

    def test_reply_days_from_settings_and_per_statement(self):
        self.assertEqual(self.company.ios_reply_days, 10)
        ios = self._ios("2026-06-30")
        self.assertEqual(ios.reply_days, 10)
        self.assertIn("within 10 days", self._render(ios))

        self.company.ios_reply_days = 15
        ios_15 = (
            self.env["account.ios"]
            .with_company(self.company)
            .create(
                {
                    "partner_id": self.partner.id,
                    "company_id": self.company.id,
                    "date": "2026-07-31",
                }
            )
        )
        self.assertEqual(ios_15.reply_days, 15)

        ios_15.reply_days = 7
        self.assertIn("within 7 days", self._render(ios_15))
        with self.assertRaises(ValidationError):
            ios_15.reply_days = 0

    def test_settings_field(self):
        settings = self.env["res.config.settings"].create({"ios_reply_days": 20})
        settings.execute()
        self.assertEqual(self.env.company.ios_reply_days, 20)

    def test_pdf_payables_only(self):
        self._invoice("in_invoice", self.partner, 9.0, "2026-06-01")
        html = self._render(self._ios("2026-06-30"))
        self.assertIn("Our payables", html)
        self.assertNotIn("Our receivables", html)

    def test_pdf_in_partner_language(self):
        self.env["res.lang"]._activate_lang("hr_HR")
        self.env["ir.module.module"]._load_module_terms(
            ["account_ios_hr"], ["hr_HR"], overwrite=True
        )
        self.partner.lang = "hr_HR"
        self._invoice("out_invoice", self.partner, 25.0, "2026-06-01")
        html = self._render(self._ios("2026-06-30"))
        self.assertIn("Izvod otvorenih stavki", html)
        self.assertIn("Naša potraživanja", html)
        self.assertIn("Vi dugujete nama", html)
        self.assertIn("u roku od 10 dana", html)

    # ------------------------------------------------------------------
    # Partner button and wizard
    # ------------------------------------------------------------------

    def test_partner_button_creates_first_statement(self):
        self.assertEqual(self.partner.ios_count, 0)
        action = self.partner.action_open_ios()
        self.assertEqual(action["view_mode"], "form")
        ios = self.env["account.ios"].browse(action["res_id"])
        self.assertEqual(ios.partner_id, self.partner)
        self.partner.invalidate_recordset(["ios_count"])
        self.assertEqual(self.partner.ios_count, 1)
        action = self.partner.action_open_ios()
        self.assertEqual(action["view_mode"], "list,form")

    def test_prepare_refreshes_existing_draft(self):
        self._invoice("out_invoice", self.partner, 8.0, "2026-07-01")
        wizard = self.env["account.ios.prepare"].create(
            {
                "date": "2026-07-31",
                "company_id": self.company.id,
                "partner_ids": [Command.set(self.partner.ids)],
            }
        )
        wizard.action_prepare()
        wizard.action_prepare()
        drafts = self.env["account.ios"].search(
            [
                ("partner_id", "=", self.partner.id),
                ("date", "=", "2026-07-31"),
                ("state", "=", "draft"),
            ]
        )
        self.assertEqual(len(drafts), 1)

    def test_prepare_without_partners_uses_open_items_on_date(self):
        open_invoice = self._invoice("out_invoice", self.partner, 8.0, "2026-07-01")
        paid = self._invoice("out_invoice", self.partner_b, 5.0, "2026-07-01")
        self._pay(paid, 5.0, "2026-07-10")
        wizard = self.env["account.ios.prepare"].create(
            {"date": "2026-07-31", "company_id": self.company.id}
        )
        partners = wizard._partners_with_open_items()
        self.assertIn(open_invoice.partner_id, partners)
        self.assertNotIn(self.partner_b, partners)

    # ------------------------------------------------------------------
    # Multi-company
    # ------------------------------------------------------------------

    def test_other_company_user_does_not_see_statement(self):
        self._invoice("out_invoice", self.partner, 11.0, "2026-08-01")
        ios = self._ios("2026-08-31")
        self.assertTrue(ios.line_ids)
        other_company = self.setup_other_company(name="IOS other company")["company"]
        user = new_test_user(
            self.env,
            login="ios_other_company",
            groups="account.group_account_invoice",
            company_id=other_company.id,
            company_ids=[Command.set(other_company.ids)],
        )
        found = self.env["account.ios"].with_user(user).search([("id", "=", ios.id)])
        self.assertFalse(found)
        lines = (
            self.env["account.ios.line"]
            .with_user(user)
            .search([("ios_id", "=", ios.id)])
        )
        self.assertFalse(lines)
