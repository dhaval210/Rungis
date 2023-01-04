{
    'name': 'Metro Lot Attributes',
    'version': '12.0.1.3.3',
    'summary': 'RUN-536,RUN-407,RUN-773,RUN-965',
    'description': '''
        https://jira.metrosystems.net/browse/RUN-536
        https://jira.metrosystems.net/browse/RUN-407
        https://jira.metrosystems.net/browse/RUN-773
        https://jira.metrosystems.net/browse/RUN-965
        RUN-1076:https://jira.metrosystems.net/browse/RUN-1076
    ''',
    'category': 'Warehouse',
    'author': 'Thore Baden, Hucke Media GmbH & Co KG',
    'website': 'https://www.hucke-media.de',
    'license': 'AGPL-3',
    'contributors': [
        'Thore Baden',
    ],
    'depends': [
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template.xml',
        'views/stock_lot_attribute_lines.xml',
        'views/stock_move_line.xml',
        'views/stock_picking_type.xml',
        'views/stock_picking.xml',
        'views/stock_production_lot.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
