from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    ios_reply_days = fields.Integer(
        string="IOS Reply Within (Days)",
        default=10,
        help="Default number of days the partner has to return a confirmed "
        "statement of open items.",
    )
