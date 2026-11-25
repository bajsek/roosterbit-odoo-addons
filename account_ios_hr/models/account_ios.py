from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang

LOCKED_FIELDS = {"date", "partner_id", "company_id"}


class AccountIos(models.Model):
    _name = "account.ios"
    _description = "Statement of Open Items"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, id desc"
    _check_company_auto = True

    name = fields.Char(
        string="Number",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env._("New"),
    )
    partner_id = fields.Many2one(
        "res.partner",
        required=True,
        tracking=True,
        check_company=True,
        domain="[('parent_id', '=', False)]",
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    date = fields.Date(
        string="As of",
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("sent", "Sent"),
            ("confirmed", "Confirmed"),
            ("disputed", "Disputed"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
    )
    reply_date = fields.Date(tracking=True)
    reply_note = fields.Text()
    reply_days = fields.Integer(
        string="Reply Within (Days)",
        required=True,
        default=lambda self: self.env.company.ios_reply_days or 10,
        help="Number of days the partner has to return the confirmed statement. "
        "Printed on the letter. The default comes from the accounting settings.",
    )
    line_ids = fields.One2many("account.ios.line", "ios_id", string="Lines")
    amount_receivable = fields.Monetary(
        string="Receivables",
        compute="_compute_amounts",
        store=True,
        currency_field="currency_id",
    )
    amount_payable = fields.Monetary(
        string="Payables",
        compute="_compute_amounts",
        store=True,
        currency_field="currency_id",
    )
    balance = fields.Monetary(
        compute="_compute_amounts",
        store=True,
        currency_field="currency_id",
        help="Positive: the partner owes us. Negative: we owe the partner.",
    )

    @api.onchange("partner_id", "date", "company_id")
    def _onchange_fill_lines(self):
        if (
            self.state not in (False, "draft")
            or not self.partner_id
            or not self.date
            or not self.company_id
        ):
            return
        commands = [(5, 0, 0)]
        commands += [(0, 0, vals) for vals in self._collect_line_vals()]
        self.line_ids = commands

    @api.depends("line_ids.amount_open", "line_ids.side")
    def _compute_amounts(self):
        for ios in self:
            receivable = sum(
                ios.line_ids.filtered(lambda line: line.side == "receivable").mapped(
                    "amount_open"
                )
            )
            payable = sum(
                ios.line_ids.filtered(lambda line: line.side == "payable").mapped(
                    "amount_open"
                )
            )
            ios.amount_receivable = receivable
            ios.amount_payable = payable
            ios.balance = receivable - payable

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("partner_id"):
                partner = self.env["res.partner"].browse(vals["partner_id"])
                vals["partner_id"] = partner.commercial_partner_id.id
            if vals.get("name", "/") in ("/", "New", self.env._("New")):
                vals["name"] = (
                    self.env["ir.sequence"]
                    .with_company(vals.get("company_id") or self.env.company.id)
                    .next_by_code("account.ios")
                    or "/"
                )
        records = super().create(vals_list)
        records.filtered(lambda ios: ios.state == "draft").action_refresh()
        return records

    def write(self, vals):
        if LOCKED_FIELDS & set(vals) and any(ios.state != "draft" for ios in self):
            raise UserError(
                self.env._(
                    "Date, partner and company can only be changed "
                    "while the statement is a draft."
                )
            )
        if vals.get("partner_id"):
            partner = self.env["res.partner"].browse(vals["partner_id"])
            vals = dict(vals, partner_id=partner.commercial_partner_id.id)
        res = super().write(vals)
        if not self.env.context.get("ios_skip_refresh") and LOCKED_FIELDS & set(vals):
            self.filtered(lambda ios: ios.state == "draft").action_refresh()
        return res

    def action_refresh(self):
        if self.filtered(lambda ios: ios.state != "draft"):
            raise UserError(
                self.env._("Open items can only be refreshed on a draft statement.")
            )
        for ios in self:
            commands = [(5, 0, 0)]
            commands += [(0, 0, vals) for vals in ios._collect_line_vals()]
            ios.with_context(ios_skip_refresh=True).write({"line_ids": commands})
        return True

    def action_mark_sent(self):
        self.write({"state": "sent"})

    def action_agree(self):
        self.write(
            {
                "state": "confirmed",
                "reply_date": fields.Date.context_today(self),
            }
        )

    def action_disagree(self):
        self.write(
            {
                "state": "disputed",
                "reply_date": fields.Date.context_today(self),
            }
        )

    def action_draft(self):
        self.write({"state": "draft"})

    @api.constrains("reply_days")
    def _check_reply_days(self):
        for ios in self:
            if ios.reply_days < 1:
                raise ValidationError(
                    self.env._("The reply deadline must be at least one day.")
                )

    @api.onchange("company_id")
    def _onchange_company_reply_days(self):
        if self.company_id and self.state in (False, "draft"):
            self.reply_days = self.company_id.ios_reply_days or 10

    def reply_sentence(self):
        """Reply deadline sentence for the letter, in the language of the env."""
        self.ensure_one()
        return self.env._(
            "Please return the confirmed statement within %(days)s days.",
            days=self.reply_days,
        )

    def tax_id_lines(self, partner):
        """Label and number printed for a partner's tax identification.

        Croatian partners show the OIB (VAT number without the HR prefix). Other
        partners show the full VAT number.
        """
        self.ensure_one()
        vat = (partner.vat or "").strip()
        if not vat:
            return []
        if partner.country_id.code == "HR" or vat.upper().startswith("HR"):
            return [("OIB", _oib(partner))]
        return [(self.env._("VAT"), vat)]

    def saldo_sentence(self):
        """Balance sentence for the letter, in the language of the current env."""
        self.ensure_one()
        if self.currency_id.is_zero(self.balance):
            return self.env._(
                "According to our books, the balance on that date is zero."
            )
        amount = formatLang(self.env, abs(self.balance), currency_obj=self.currency_id)
        if self.balance > 0:
            return self.env._(
                "According to our books, on that date you owe us %s.", amount
            )
        return self.env._("According to our books, on that date we owe you %s.", amount)

    def partner_oib(self):
        self.ensure_one()
        return _oib(self.partner_id)

    def company_oib(self):
        self.ensure_one()
        return _oib(self.company_id.partner_id)

    def company_iban(self):
        self.ensure_one()
        bank = self.company_id.partner_id.bank_ids[:1]
        return bank.acc_number or ""

    def _collect_line_vals(self):
        self.ensure_one()
        company = self.company_id
        date = self.date
        partner = self.partner_id.commercial_partner_id
        lines = self.env["account.move.line"].search(
            [
                ("company_id", "=", company.id),
                ("parent_state", "=", "posted"),
                ("date", "<=", date),
                ("partner_id", "child_of", partner.id),
                (
                    "account_id.account_type",
                    "in",
                    ("asset_receivable", "liability_payable"),
                ),
            ]
        )
        # Prefetch the counterpart lines used by _residual_to_date.
        lines.mapped("matched_credit_ids.credit_move_id")
        lines.mapped("matched_debit_ids.debit_move_id")
        currency = company.currency_id
        vals = []
        for line in lines:
            residual = _residual_to_date(line, date)
            if currency.is_zero(residual):
                continue
            side = (
                "receivable"
                if line.account_id.account_type == "asset_receivable"
                else "payable"
            )
            sign = 1 if side == "receivable" else -1
            move = line.move_id
            vals.append(
                {
                    "move_id": move.id,
                    "move_line_id": line.id,
                    "side": side,
                    "invoice_date": move.invoice_date or line.date,
                    "date_maturity": line.date_maturity or line.date,
                    "move_name": move.name,
                    "ref": move.ref or line.name or "",
                    "amount_original": sign * line.balance,
                    "amount_open": sign * residual,
                }
            )
        vals.sort(
            key=lambda item: (
                item["side"],
                item["invoice_date"] or date,
                item["move_name"] or "",
            )
        )
        return vals

    @api.model
    def prepare_for_partners(self, partners, date, company):
        """One draft per partner and date. An existing draft is refreshed."""
        records = self.browse()
        for partner in partners.mapped("commercial_partner_id"):
            existing = self.search(
                [
                    ("partner_id", "=", partner.id),
                    ("company_id", "=", company.id),
                    ("date", "=", date),
                    ("state", "=", "draft"),
                ],
                limit=1,
            )
            if existing:
                existing.action_refresh()
                records |= existing
            else:
                records |= self.create(
                    {
                        "partner_id": partner.id,
                        "company_id": company.id,
                        "date": date,
                    }
                )
        return records


class AccountIosLine(models.Model):
    _name = "account.ios.line"
    _description = "Statement of Open Items Line"
    _order = "side, invoice_date, move_name, id"

    ios_id = fields.Many2one(
        "account.ios", string="Statement", required=True, ondelete="cascade"
    )
    company_id = fields.Many2one(related="ios_id.company_id", store=True)
    currency_id = fields.Many2one(related="ios_id.currency_id")
    move_id = fields.Many2one("account.move", string="Document", required=True)
    move_line_id = fields.Many2one(
        "account.move.line", string="Journal Item", required=True
    )
    side = fields.Selection(
        [("receivable", "Receivable"), ("payable", "Payable")],
        required=True,
    )
    invoice_date = fields.Date(string="Document Date")
    date_maturity = fields.Date(string="Due Date")
    move_name = fields.Char(string="Number")
    ref = fields.Char(string="Reference")
    amount_original = fields.Monetary(
        string="Document Amount", currency_field="currency_id"
    )
    amount_open = fields.Monetary(string="Open Amount", currency_field="currency_id")


def _oib(partner):
    """Croatian OIB from the VAT number, without the HR prefix."""
    vat = (partner.vat or "").strip()
    if vat.upper().startswith("HR"):
        vat = vat[2:]
    return vat


def _residual_to_date(line, date):
    """Line balance after reconciliations dated on or before the given date."""
    residual = line.balance
    if line.balance > 0:
        for partial in line.matched_credit_ids:
            if partial.credit_move_id.date <= date:
                residual -= partial.amount
    elif line.balance < 0:
        for partial in line.matched_debit_ids:
            if partial.debit_move_id.date <= date:
                residual += partial.amount
    return residual
