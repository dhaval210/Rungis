# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd. - ©
# Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

{
    'name': 'Metro PO Confirm',
    'version': '12.0.0.0.0',
    'sequence': 1,
    'category': 'Purchase',
    'summary': 'Check CW-UOM in PO Lines While Confirm PO',
    'description': """
    Check CW-UOM category in Purchase Order lines with CW-UOM category in Product form.Also shows Warning accordingly.
   """,
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'website': 'http://www.catchweighterp.com/',
    'currency': 'EUR',
    'license': 'Other proprietary',
    'depends': [
        'tis_catch_weight'
    ],
    'data': [],
    'qweb': [],
    'images': [],
    'installable': True,
    'auto_install': False,
    'application': True
}
