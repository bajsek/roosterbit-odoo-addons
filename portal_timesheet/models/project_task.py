from odoo import api, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    @api.model
    def _portal_timesheet_tasks(self, user):
        """Open tasks on which the portal user may log time.

        The user must have portal time entry enabled and be assigned to the task
        or follow it. The project must allow timesheets.
        """
        if not user.portal_timesheet_enabled:
            return self.browse()
        followed = (
            self.env["mail.followers"]
            .sudo()
            .search(
                [
                    ("res_model", "=", "project.task"),
                    ("partner_id", "=", user.partner_id.id),
                ]
            )
            .mapped("res_id")
        )
        return self.sudo().search(
            [
                "|",
                ("id", "in", followed),
                ("user_ids", "in", user.id),
                ("project_id.allow_timesheets", "=", True),
                ("project_id.active", "=", True),
                ("state", "not in", ("1_done", "1_canceled")),
            ],
            order="project_id, name",
        )
