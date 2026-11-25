from odoo import fields, http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal

MAX_HOURS_PER_ENTRY = 24.0


class PortalTimesheetEntry(CustomerPortal):
    """Time entry for portal users on tasks they follow or are assigned to.

    Portal users have no direct access rights on timesheets or employees. Every
    read and write goes through these routes, which check access first and then
    use sudo.
    """

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _timesheet_entry_lines(self, user):
        return (
            request.env["account.analytic.line"]
            .sudo()
            .search(
                [("user_id", "=", user.id), ("project_id", "!=", False)],
                order="date desc, id desc",
            )
        )

    def _timesheet_entry_own_line(self, line_id):
        """Own timesheet line of the current user, or None."""
        line = request.env["account.analytic.line"].sudo().browse(line_id).exists()
        if not line or line.user_id != request.env.user or not line.project_id:
            return None
        return line

    def _timesheet_entry_line(self, line_id):
        """Own timesheet line that may still be changed, or None."""
        line = self._timesheet_entry_own_line(line_id)
        if not line or line._portal_timesheet_locked():
            return None
        return line

    def _timesheet_entry_values(self, line=None, error=None, form=None):
        user = request.env.user
        form = form or {}
        if line:
            form = {
                "task_id": str(line.task_id.id),
                "date": fields.Date.to_string(line.date),
                "unit_amount": line.unit_amount,
                "name": line.name or "",
            } | form
        values = self._prepare_portal_layout_values()
        values.update(
            {
                "page_name": "timesheet_entry",
                "tasks": request.env["project.task"]._portal_timesheet_tasks(user),
                "line": line,
                "form": form,
                "error": error,
                "today": fields.Date.to_string(fields.Date.context_today(user)),
            }
        )
        return values

    def _timesheet_entry_parse(self, post):
        """Validated values from the form. Raises UserError on bad input."""
        user = request.env.user
        try:
            task_id = int(post.get("task_id") or 0)
            hours = float(post.get("unit_amount") or 0)
            date = fields.Date.to_date(post.get("date"))
        except ValueError as exc:
            raise UserError(
                request.env._("Please check the task, the date and the hours.")
            ) from exc
        if not date:
            raise UserError(request.env._("The date is required."))
        if hours <= 0 or hours > MAX_HOURS_PER_ENTRY:
            raise UserError(
                request.env._(
                    "Hours must be more than 0 and at most %s.", MAX_HOURS_PER_ENTRY
                )
            )
        task = (
            request.env["project.task"]
            ._portal_timesheet_tasks(user)
            .filtered(lambda t: t.id == task_id)
        )
        if not task:
            raise AccessError(request.env._("You cannot log time on this task."))
        return {
            "task_id": task.id,
            "project_id": task.project_id.id,
            "date": date,
            "unit_amount": hours,
            "name": (post.get("name") or "").strip() or "/",
        }

    def _timesheet_entry_employee(self, task):
        """Employee of the portal user in the task's company, created if missing."""
        user = request.env.user
        company = task.company_id or task.project_id.company_id or user.company_id
        Employee = request.env["hr.employee"].sudo().with_company(company)
        employee = Employee.search(
            [("user_id", "=", user.id), ("company_id", "=", company.id)], limit=1
        )
        if not employee:
            employee = Employee.create(
                {"name": user.name, "user_id": user.id, "company_id": company.id}
            )
        return employee

    def _timesheet_entry_render(self, line=None, error=None, form=None):
        return request.render(
            "portal_timesheet.portal_timesheet_entry_form",
            self._timesheet_entry_values(line=line, error=error, form=form),
        )

    # ------------------------------------------------------------------
    # Routes
    # ------------------------------------------------------------------

    @http.route("/my/timesheet-entries", type="http", auth="user", website=True)
    def portal_timesheet_entries(self, **kw):
        user = request.env.user
        if not user.portal_timesheet_enabled:
            return request.redirect("/my")
        values = self._prepare_portal_layout_values()
        values.update(
            {
                "page_name": "timesheet_entry",
                "lines": self._timesheet_entry_lines(user),
                "message": kw.get("message"),
            }
        )
        return request.render("portal_timesheet.portal_timesheet_entries", values)

    @http.route(
        "/my/timesheet-entries/new",
        type="http",
        auth="user",
        website=True,
        methods=["GET", "POST"],
    )
    def portal_timesheet_entry_new(self, **post):
        if not request.env.user.portal_timesheet_enabled:
            return request.redirect("/my")
        if request.httprequest.method != "POST":
            return self._timesheet_entry_render()
        try:
            vals = self._timesheet_entry_parse(post)
            task = request.env["project.task"].sudo().browse(vals["task_id"])
            vals |= {
                "user_id": request.env.user.id,
                "employee_id": self._timesheet_entry_employee(task).id,
            }
            request.env["account.analytic.line"].sudo().create(vals)
        except (AccessError, UserError, ValidationError) as exc:
            return self._timesheet_entry_render(error=exc.args[0], form=post)
        return request.redirect("/my/timesheet-entries?message=saved")

    @http.route(
        "/my/timesheet-entries/<int:line_id>/edit",
        type="http",
        auth="user",
        website=True,
        methods=["GET", "POST"],
    )
    def portal_timesheet_entry_edit(self, line_id, **post):
        if not request.env.user.portal_timesheet_enabled:
            return request.redirect("/my")
        line = self._timesheet_entry_line(line_id)
        if not line:
            return request.redirect("/my/timesheet-entries")
        if request.httprequest.method != "POST":
            return self._timesheet_entry_render(line=line)
        try:
            vals = self._timesheet_entry_parse(post)
            line.write(vals)
        except (AccessError, UserError, ValidationError) as exc:
            return self._timesheet_entry_render(line=line, error=exc.args[0], form=post)
        return request.redirect("/my/timesheet-entries?message=saved")

    @http.route(
        "/my/timesheet-entries/<int:line_id>/delete",
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
    )
    def portal_timesheet_entry_delete(self, line_id, **post):
        if not request.env.user.portal_timesheet_enabled:
            return request.redirect("/my")
        line = self._timesheet_entry_own_line(line_id)
        if not line:
            return request.redirect("/my/timesheet-entries")
        if line._portal_timesheet_locked():
            return request.redirect("/my/timesheet-entries?message=locked")
        try:
            line.unlink()
        except (AccessError, UserError, ValidationError):
            return request.redirect("/my/timesheet-entries?message=locked")
        return request.redirect("/my/timesheet-entries?message=deleted")
