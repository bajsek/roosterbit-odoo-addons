import { patch } from "@web/core/utils/patch";
import { FloorScreen } from "@pos_restaurant/app/floor_screen/floor_screen";

patch(FloorScreen.prototype, {
    /** Today's booked reservation for the table, if any. */
    tableReservation(table) {
        const reservations = this.pos.models["pos.table.reservation"]?.getAll() || [];
        return reservations.find(
            (row) => row.table_id?.id === table.id && row.state === "booked"
        );
    },
});
