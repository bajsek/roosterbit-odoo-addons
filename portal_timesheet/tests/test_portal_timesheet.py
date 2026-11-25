import re

from odoo.exceptions import AccessError
from odoo.tests import HttpCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestPortalTimesheet(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.portal = new_test_user(
            cls.env,
            login="portal_time",
            password="portal_time_pw",
            groups="base.group_portal",
            name="Portal Time",
        )
        cls.portal.portal_timesheet_enabled = True
        cls.portal_off = new_test_user(
            cls.env,
            login="portal_time_off",
            password="portal_time_off_pw",
            groups="base.group_portal",
            name="Portal Off",
        )
        cls.other_portal = new_test_user(
            cls.env,
            login="portal_time_other",
            password="portal_time_other_pw",
            groups="base.group_portal",
            name="Portal Other",
        )
        cls.other_portal.portal_timesheet_enabled = True

        Project = cls.env["project.project"]
        cls.project = Project.create(
            {"name": "Portal project", "allow_timesheets": True}
        )
        cls.project_no_time = Project.create(
            {"name": "No timesheets", "allow_timesheets": False}
        )
        Task = cls.env["project.task"]
        cls.task_followed = Task.create(
            {"name": "Followed task", "project_id": cls.project.id}
        )
        cls.task_other = Task.create(
            {"name": "Other task", "project_id": cls.project.id}
        )
        cls.task_no_time = Task.create(
            {"name": "No time task", "project_id": cls.project_no_time.id}
        )
        for task in (cls.task_followed, cls.task_no_time):
            task.message_subscribe(partner_ids=cls.portal.partner_id.ids)
        cls.task_other.message_subscribe(partner_ids=cls.other_portal.partner_id.ids)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _login(self, user, password):
        self.authenticate(user.login, password)

    def _csrf(self, url):
        response = self.url_open(url)
        self.assertEqual(response.status_code, 200)
        match = re.search(r'name="csrf_token" value="([^"]+)"', response.text)
        self.assertTrue(match, "form must contain a CSRF token")
        return match.group(1)

    def _post(self, url, data, form_url="/my/timesheet-entries/new"):
        data = dict(data, csrf_token=self._csrf(form_url))
        return self.url_open(url, data=data)

    def _lines(self, user):
        return self.env["account.analytic.line"].search([("user_id", "=", user.id)])

    def _new_line(self, user, task, hours=2.0):
        employee = self.env["hr.employee"].create(
            {"name": user.name, "user_id": user.id, "company_id": self.env.company.id}
        )
        return self.env["account.analytic.line"].create(
            {
                "name": "Existing",
                "task_id": task.id,
                "project_id": task.project_id.id,
                "unit_amount": hours,
                "user_id": user.id,
                "employee_id": employee.id,
            }
        )

    # ------------------------------------------------------------------
    # Access rights
    # ------------------------------------------------------------------

    def test_portal_has_no_direct_rights(self):
        for model, operation in (
            ("hr.employee", "read"),
            ("hr.employee", "write"),
            ("hr.employee", "create"),
            ("mail.followers", "read"),
            ("account.analytic.line", "create"),
            ("account.analytic.line", "write"),
            ("account.analytic.line", "unlink"),
        ):
            with self.subTest(model=model, operation=operation):
                with self.assertRaises(AccessError):
                    self.env[model].with_user(self.portal).check_access(operation)

    def test_tasks_offered_to_portal_user(self):
        Task = self.env["project.task"]
        self.assertEqual(Task._portal_timesheet_tasks(self.portal), self.task_followed)
        self.assertFalse(Task._portal_timesheet_tasks(self.portal_off))
        self.task_followed.state = "1_done"
        self.assertFalse(Task._portal_timesheet_tasks(self.portal))

    # ------------------------------------------------------------------
    # Portal pages
    # ------------------------------------------------------------------

    def test_home_shows_entry_only_when_enabled(self):
        self._login(self.portal, "portal_time_pw")
        self.assertIn("/my/timesheet-entries", self.url_open("/my").text)
        self._login(self.portal_off, "portal_time_off_pw")
        home = self.url_open("/my")
        self.assertEqual(home.status_code, 200)
        self.assertNotIn("/my/timesheet-entries", home.text)

    def test_disabled_user_is_redirected(self):
        self._login(self.portal_off, "portal_time_off_pw")
        # Follow redirects: the website may add a language prefix first.
        response = self.url_open("/my/timesheet-entries")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.url.rstrip("/").endswith("/my"), response.url)

    def test_core_timesheet_page_is_untouched(self):
        self._login(self.portal, "portal_time_pw")
        response = self.url_open("/my/timesheets")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("/my/timesheet-entries/new", response.text)

    def test_log_time_creates_line_and_employee(self):
        self._login(self.portal, "portal_time_pw")
        response = self._post(
            "/my/timesheet-entries/new",
            {
                "task_id": self.task_followed.id,
                "date": "2026-11-18",
                "unit_amount": "1.5",
                "name": "Site visit",
            },
        )
        self.assertEqual(response.status_code, 200)
        line = self._lines(self.portal)
        self.assertEqual(len(line), 1)
        self.assertEqual(line.task_id, self.task_followed)
        self.assertEqual(line.unit_amount, 1.5)
        self.assertEqual(line.name, "Site visit")
        self.assertEqual(line.employee_id.user_id, self.portal)
        self.assertIn("Site visit", self.url_open("/my/timesheet-entries").text)

    def test_cannot_log_time_on_other_task(self):
        self._login(self.portal, "portal_time_pw")
        for task in (self.task_other, self.task_no_time):
            with self.subTest(task=task.name):
                response = self._post(
                    "/my/timesheet-entries/new",
                    {"task_id": task.id, "date": "2026-11-18", "unit_amount": "1"},
                )
                self.assertIn("You cannot log time on this task", response.text)
        self.assertFalse(self._lines(self.portal))

    def test_hours_are_validated(self):
        self._login(self.portal, "portal_time_pw")
        for hours in ("0", "-2", "30", "abc"):
            with self.subTest(hours=hours):
                response = self._post(
                    "/my/timesheet-entries/new",
                    {
                        "task_id": self.task_followed.id,
                        "date": "2026-11-18",
                        "unit_amount": hours,
                    },
                )
                self.assertIn("alert-danger", response.text)
        self.assertFalse(self._lines(self.portal))

    def test_edit_own_line(self):
        line = self._new_line(self.portal, self.task_followed)
        self._login(self.portal, "portal_time_pw")
        edit_url = f"/my/timesheet-entries/{line.id}/edit"
        self._post(
            edit_url,
            {
                "task_id": self.task_followed.id,
                "date": "2026-11-17",
                "unit_amount": "3",
                "name": "Changed",
            },
            form_url=edit_url,
        )
        self.assertEqual(line.unit_amount, 3.0)
        self.assertEqual(line.name, "Changed")

    def test_cannot_edit_or_delete_other_users_line(self):
        line = self._new_line(self.other_portal, self.task_other)
        self._login(self.portal, "portal_time_pw")
        response = self.url_open(f"/my/timesheet-entries/{line.id}/edit")
        self.assertTrue(
            response.url.rstrip("/").endswith("/my/timesheet-entries"), response.url
        )
        self.assertNotIn("Existing", response.text)
        self._post(
            f"/my/timesheet-entries/{line.id}/delete",
            {},
            form_url="/my/timesheet-entries/new",
        )
        self.assertTrue(line.exists())
        self.assertEqual(line.unit_amount, 2.0)

    def test_delete_requires_post_with_csrf(self):
        line = self._new_line(self.portal, self.task_followed)
        self._login(self.portal, "portal_time_pw")
        delete_url = f"/my/timesheet-entries/{line.id}/delete"
        self.assertEqual(self.url_open(delete_url).status_code, 405)
        self.assertTrue(line.exists())
        response = self.url_open(delete_url, data={"csrf_token": "wrong"})
        self.assertNotEqual(response.status_code, 200)
        self.assertTrue(line.exists())
        self._post(delete_url, {})
        self.assertFalse(line.exists())

    def test_invoiced_line_is_locked(self):
        Line = self.env["account.analytic.line"]
        if "timesheet_invoice_id" not in Line._fields:
            self.skipTest("sale_timesheet is not installed")
        line = self._new_line(self.portal, self.task_followed)
        self.assertFalse(line._portal_timesheet_locked())
        invoice = self.env["account.move"].create(
            {"move_type": "out_invoice", "partner_id": self.portal.partner_id.id}
        )
        line.sudo().timesheet_invoice_id = invoice
        self.assertTrue(line._portal_timesheet_locked())

        self._login(self.portal, "portal_time_pw")
        page = self.url_open("/my/timesheet-entries").text
        self.assertIn("Invoiced", page)
        self.assertNotIn(f"/my/timesheet-entries/{line.id}/edit", page)

        edit = self.url_open(f"/my/timesheet-entries/{line.id}/edit")
        self.assertTrue(
            edit.url.rstrip("/").endswith("/my/timesheet-entries"), edit.url
        )
        delete = self._post(f"/my/timesheet-entries/{line.id}/delete", {})
        self.assertIn("message=locked", delete.url)
        self.assertTrue(line.exists())

        # A cancelled invoice unlocks the line again.
        invoice.button_cancel()
        self.assertFalse(line._portal_timesheet_locked())

    def test_croatian_translation(self):
        self.env["res.lang"]._activate_lang("hr_HR")
        self.env["ir.module.module"]._load_module_terms(
            ["portal_timesheet"], ["hr_HR"], overwrite=True
        )
        self.portal.lang = "hr_HR"
        self._login(self.portal, "portal_time_pw")
        page = self.url_open("/my/timesheet-entries").text
        self.assertIn("Unos sati", page)
