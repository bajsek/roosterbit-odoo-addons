import * as ChromePos from "@point_of_sale/../tests/tours/utils/chrome_util";
import * as ChromeRestaurant from "@pos_restaurant/../tests/tours/utils/chrome";
import * as FloorScreen from "@pos_restaurant/../tests/tours/utils/floor_screen_util";
import { registry } from "@web/core/registry";

const Chrome = { ...ChromePos, ...ChromeRestaurant };

registry.category("web_tour.tours").add("PosTableReservationFloorTour", {
    steps: () =>
        [
            Chrome.startPoS(),
            FloorScreen.hasTable("4"),
            {
                content: "Table 4 shows today's guest",
                trigger: '.floor-map .table:has(.label:contains("4")):contains("Ana Gost")',
            },
            {
                content: "Table 5 has no reservation",
                trigger: '.floor-map .table:has(.label:contains("5")):not(:contains("Ana Gost"))',
            },
        ].flat(),
});
