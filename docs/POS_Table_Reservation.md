# POS Table Reservation

Module `pos_table_reservation`, version 18.0.1.1.1. Depends only on the standard
Odoo module `pos_restaurant`. License LGPL-3.

Odoo Community has no table reservations (they are part of the Enterprise
*Appointments* app). This module adds simple reservations that are shown on the
floor plan of the restaurant point of sale.

---

## 1. Setup

| What | Where |
|---|---|
| Restaurant mode (floors and tables) | Point of Sale → Configuration → Settings → *Restaurant* |
| Time zone of the point of sale users | Settings → Users → user → *Preferences* → Timezone |

"Today" is calculated in the user's time zone. Without a time zone, UTC is used and
reservations around midnight may appear on the wrong day.

---

## 2. New reservation

1. **Point of Sale → Table Reservations → New**.
2. Choose the **Point of Sale** and the **Table**. Only tables on the floors of that
   point of sale are offered.
3. Enter **Date and Time**, **Guest**, **Phone**, **Guests** (number of people) and
   an optional **Note**.
4. Save.

Rules:
- the number of guests must be at least 1;
- the table must belong to the selected point of sale.

---

## 3. At the point of sale

When the point of sale opens, it loads **today's** reservations in status *Booked*.
The guest name is shown on the floor plan under the table number.

A reservation created while the point of sale is open appears after the point of
sale is reloaded (refresh the browser).

---

## 4. Statuses

| Status | Button | On the floor plan |
|---|---|---|
| **Booked** | — | yes, if today |
| **Seated** | **Seated** | no |
| **Cancelled** | **Cancel** | no |

The list is filtered on **Booked** by default. The **Today** filter and grouping by
day help with the daily overview.

---

## 5. Multi-company

The company of a reservation is the company of its point of sale. Users see only
reservations of the companies selected for them.

---

## 6. Troubleshooting

| Problem | Cause and fix |
|---|---|
| The guest name is not on the floor plan | The reservation is not for today, not *Booked*, or was created after the point of sale opened. Reload the point of sale. |
| A reservation near midnight is on the wrong day | Set the time zone of the point of sale user. |
| "Table … is not on point of sale …" | Choose a table from a floor of the selected point of sale. |
| "The number of guests must be at least 1" | Enter 1 or more guests. |

---

## 7. Technical notes

| Item | Where |
|---|---|
| Model `pos.table.reservation` | `models/pos_table_reservation.py` |
| "Today" in the user's time zone | `_today_utc_bounds()` |
| Loading into the point of sale | `pos.session._load_pos_data_models` in `models/pos_session.py` |
| Floor plan display | `static/src/js/floor_screen.js`, `static/src/xml/floor_screen.xml` |
| Browser test (tour) | `static/tests/tours/table_reservation_tour.js` |
| Translations | `i18n/pos_table_reservation.pot`, `i18n/hr.po` |

### Tests

- `tests/test_reservation.py`, 10 tests: loading through a real POS session,
  today's reservations until seated, cancelled not loaded, user time zone, other
  point of sale, validation, company, multi-company, Croatian translation.
- `tests/test_floor_tour.py`, 1 browser test: opens the point of sale and checks the
  guest name on the right table. It needs Chrome and the Python package
  `websocket-client`; without them Odoo skips it.

Run on a test database:

```bash
odoo -d <database> -i pos_table_reservation --test-enable \
  --test-tags /pos_table_reservation --stop-after-init
```
