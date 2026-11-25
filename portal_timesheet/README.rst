=================
Portal Time Entry
=================

.. |badge1| image:: https://img.shields.io/badge/licence-LGPL--3-blue.png
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3
.. |badge2| image:: https://img.shields.io/badge/odoo-18.0-875A7B.png
    :alt: Odoo 18.0

|badge1| |badge2|

Lets portal users, such as subcontractors or external consultants, log their
working hours on project tasks from the customer portal.

A portal user with **Portal Time Entry** enabled sees a **Time Entry** card on the
portal home page. From there they can log, edit and delete their own hours on tasks
they follow, in projects that allow timesheets. The first entry creates an employee
for the portal user, because Odoo timesheets require one.

Portal users get no direct access rights on timesheets, employees or followers. All
reads and writes go through the portal pages, which check access first. The standard
``/my/timesheets`` page of Odoo is not changed.

**Table of contents**

.. contents::
   :local:

Configuration
=============

1. Open the portal user in **Settings > Users** and enable **Portal Time Entry**.
2. Add the portal user's contact as a follower of the tasks they work on.
3. The task's project must have **Timesheets** enabled.

Invoiced entries cannot be changed or deleted from the portal.

Usage
=====

As the portal user:

1. Go to **My Account** and open **Time Entry**.
2. Click **Log Time**, choose the task, date and hours (for example 1.5), add a
   description and save.
3. Use **Edit** or **Delete** on a line to change it. Deleting asks for confirmation.

Hours must be more than 0 and at most 24 per entry. Only open tasks are offered.

Changelog
=========

18.0.2.0.1
----------

- Correct message when deleting an invoiced entry is refused.
- Code style: ruff and pylint-odoo clean.

18.0.2.0.0
----------

- Security: portal users no longer get access rights on employees, followers,
  projects, tasks or timesheets. All changes go through checked portal routes.
- Delete is a POST with CSRF protection instead of a GET link.
- The portal home page and the standard ``/my/timesheets`` page are no longer
  overridden. New routes under ``/my/timesheet-entries``.
- Hours are validated (more than 0, at most 24), only open tasks in projects with
  timesheets are offered, invoiced entries are locked.
- English source texts with a complete Croatian translation.
- Tests for access rights, portal pages, validation, CSRF and translation.

Credits
=======

Authors
-------

- Roosterbit

Contributors
------------

- Roosterbit <https://www.roosterbit.com.hr>
