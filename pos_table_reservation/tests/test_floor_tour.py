from datetime import timedelta

from odoo import fields
from odoo.tests import tagged

from odoo.addons.pos_restaurant.tests.test_frontend import TestFrontendCommon


@tagged("post_install", "-at_install")
class TestPosTableReservationTour(TestFrontendCommon):
    def test_guest_name_on_floor_plan(self):
        table = self.env["restaurant.table"].search(
            [
                ("floor_id.pos_config_ids", "in", self.pos_config.ids),
                ("table_number", "=", 4),
            ],
            limit=1,
        )
        self.env["pos.table.reservation"].create(
            {
                "config_id": self.pos_config.id,
                "table_id": table.id,
                "start_datetime": fields.Datetime.now() + timedelta(minutes=30),
                "guest_name": "Ana Gost",
                "guest_count": 2,
            }
        )
        self.pos_config.with_user(self.pos_user).open_ui()
        # Open the session up front so no opening-control dialog covers the floor.
        self.pos_config.current_session_id.set_opening_control(0, "")
        self.start_pos_tour("PosTableReservationFloorTour")
