{
    "name": "Statement of Open Items (IOS)",
    "summary": "Open receivables and payables on a date, PDF letter with "
    "OIB and IBAN, partner confirmation.",
    "version": "18.0.1.2.0",
    "category": "Accounting/Accounting",
    "website": "https://www.roosterbit.com.hr",
    "author": "Roosterbit",
    "license": "LGPL-3",
    "depends": ["account", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "security/account_ios_security.xml",
        "data/sequence.xml",
        "wizard/ios_prepare_views.xml",
        "views/account_ios_views.xml",
        "views/res_partner_views.xml",
        "views/menus.xml",
        "views/res_config_settings_views.xml",
        "report/ios_report.xml",
        "report/ios_templates.xml",
    ],
}
