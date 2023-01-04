# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Devintelle Software Solutions (<http://devintellecs.com>).
#
##############################################################################
{
    'name': 'Advance Date Filter & Date Group by',
    'version': '12.0.1.1',
    'sequence': 1,
    'category': 'Generic Modules/Sales Management',
    'summary': 'odoo app will add filter Yearsterday, Today, Last 7 Days, Last 30 Days, This Year Filter and Group by Filter with Week, Month, Year in Sale,Purchase,Invoice,Picking,Payments, Journal Items , Journal Entries and Inventory Adjustment,RUN-256',
    'description': """
        RUN-256: https://jira.metrosystems.net/browse/RUN-256,
         odoo app will Add filter Yearsterday, Today, Last 7 Days, Last 30 Days, This Year Filter and Group by Filter with Week, Month, Year in Sale Order, Purchase Order, Account Invoice, Stock Picking, Account Payment, Journal Items , Journal Entries and Inventory Adjustment
        
        Today Date filter, Date filter, Yester date filter, week filter, last 7 days filter, month date filter, last 30 dayes date filter,
        whole year date filter, this year date filter , current date filter, 
        
        Current day group by date filter, Today date group by filter, last 7 days date group by filter, last month group by date filter, last 30 days month filter, last year group by date filter, last 365 days group by date filter
        
Advance date filter
Advance date filter odoo
Create advance date filter 
Easily create advance date filter
Create advance date filter in odoo
Easily create advance date filter
Advance date filter and date group by
Date filtering
Date filtering odoo
Sales order date filtering
Purchase order date filtering
Date filter
Date filter odoo
Point of Sale filter by Today, Yesterday, Current Week, Previous Week, Current Month, Previous Month, Current Year, Previous Year.
Group By Day, Week, Month, Year
Date filtration
Odoo date filtration
Odoo advance date filter
Easily create advance date filter and dte group by
Easily create sales advance date filter        
        
    """,
    'author': 'DevIntelle Consulting Service Pvt.Ltd,Cybrosys for METRONOM GmbH',
    'website': 'http://www.devintellecs.com/',
    'depends': ['sale_management', 'purchase', 'sale_stock', 'account', 'stock'],
    'data': [
        'views/dev_view.xml',
    ],
    'demo': [],
    'test': [],
    'css': [],
    'qweb': [],
    'js': [],
    'images': ['images/main_screenshot.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'price':25.0,
    'currency':'EUR',
    'live_test_url':'https://youtu.be/8Q2x5xcxZJ0',   
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
