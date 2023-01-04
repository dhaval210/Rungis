{
    'name': 'Topsystem Pick by Voice Transport Unit Addon',
    'version': '12.0.1.2.1',
    'summary': 'Topsystem Pick by Voice Transport Unit Addon',
    'category': 'Warehouse',
    'author': 'Hucke Media GmBH & Co KG.',
    'maintainer': 'Thore Baden',
    'website': 'https://www.hucke-media.de/',
    'license': 'AGPL-3',
    'depends': [
        'metro_rungis_report',
        'metro_split_picking',
        'tspbv_connector',
    ],
    'data': [
        'data/tspbv_dialoglist_transport_unit.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
