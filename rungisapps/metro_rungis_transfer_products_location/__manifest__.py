# -*- coding: utf-8 -*-
{
    'name': "Transfer products between locations",
    'summary': """RUN-886, RUN-904, RUN-971""",
    'description': """
        This module introduces a wizard which will enable the user to transfer products between locations.
        Runs:
        * https://jira.metrosystems.net/browse/RUN-886
        * https://jira.metrosystems.net/browse/RUN-904
        * https://jira.metrosystems.net/browse/RUN-971
    """,

    'author': "Niklas Hucke - Hucke Media GmbH & Co KG",
    'website': "http://www.hucke-media.de",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'stock',
    'version': '12.0.1.2.5',

    # any module necessary for this one to work correctly
    'depends': [
        'stock',
        "tis_catch_weight"
    ],

    # always loaded
    'data': [
        "security/security.xml",
        "views/assets.xml",
        "wizard/wizard_transfer_products_location.xml",
    ],
}
