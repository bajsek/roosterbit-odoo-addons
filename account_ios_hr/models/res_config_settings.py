from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    ios_reply_days = fields.Integer(
        related="company_id.ios_reply_days",
        readonly=False,
    )
