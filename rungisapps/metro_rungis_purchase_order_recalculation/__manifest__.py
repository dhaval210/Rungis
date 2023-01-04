# -*- coding: utf-8 -*-
{
    'name': "metro_rungis_purchase_order_recalculation",
    'version': '12.0.1.0.7',
    'summary': "RUN-958",
    'description': """RUN-958 : Exchange order quantities on order / delivery / logistic unit level""",
    'author': "Wipro Technologies - Abhay Singh Rathore",
    'website': 'https://www.wipro.com/',
    'category': 'Purchases',
    'depends': ['base', 'purchase', 'tis_catch_weight', 'metro_rungis_purchase_order_report'],
    'data': [
        'views/views.xml',
   ],
}
