from odoo import fields, models

from ..models.account_ios import _residual_to_date


class AccountIosPrepare(models.TransientModel):
    _name = "account.ios.prepare"
    _description = "Prepare Statements of Open Items"

    date = fields.Date(string="As of", required=True, default=fields.Date.context_today)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    partner_ids = fields.Many2many(
        "res.partner",
        string="Partners",
        domain="[('parent_id', '=', False)]",
        help="Leave empty to prepare a statement for every partner "
        "with an open item on that date.",
    )

    def action_prepare(self):
        self.ensure_one()
        partners = self.partner_ids or self._partners_with_open_items()
        records = self.env["account.ios"].prepare_for_partners(
            partners, self.date, self.company_id
        )
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Statements of Open Items"),
            "res_model": "account.ios",
            "view_mode": "list,form",
            "domain": [("id", "in", records.ids)],
            "context": {"create": False},
        }

    def _partners_with_open_items(self):
        """Partners with a non-zero receivable or payable balance on the date.

        Reconciliations dated after the date are ignored.
        """
        lines = self.env["account.move.line"].search(
            [
                ("company_id", "=", self.company_id.id),
                ("parent_state", "=", "posted"),
                ("date", "<=", self.date),
                ("partner_id", "!=", False),
                (
                    "account_id.account_type",
                    "in",
                    ("asset_receivable", "liability_payable"),
                ),
            ]
        )
        lines.mapped("matched_credit_ids.credit_move_id")
        lines.mapped("matched_debit_ids.debit_move_id")
        currency = self.company_id.currency_id
        open_lines = lines.filtered(
            lambda line: not currency.is_zero(_residual_to_date(line, self.date))
        )
        return open_lines.partner_id.commercial_partner_id
