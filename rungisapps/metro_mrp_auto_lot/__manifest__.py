# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Take over LOT dates of Raw Product to Produced Product LOT",
    'summary': "EMO-910",
    'description': """
        - On the BOM-Line, adds a checkbox "Auto Lot Creation". Adds a constraint that only one line of each BOM shall have this checkbox set.
        - On the MO, adds a button left to "Produce": "Generate Lots".
            - When clicked, the system duplicates the lots used in the "Consumed Materials" for the respective line
              (where the checkbox is set on the BOM-Line) and assigns them to the "Finished Products".
     """,
    'category': 'Manufacturing',
    'version': '0.4',
    'depends': ['mrp'],
    'data': [
        'wizard/mrp_product_produce_views.xml',
        'views/mrp_bom_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
