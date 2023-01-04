# -*- coding: utf-8 -*-
# Copyright 2019 Linksoft Mitra Informatika
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
# noinspection PyUnresolvedReferences,SpellCheckingInspection
{
    "name": """Wide Form View Full Width Sheet""",
    "summary": """Turn form view to full width on the screen""",
    "category": "Tools",
    "version": "12.0.0.1.0",
    "development_status": "Alpha",  # Options: Alpha|Beta|Production/Stable|Mature
    "auto_install": False,
    "installable": True,
    "application": False,
    "author": "Linksoft Mitra Informatika",
    "support": "support@linksoft.id",
    "website": "https://linksoft.id",
    "license": "OPL-1",
    "images": [
        'images/main_screenshot.png'
    ],

    "price": 15.00,
    "currency": "EUR",

    "depends": [
        # odoo addons
        'base',
        # third party addons

        # developed addons
    ],
    "data": [
        # group

        # data

        # action
        # 'views/action.xml',

        # view

        # report

        # assets
        'views/assets.xml',

        # wizard

        # onboarding

        # action menu
        # 'views/action_menu.xml',

        # action onboarding
        # 'views/action_onboarding.xml',

        # menu
        # 'views/menu.xml',

        # security
        # 'security/ir.model.access.csv',

        # data
    ],
    "demo": [
        # 'demo/demo.xml',
    ],
    "qweb": [
        # "static/src/xml/{QWEBFILE1}.xml",
    ],

    "post_load": None,
    "pre_init_hook": None,
    "post_init_hook": None,
    "uninstall_hook": None,

    "external_dependencies": {"python": [], "bin": []},
    # "live_test_url": "",
    # "demo_title": "{MODULE_NAME}",
    # "demo_addons": [
    # ],
    # "demo_addons_hidden": [
    # ],
    # "demo_url": "DEMO-URL",
    # "demo_summary": "{SHORT_DESCRIPTION_OF_THE_MODULE}",
    # "demo_images": [
    #    "images/MAIN_IMAGE",
    # ]
}
