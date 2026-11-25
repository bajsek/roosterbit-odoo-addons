## 18.0.2.0.1

- Correct message when deleting an invoiced entry is refused.
- Code style: ruff and pylint-odoo clean.

## 18.0.2.0.0

- Security: portal users no longer get access rights on employees, followers,
  projects, tasks or timesheets. All changes go through checked portal routes.
- Delete is a POST with CSRF protection instead of a GET link.
- The portal home page and the standard `/my/timesheets` page are no longer
  overridden. New routes under `/my/timesheet-entries`.
- Hours are validated (more than 0, at most 24), only open tasks in projects with
  timesheets are offered, invoiced entries are locked.
- English source texts with a complete Croatian translation.
- Tests for access rights, portal pages, validation, CSRF and translation.
