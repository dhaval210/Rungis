# -*- coding: utf-8 -*-
{
	'name': 'Sticky Pivot View',

	'summary': """
Enhance the default Odoo Pivot View by sticking the Pivot View Header and its first Column.
""",

	'description': """
Enhance the default Odoo Pivot View by sticking the Pivot View Header and its first Column.
        Pivot View
        Sticky Pivot View
        Odoo Sticky Pivot View
        Odoo Pivot View
        Web List View Sticky Header
        Odoo Sticky Header
        Pivot View Sticky Header
        Sticky Header
        Sticky Pivot View Header
        Sticky Pivot View Column
        Freeze Pivot View
""",

	'author': 'Ksolves India Ltd.',

	'website': 'https://www.ksolves.com/',

	'support': 'sales@ksolves.com',

	'license': 'OPL-1',

	'currency': 'EUR',

	'price': 39.2,

	'category': 'Tools',

	'version': '1.0.2',

	'live_test_url': 'https://stickypivotview.kappso.com/web/demo_login',

	'images': ['static/description/event_banner.gif'],

	'depends': ['base', 'web', 'base_setup'],

	'data': ['data/ks_data_ir_config_parameter.xml', 'views/ks_assets.xml', 'views/ks_inherited_res_config.xml'],

	'uninstall_hook': 'uninstall_hook',
}
