Lets portal users, such as subcontractors or external consultants, log their
working hours on project tasks from the customer portal.

A portal user with **Portal Time Entry** enabled sees a **Time Entry** card on the
portal home page. From there they can log, edit and delete their own hours on tasks
they follow, in projects that allow timesheets. The first entry creates an employee
for the portal user, because Odoo timesheets require one.

Portal users get no direct access rights on timesheets, employees or followers. All
reads and writes go through the portal pages, which check access first. The standard
`/my/timesheets` page of Odoo is not changed.
