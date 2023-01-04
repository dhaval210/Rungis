{
    'name': 'Topsystem Pick by Voice Async Validate',
    'version': '12.0.1.1.3',
    'summary': 'Topsystem Pick by Voice Async Validate',
    'category': 'Warehouse',
    'author': 'Hucke Media GmBH & Co KG.',
    'maintainer': 'Thore Baden',
    'website': 'https://www.hucke-media.de/',
    'license': 'AGPL-3',
    'depends': [
        'queue_job',
        'tspbv_connector_location_picker',
    ],
    'data': [
        'data/ir_filters.xml',
        'views/res_config_settings.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
