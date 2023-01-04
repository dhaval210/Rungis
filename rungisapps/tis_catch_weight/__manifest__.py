# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

{
    'name': 'CatchWeight Management',
    'version': '12.0.2.6.8',
    'sequence': 1,
    'category': 'Inventory',
    'summary': 'Catchw8 - Catch Weight Management - Dual Units of Measure',
    'description': """
    This module is for activating Catch weight management
""",
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'website': 'http://www.catchweighterp.com/',
    'price': 699,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'depends': [
        'sale_stock',
        'account',
        'sale_management',
        'purchase',
    ],
    'data': [
        'security/catch_weight_security.xml',
        'views/product_views.xml',
        'views/sale_views.xml',
        'views/purchase_views.xml',
        'views/account_invoice_view.xml',
        'views/stock_picking_views.xml',
        'views/stock_scrap_views.xml',
        'views/stock_move_line_views.xml',
        'views/stock_move_view.xml',
        'views/res_config_settings_views.xml',
        'views/stock_inventory.xml',
        'views/stock_quant_views.xml',
        'views/stock_production_lot.xml',
        'views/product_category_views.xml',
        'wizard/stock_picking_return_view.xml',
        'wizard/stock_change_product_qty.xml',
        'wizard/set_cw_multiple_products.xml',
        'wizard/stock_warn_insufficient_qty_views.xml',
        'report/sale_report_template.xml',
        'report/purchase_order_templates.xml',
        'report/purchase_quotation_templates.xml',
        'report/report_invoice.xml',
        'report/report_stockpicking_operations.xml',
        'report/report_deliveryslip.xml',
        'report/report_stock_forecast.xml',
        'report/report_stock_traceability.xml',
        'data/product_data.xml'
    ],
    'images': ['images/main_screenshot.png'],
    'installable': True,
    'auto_install': False,
    'application': True

}
