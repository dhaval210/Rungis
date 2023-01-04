# -*- coding: utf-8 -*-
{
    'name': "Purchase Orders: Delivery Deviation Reporting",

    'summary': """EMO-1289""",

    'description': """
    This module detects delivery deviations on purchase order.
    You can configure a tolerance in the settings for the scheduled date.

    It runs a cron job in the background which automatically checks for deviated orders and reports them.

    A deviated purchase order is an order where:
        * The Effective date is after the scheduled date + tolerance
        * Product Quantities Changed
        * Products are missing
    """,

    'author': "Odoo PDA",
    'website': "http://www.odoo.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'purchase',
    'version': '12.0.1.0.4',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        "purchase",
        "stock",
    ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        "data/cron_job.xml",
        "views/purchase_conf.xml",
        "views/purchase_order_deviation.xml",
    ],
    # only loaded in demonstration mode
    'demo': [
        
    ],
}