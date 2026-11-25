{
    "name": "POS Table Reservation",
    "summary": "Book restaurant tables: date, time, guest and number of people, "
    "shown on the floor plan.",
    "version": "18.0.1.1.1",
    "category": "Sales/Point of Sale",
    "website": "https://www.roosterbit.com.hr",
    "author": "Roosterbit",
    "license": "LGPL-3",
    "depends": ["pos_restaurant"],
    "data": [
        "security/ir.model.access.csv",
        "security/pos_table_reservation_security.xml",
        "views/pos_table_reservation_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "pos_table_reservation/static/src/js/floor_screen.js",
            "pos_table_reservation/static/src/xml/floor_screen.xml",
        ],
        "web.assets_tests": [
            "pos_table_reservation/static/tests/tours/**/*",
        ],
    },
}
