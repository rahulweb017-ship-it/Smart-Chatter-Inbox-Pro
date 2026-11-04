{
    "name": "Smart Chatter Inbox Pro",
    "summary": "CRM follow-up queue: Needs Action, Waiting, Done and Snoozed with owners, filters and one-click chatter",
    "version": "20.0.1.0.0",
    "category": "Sales/CRM",
    "author": "Softdeviser",
    "website": "https://softdeviser.com",
    "support": "rahul@softdeviser.com",
    "license": "OPL-1",
    "price": 19.0,
    "currency": "USD",
    "depends": ["base", "web", "mail", "crm"],
    "data": [
        "security/security_groups.xml",
        "views/crm_inbox_actions.xml",
        "views/crm_inbox_menu.xml",
        "views/crm_lead_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "sd_smart_chatter_inbox/static/src/js/**/*.js",
            "sd_smart_chatter_inbox/static/src/xml/**/*.xml",
            "sd_smart_chatter_inbox/static/src/scss/**/*.scss",
        ],
        "web.assets_unit_tests": [
            "sd_smart_chatter_inbox/static/tests/**/*.test.js",
        ],
        "web.assets_tests": [
            "sd_smart_chatter_inbox/static/tests/tours/**/*.js",
        ],
    },
    "images": ["static/description/banner.png"],
    "installable": True,
    "application": False,
}
