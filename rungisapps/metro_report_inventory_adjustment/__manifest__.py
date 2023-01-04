{
    'name': 'Inventory Adjustment Report',
    'version': '12.0.1.0.1',
    'summary': ' EMO-769 ',
    'description': 'EMO-769:This module allows to print report from '
                   'inventory Adjustment',
    'author': ' Odoo PDA',
    'category': 'Inventory',
    'depends': [
        'stock',
        'stock_inventory_chatter',
        'stock_inventory_discrepancy',
        'stock_inventory_exclude_sublocation',
        'stock_inventory_lockdown'],
    'data': [
        'views/report_valuation_view.xml',
        'report/inventory_adjustment_report.xml',
        'views/report_stock_inventory.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
}
