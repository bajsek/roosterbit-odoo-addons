# Portal Time Entry

Module `portal_timesheet`, version 18.0.2.0.1. Depends only on the standard Odoo
modules `hr_timesheet` and `portal`. License LGPL-3.

External people, such as subcontractors or consultants, log their working hours on
project tasks from the customer portal. They do not need an internal Odoo user.

---

## 1. Setup (administrator)

### 1.1 Give the person portal access

1. Open the person's contact.
2. **Action → Grant portal access**, then send the invitation.
3. The person sets a password and can log in at `/my`.

### 1.2 Enable time entry for the portal user

1. **Settings → Users & Companies → Users**. Remove the default *Internal Users*
   filter to see portal users.
2. Open the portal user and tick **Portal Time Entry**. The field is shown only for
   portal users.

### 1.3 Give the user tasks

1. The task's project must have **Timesheets** enabled (project settings).
2. On each task the person works on, add their contact as a **follower**.

Only open tasks are offered. Tasks that are done or cancelled disappear from the
list.

### 1.4 Employee record

Odoo cannot save a timesheet without an employee. The first time a portal user
logs time, the module creates an employee with the user's name in the task's
company. Nothing has to be set up by hand. The employee can be edited later in
**Employees** like any other.

---

## 2. Logging time (portal user)

1. Log in and open **My Account** (`/my`).
2. Open the **Time Entry** card (`/my/timesheet-entries`).
3. Click **Log Time**.
4. Choose the **Task**, pick the **Date** in the calendar, enter the **Hours** and
   an optional **Description**.
   - Hours are decimal: `1.5` is one hour and a half, `0.25` is fifteen minutes.
5. Click **Save**. The list shows the entry with date, project, task, hours and
   description.

To change an entry, click **Edit**. To remove it, click **Delete** and confirm.

### Rules

| Rule | What the user sees |
|---|---|
| Hours must be more than 0 and at most 24 per entry | an error above the form, nothing is saved |
| The date is required | an error above the form |
| Only tasks the user follows or is assigned to, in projects with timesheets | other tasks are not offered and are refused |
| Only the user's own entries can be edited or deleted | other entries are not reachable |
| Invoiced entries are locked | **Invoiced** badge instead of Edit and Delete |

An entry is invoiced when it is linked to a customer invoice that is not cancelled
(module `sale_timesheet`). If the invoice is cancelled, the entry can be changed
again.

---

## 3. Reviewing the hours (internal user)

Portal entries are normal timesheets. They appear in:

- **Timesheets → All Timesheets**, filtered or grouped by employee;
- the **Timesheets** tab of the task;
- project reports and, with `sale_timesheet`, invoicing.

The standard portal page `/my/timesheets` (timesheets of shared projects) is not
changed by this module.

---

## 4. Security

The portal user has **no direct access rights** on timesheets, employees,
followers, projects or tasks through this module. Every read and write goes
through the portal pages, which check access first and then act on the user's
behalf.

- Time can only be logged on tasks the user follows or is assigned to.
- Only the user's own entries can be changed or deleted.
- Delete works only through a form protected by a CSRF token. A plain link cannot
  delete anything.
- The user cannot reach these pages when **Portal Time Entry** is off.

---

## 5. Troubleshooting

| Problem | Cause and fix |
|---|---|
| The **Time Entry** card is missing on `/my` | **Portal Time Entry** is not ticked on the user (1.2). |
| "There are no tasks on which you can log time" | The user follows no open task in a project with timesheets (1.3). |
| "You cannot log time on this task" | The task was closed, the follower was removed, or the project no longer allows timesheets. |
| Edit and Delete are missing on a line | The line is invoiced. Cancel the invoice or correct it internally. |
| Old bookmarks such as `/my/timesheet/create` return "page not found" | The addresses changed in 18.0.2.0.0. Use `/my/timesheet-entries`. |

---

## 6. Changes in 18.0.2.0.0

| Before (18.0.1.0.0) | Now |
|---|---|
| Portal users could read, edit and create **all employees** | no access |
| Portal users could read all followers in the database | no access |
| Portal users saw other people's hours on their tasks | own entries only |
| Delete was a GET link without CSRF protection | POST form with CSRF token |
| The module replaced `/my` and `/my/timesheets` | both untouched, own routes under `/my/timesheet-entries` |
| No validation of hours, any task | 0 < hours ≤ 24, only open tasks in projects with timesheets |
| Texts in Croatian only | English source with a complete Croatian translation |
| No tests | 13 tests |

When upgrading, Odoo removes the old access rights and record rules automatically.
Existing timesheets and employees of portal users are kept.

---

## 7. Technical notes

| Item | Where |
|---|---|
| Routes `/my/timesheet-entries`, `/new`, `/<id>/edit`, `/<id>/delete` (POST only) | `controllers/portal_timesheet.py` |
| Tasks offered to a portal user | `project.task._portal_timesheet_tasks(user)` |
| Invoiced lock | `account.analytic.line._portal_timesheet_locked()` |
| User switch | `res.users.portal_timesheet_enabled` |
| Templates | `views/portal_timesheet_templates.xml` |
| Translations | `i18n/portal_timesheet.pot`, `i18n/hr.po` |

### Tests

`tests/test_portal_timesheet.py`, 13 tests:

- no direct access rights for portal users;
- tasks offered (followed, open, project with timesheets);
- portal home card only when enabled; disabled user redirected;
- standard `/my/timesheets` untouched;
- logging time creates the line and the employee;
- refused on other tasks; hours validated;
- edit own line; no access to other users' lines;
- delete only by POST with a valid CSRF token;
- invoiced lines locked (skipped when `sale_timesheet` is not installed);
- Croatian translation.

Run on a test database:

```bash
odoo -d <database> -i portal_timesheet --test-enable \
  --test-tags /portal_timesheet --stop-after-init
```
