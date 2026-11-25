=====================
POS Table Reservation
=====================

.. |badge1| image:: https://img.shields.io/badge/licence-LGPL--3-blue.png
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3
.. |badge2| image:: https://img.shields.io/badge/odoo-18.0-875A7B.png
    :alt: Odoo 18.0

|badge1| |badge2|

Table reservations for the restaurant point of sale in Odoo Community.

A reservation holds the point of sale, table, date and time, guest name, phone,
number of guests and a note. Today's booked reservations are loaded into the point
of sale and the guest name is shown on the floor plan, under the table number.

"Today" follows the user's time zone, so a booking at 00:30 local time is shown on
the right day.

**Table of contents**

.. contents::
   :local:

Configuration
=============

No configuration is required.

- The point of sale must have the restaurant option (floors and tables) enabled.
- A reservation's table must be on a floor of the same point of sale.
- Set the time zone on the point of sale users; "today" is calculated in that zone.

Usage
=====

1. Go to **Point of Sale > Table Reservations** and click **New**.
2. Choose the point of sale and the table, then enter the date and time, the guest
   name and the number of guests.
3. Open the point of sale. Today's reservations show the guest name on the floor
   plan, under the table number.
4. When the guest arrives, click **Seated**. If the booking is called off, click
   **Cancel**. Both remove the name from the floor plan the next time the point of
   sale loads.

Known issues / Roadmap
======================

- Reservations are loaded when the point of sale opens. A reservation made while
  the point of sale is open appears after reloading it.
- The floor plan shows the guest name only; the time is visible in the backend.

Changelog
=========

18.0.1.1.1
----------

- Code style: ruff and pylint-odoo clean.

18.0.1.1.0
----------

- Reservations are now loaded into the point of sale, so guest names appear on the
  floor plan.
- "Today" follows the user's time zone instead of UTC.
- Validation errors instead of user errors for wrong data.
- Company field and multi-company record rule.
- English source texts with a complete Croatian translation.
- Search view with Booked and Today filters.
- More tests: loading, time zone, cancel, other point of sale, translation and
  multi-company.

Credits
=======

Authors
-------

- Roosterbit

Contributors
------------

- Roosterbit <https://www.roosterbit.com.hr>
