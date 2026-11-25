from datetime import datetime, time, timedelta

import pytz

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PosTableReservation(models.Model):
    _name = "pos.table.reservation"
    _description = "Table Reservation"
    _order = "start_datetime, id"
    _inherit = ["pos.load.mixin"]

    config_id = fields.Many2one(
        "pos.config",
        string="Point of Sale",
        required=True,
        index=True,
    )
    company_id = fields.Many2one(
        related="config_id.company_id",
        store=True,
        index=True,
    )
    table_id = fields.Many2one(
        "restaurant.table",
        required=True,
        index=True,
    )
    start_datetime = fields.Datetime(string="Date and Time", required=True)
    guest_name = fields.Char(string="Guest", required=True)
    guest_phone = fields.Char(string="Phone")
    guest_count = fields.Integer(string="Guests", default=2, required=True)
    note = fields.Char()
    state = fields.Selection(
        selection=[
            ("booked", "Booked"),
            ("seated", "Seated"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="booked",
        required=True,
    )

    @api.constrains("guest_count")
    def _check_guest_count(self):
        for reservation in self:
            if reservation.guest_count < 1:
                raise ValidationError(
                    self.env._("The number of guests must be at least 1.")
                )

    @api.constrains("table_id", "config_id")
    def _check_table_config(self):
        for reservation in self:
            configs = reservation.table_id.floor_id.pos_config_ids
            if configs and reservation.config_id not in configs:
                raise ValidationError(
                    self.env._(
                        "Table %(table)s is not on point of sale %(config)s.",
                        table=reservation.table_id.display_name,
                        config=reservation.config_id.display_name,
                    )
                )

    def action_seat(self):
        self.filtered(lambda row: row.state == "booked").write({"state": "seated"})

    def action_cancel(self):
        self.filtered(lambda row: row.state == "booked").write({"state": "cancelled"})

    @api.model
    def _today_utc_bounds(self):
        """Start and end of today in the user's time zone, as naive UTC datetimes."""
        tz = pytz.timezone(self.env.context.get("tz") or self.env.user.tz or "UTC")
        today = fields.Datetime.now().replace(tzinfo=pytz.utc).astimezone(tz).date()

        def to_utc(day):
            local = tz.localize(datetime.combine(day, time.min))
            return local.astimezone(pytz.utc).replace(tzinfo=None)

        return to_utc(today), to_utc(today + timedelta(days=1))

    @api.model
    def _load_pos_data_domain(self, data):
        config_id = data["pos.config"]["data"][0]["id"]
        start, end = self._today_utc_bounds()
        return [
            ("config_id", "=", config_id),
            ("state", "=", "booked"),
            ("start_datetime", ">=", start),
            ("start_datetime", "<", end),
        ]

    @api.model
    def _load_pos_data_fields(self, config_id):
        return [
            "config_id",
            "table_id",
            "start_datetime",
            "guest_name",
            "guest_phone",
            "guest_count",
            "note",
            "state",
        ]
