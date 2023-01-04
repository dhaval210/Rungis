{
    'name': 'Topsystem Pick by Voice Location Picker',
    'version': '12.0.1.2.2',
    'summary': 'Topsystem Pick by Voice Location Picker',
    'category': 'Warehouse',
    'author': 'Hucke Media GmBH & Co KG.',
    'maintainer': 'Thore Baden',
    'website': 'https://www.hucke-media.de/',
    'license': 'AGPL-3',
    'depends': [
        'tspbv_connector_transport_unit',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/tspbv_picker.xml',
        'views/stock_picking_batch.xml',
        'views/res_users.xml',
        'views/resources.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
