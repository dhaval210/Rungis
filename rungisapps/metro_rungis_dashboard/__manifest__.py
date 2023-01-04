{
    'name': 'Metro Rungis Dashboard',
    'version': '12.0.0.0.3',
    'summary': 'RUN-749,RUN-1267',
    'description': '''
    RUN-749:https://jira.metrosystems.net/browse/RUN-749
    RUN-1267:https://jira.metrosystems.net/browse/RUN-1267
    ''',
    'author': 'Cybrosys for METRONOM GmbH',
    'category': 'Enhancement',
    'depends': [
        'sale',
        'purchase',
        'base',
        'stock',
        'tis_catch_weight',
    ],
    "data": [
        'data/data.xml',
        'security/ir.model.access.csv',
        'views/res_partner.xml',
        'views/sale_order.xml',
        'views/purchase_order.xml',
        'views/product_product.xml',
        'views/article_statistics.xml',
        'views/buying_reorders.xml',
        'views/purchase_supply.xml',
    ],
    'license': 'Other proprietary',
    'installable': True,
}