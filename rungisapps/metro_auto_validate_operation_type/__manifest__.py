{
    'name': 'Auto Validation of Operation Types',
    'version': '12.0.1.0.8',
    'summary': """
        RUN-357
    """,
    'description': """
        https://jira.metrosystems.net/browse/RUN-357,
    """,
    'category': 'Inventory',
    'author': 'Thore Baden, Hucke Media GmbH & Co KG',
    'website': 'https://www.hucke-media.de/',
    'license': 'LGPL-3',
    'depends': [
        'stock',
        # temp dependency should be removed in the future
        'sync_quality_control',
    ],
    'data': [
        'data/res_config_settings_data.xml',
        'views/res_config_settings.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
