{
    'name': 'Metro Inventory UI Improvements',
    'version': '12.0.1.0.8',
    'summary': 'Metro UI Improvementes, RUN-548, RUN-559,RUN-1248',
    "description": """
        https://jira.metrosystems.net/browse/RUN-548
        https://jira.metrosystems.net/browse/RUN-559
        https://jira.metrosystems.net/browse/RUN-1248
    """,
    'category': 'Inventory',
    'author': 'Hucke Media GmbH & Co. KG',
    'maintainer': 'Thore Baden',
    'website': 'https://www.hucke-media.de',
    'license': 'AGPL-3',
    'depends': [
        'odoo_transport_management',
        'stock',
        'product',
        'metro_softm_fields',
        "stock_inventory_discrepancy",
        "stock_change_qty_reason",
    ],
    'data': [
        'views/product_product.xml',
        'views/product_template.xml',
        'views/resources.xml',
        'views/stock_picking.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
