# Roosterbit Odoo Addons

Odoo 18 modules by Roosterbit that extend standard Odoo features. Each module
depends only on standard Odoo (Community or Enterprise) and can be installed on its
own.

## Modules

| Module | Version | What it does | Depends on | Guide |
|---|---|---|---|---|
| [`account_ios_hr`](account_ios_hr) | 18.0.1.2.0 | Statement of open items (IOS): open receivables and payables on a date, letter in the partner's language, configurable reply deadline, partner confirmation | `account`, `mail` | [Statement of Open Items](docs/Statement_of_Open_Items.md) |
| [`pos_table_reservation`](pos_table_reservation) | 18.0.1.1.1 | Table reservations for the restaurant point of sale, guest name on the floor plan | `pos_restaurant` | [POS Table Reservation](docs/POS_Table_Reservation.md) |
| [`portal_timesheet`](portal_timesheet) | 18.0.2.0.1 | Portal users log their hours on the tasks they follow, without direct access rights | `hr_timesheet`, `portal` | [Portal Time Entry](docs/Portal_Time_Entry.md) |

All modules are licensed under LGPL-3 and come with an English source and a
complete Croatian translation.

## Installation

1. Clone the branch that matches your Odoo version:

   ```bash
   git clone -b 18.0 <repository-url> roosterbit-odoo-addons
   ```

2. Add the folder to `addons_path` in the Odoo configuration.
3. Restart Odoo, update the apps list and install the module you need.

No extra Python packages are required.

## Tests

Each module has automated tests. Run them on a test database:

```bash
odoo -d <database> -i <module> --test-enable --test-tags /<module> --stop-after-init
```

The browser test of `pos_table_reservation` needs Chrome; without it Odoo skips
that test.

## Development

- Code style: `pre-commit` with ruff and pylint-odoo (`pip install pre-commit`,
  then `pre-commit install`).
- Continuous integration: `.github/workflows/ci.yml` runs pre-commit, installs the
  modules, checks licenses and runs the tests with coverage.
- Each module documents its configuration, usage and changelog in `readme/` and
  `README.rst`.

## Versions

| Branch | Odoo |
|---|---|
| `18.0` | 18.0 |

## License

LGPL-3. See [`LICENSE`](LICENSE) and [`licenses/`](licenses/).

## Contact

Roosterbit, https://www.roosterbit.com.hr
