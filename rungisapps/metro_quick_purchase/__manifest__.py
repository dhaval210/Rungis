# -*- coding: utf-8 -*-
{
    'name': 'Metro Quick Purchase',
    'version': '12.0.1.0.12',
    'category': 'Purchases',
    'summary': "RUN-947",
    'description': """
     1. Press select items button at order line on Purchase order
     2. Select products can be purchased only and vendor specific products by entering the required qty and press apply button on wizard
     3. Add bulk products to Purchase line.
    
    RUN-947 :https://jira.metrosystems.net/browse/RUN-947""",
    'author': 'Wipro Technologies - Abhay Singh Rathore',
    'website': 'https://www.wipro.com/',
    'license': 'AGPL-3',
    'depends': ['base', 'product','purchase','stock'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/po_line_select_product_wiz_view.xml',
        'views/purchase_view.xml',
    ],
}