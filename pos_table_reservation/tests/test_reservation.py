from datetime import datetime, timedelta

from freezegun import freeze_time

from odoo import Command, fields
from odoo.exceptions import ValidationError
from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestPosTableReservation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Reservation = cls.env["pos.table.reservation"]
        cls.config = cls._create_config("Restaurant test")
        cls.floor = cls.env["restaurant.floor"].create(
            {"name": "Main room", "pos_config_ids": [Command.set(cls.config.ids)]}
        )
        cls.table = cls.env["restaurant.table"].create(
            {"table_number": 4, "floor_id": cls.floor.id, "seats": 4}
        )

    @classmethod
    def _create_config(cls, name):
        journal = cls.env["account.journal"].search(
            [("type", "=", "sale"), ("company_id", "=", cls.env.company.id)], limit=1
        )
        return cls.env["pos.config"].create(
            {
                "name": name,
                "journal_id": journal.id,
                "invoice_journal_id": journal.id,
                "module_pos_restaurant": True,
            }
        )

    def _reserve(self, start, **values):
        return self.Reservation.create(
            {
                "config_id": self.config.id,
                "table_id": self.table.id,
                "start_datetime": start,
                "guest_name": "Ana",
                "guest_count": 3,
                **values,
            }
        )

    def _loaded(self):
        data = {"pos.config": {"data": [{"id": self.config.id}]}}
        return self.Reservation.search(self.Reservation._load_pos_data_domain(data))

    def test_loaded_into_restaurant_pos(self):
        reservation = self._reserve(fields.Datetime.now() + timedelta(minutes=5))
        session = self.env["pos.session"].create(
            {"config_id": self.config.id, "user_id": self.env.uid}
        )
        data = session.load_data(
            [
                "pos.config",
                "restaurant.floor",
                "restaurant.table",
                "pos.table.reservation",
            ]
        )
        rows = data["pos.table.reservation"]["data"]
        self.assertEqual([row["id"] for row in rows], reservation.ids)
        self.assertEqual(rows[0]["table_id"], self.table.id)

    def test_today_reservation_until_seated(self):
        reservation = self._reserve(fields.Datetime.now() + timedelta(minutes=5))
        self.assertIn(reservation, self._loaded())
        reservation.action_seat()
        self.assertEqual(reservation.state, "seated")
        self.assertNotIn(reservation, self._loaded())

    def test_cancelled_reservation_is_not_loaded(self):
        reservation = self._reserve(fields.Datetime.now() + timedelta(minutes=5))
        reservation.action_cancel()
        self.assertEqual(reservation.state, "cancelled")
        self.assertNotIn(reservation, self._loaded())
        # Seating a cancelled reservation does nothing.
        reservation.action_seat()
        self.assertEqual(reservation.state, "cancelled")

    @freeze_time("2026-07-15 10:00:00")
    def test_today_follows_user_time_zone(self):
        # Zagreb is UTC+2 in July.
        self.env.user.tz = "Europe/Zagreb"
        just_after_midnight = self._reserve(datetime(2026, 7, 14, 22, 30))
        late_evening = self._reserve(datetime(2026, 7, 15, 21, 30))
        tomorrow = self._reserve(datetime(2026, 7, 15, 22, 30))
        yesterday = self._reserve(datetime(2026, 7, 14, 21, 30))
        loaded = self._loaded()
        self.assertIn(just_after_midnight, loaded)
        self.assertIn(late_evening, loaded)
        self.assertNotIn(tomorrow, loaded)
        self.assertNotIn(yesterday, loaded)

    def test_other_pos_is_not_loaded(self):
        other_config = self._create_config("Restaurant test 2")
        self.floor.pos_config_ids = [Command.link(other_config.id)]
        reservation = self._reserve(
            fields.Datetime.now() + timedelta(minutes=5), config_id=other_config.id
        )
        self.assertNotIn(reservation, self._loaded())

    def test_guest_count_must_be_positive(self):
        with self.assertRaises(ValidationError):
            self._reserve(fields.Datetime.now(), guest_count=0)

    def test_table_must_belong_to_pos(self):
        other_config = self._create_config("Restaurant test 3")
        with self.assertRaises(ValidationError):
            self._reserve(fields.Datetime.now(), config_id=other_config.id)

    def test_company_follows_pos(self):
        reservation = self._reserve(fields.Datetime.now())
        self.assertEqual(reservation.company_id, self.config.company_id)

    def test_croatian_translation(self):
        self.env["res.lang"]._activate_lang("hr_HR")
        self.env["ir.module.module"]._load_module_terms(
            ["pos_table_reservation"], ["hr_HR"], overwrite=True
        )
        field = self.env["ir.model.fields"]._get("pos.table.reservation", "guest_count")
        self.assertEqual(
            field.with_context(lang="hr_HR").field_description, "Broj osoba"
        )
        with self.assertRaisesRegex(ValidationError, "Broj osoba mora biti barem 1"):
            self.Reservation.with_context(lang="hr_HR").create(
                {
                    "config_id": self.config.id,
                    "table_id": self.table.id,
                    "start_datetime": fields.Datetime.now(),
                    "guest_name": "Ana",
                    "guest_count": 0,
                }
            )

    def test_other_company_user_does_not_see_reservation(self):
        reservation = self._reserve(fields.Datetime.now())
        other_company = self.env["res.company"].create({"name": "Other restaurant"})
        user = new_test_user(
            self.env,
            login="reservation_other_company",
            groups="point_of_sale.group_pos_user",
            company_id=other_company.id,
            company_ids=[Command.set(other_company.ids)],
        )
        found = self.Reservation.with_user(user).search([("id", "=", reservation.id)])
        self.assertFalse(found)
