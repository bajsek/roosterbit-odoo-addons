from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    ios_count = fields.Integer(string="IOS", compute="_compute_ios_count")

    def _compute_ios_count(self):
        groups = self.env["account.ios"]._read_group(
            [
                ("partner_id", "in", self.commercial_partner_id.ids),
                ("company_id", "=", self.env.company.id),
            ],
            groupby=["partner_id"],
            aggregates=["__count"],
        )
        counts = {partner.id: count for partner, count in groups}
        for partner in self:
            partner.ios_count = counts.get(partner.commercial_partner_id.id, 0)

    def action_open_ios(self):
        self.ensure_one()
        partner = self.commercial_partner_id
        action = {
            "type": "ir.actions.act_window",
            "name": self.env._("Statements of Open Items"),
            "res_model": "account.ios",
            "view_mode": "list,form",
            "domain": [
                ("partner_id", "=", partner.id),
                ("company_id", "=", self.env.company.id),
            ],
            "context": {
                "default_partner_id": partner.id,
                "default_company_id": self.env.company.id,
            },
        }
        if not self.ios_count:
            ios = self.env["account.ios"].create(
                {
                    "partner_id": partner.id,
                    "company_id": self.env.company.id,
                }
            )
            action.update({"res_id": ios.id, "view_mode": "form"})
        return action
