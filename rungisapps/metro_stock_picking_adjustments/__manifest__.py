{
    'name': 'Metro Stock Picking Adjustments',
    'version': '12.0.1.0.1',
    'summary': 'RUN-524',
    'category': 'Warehouse',
    'author': 'Niklas Hucke, Hucke Media GmbH & Co KG',
    'website': 'https://www.hucke-media.de',
    'description': '''
        https://jira.metrosystems.net/browse/RUN-524
    ''',
    'license': 'AGPL-3',
    'contributors': [
        'Niklas Hucke',
    ],
    'depends': [
        'tspbv_connector',
    ],
    'data': [
        "views/stock_picking.xml",
        "views/stock_quant.xml",
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
