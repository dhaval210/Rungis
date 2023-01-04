# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd. - ©
# Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

{
    'name': 'Metro CW8 Sale Pick Pack Ship',
    'version': '12.0.0.0.6',
    'sequence': 1,
    'category': 'Sales',
    'summary': 'CW Done quantity carried over to next step in multi step routing.',
    'description': """
    From the PICK operation, the value in field "CW Done", to be copied over to PACK Operation > "CW Reserved" field
    Similarly for Putaway operation, From the Pack Operation > the value in field "CW Done", to be copied over to OUT Operation > "CW Reserved" field
    RUN-1178:https://jira.metrosystems.net/browse/RUN-1116 --> Update for intecompany overprocessing
""",
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'website': 'http://www.catchweighterp.com/',
    'currency': 'EUR',
    'license': 'Other proprietary',
    'depends': [
        'tis_catch_weight',
        'metro_lefo_cw',
    ],
    'data': [],
    'qweb': [],
    'images': [],
    'installable': True,
    'auto_install': False,
    'application': True
}
