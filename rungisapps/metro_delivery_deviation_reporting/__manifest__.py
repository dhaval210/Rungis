# -*- coding: utf-8 -*-
{
    'name': "Metro Delivery Deviation Reporting",

    'summary': """EMO-1169, EMO-1170,RUN-257, RUN-571""",

    'description': """**Set up the module**

To make sure the delivery deviations are reported correctly you need to go to the Sales settings **Sales App -> Configuration -> Settings**.

Scroll down to the **"Quotations & Orders"** section.

At the button you'll be able to see the **"Maximum Allowed Delivery Time" and the "Timezone" setting**.

Please set a value to the Maximum Allowed Delivery Time which is greater than 0 and less than 24 hours.
In the "Timezone" dropdown please choose your timezone.

        EMO-1169: This module allows you to get an email when  
                  products are missing, product quantities changed or delivery delays
                  occur while packing the sale orders
                  
        RUN-257:https://jira.metrosystems.net/browse/RUN-257 """,


    'author': "Odoo PDA, Cybrosys for METRONOM GmbH",
    'website': "http://www.odoo.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'sale',
    'version': '12.0.2.0.13',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        "sale_management",
        "stock",
        "metro_shipment_tour",
    ],

    # always loaded
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'views/sale_conf_view.xml',
        'views/packing_details_view.xml',
    ],
}