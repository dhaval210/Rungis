{
    'name': 'Metro Rungis Report',
    'version': '12.0.1.1.12',
    'summary': '''
        RUN-150,RUN-167,RUN-226,RUN-241,RUN-272,RUN-295,RUN-283,RUN-308,
        RUN-348,RUN-245,RUN-478,RUN-497,RUN-653,RUN-771
    ''',
    'description': '''
        https://jira.metrosystems.net/browse/RUN-150
        https://jira.metrosystems.net/browse/RUN-167
        https://jira.metrosystems.net/browse/RUN-226
        https://jira.metrosystems.net/browse/RUN-241
        https://jira.metrosystems.net/browse/RUN-272
        https://jira.metrosystems.net/browse/RUN-295
        https://jira.metrosystems.net/browse/RUN-283
        https://jira.metrosystems.net/browse/RUN-308
        https://jira.metrosystems.net/browse/RUN-329
        https://jira.metrosystems.net/browse/RUN-348
        https://jira.metrosystems.net/browse/RUN-245
        https://jira.metrosystems.net/browse/RUN-478
        https://jira.metrosystems.net/browse/RUN-497
        https://jira.metrosystems.net/browse/RUN-653
        https://jira.metrosystems.net/browse/RUN-771
    ''',
    'category': 'Enhancement',
    'author': '''
        Thore Baden, Huckemedia GmbH & Co. KG,
        Cybrosys for METRONOM GmbH
    ''',
    'website': 'https://www.hucke-media.de/',
    'license': 'LGPL-3',
    'depends': [
        'metro_softm_fields',
        'odoo_transport_management',
        'stock',
        'stock_picking_batch',
        'tspbv_connector',
        'tis_catch_weight',
        'report_qweb_element_page_visibility'
    ],
    'data': [
        'reports/label.xml',
        'reports/picking.xml',
        'reports/stock.xml',
        'reports/warehouse4.xml',
        'views/stock_picking_batch.xml',
        'views/stock_inventory_views.xml',
        'views/res_config_settings_views.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
