from odoo import models


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    def _portal_timesheet_locked(self):
        """True when the line is invoiced and must not change from the portal."""
        self.ensure_one()
        if "timesheet_invoice_id" not in self._fields:
            return False
        invoice = self.sudo().timesheet_invoice_id
        return bool(invoice and invoice.state != "cancel")
