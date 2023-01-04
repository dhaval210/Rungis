{
    'name': 'Metro Rungis Purchase Order Line Transfer',
    'version': '12.0.1.0.1',
    'summary': 'Ordering solution for fish assortment:RUN-1256',
    'description': """
                RUN-1256 :https://jira.metrosystems.net/browse/RUN-1256
                """,
    'category': 'Purchases',
    'author': 'Wipro Technologies - Abhay Singh Rathore',
    'company': 'Wipro Technologies',
    'website': "https://wipro.com/",
    'maintainer': 'Wipro Technologies',
    'license': 'AGPL-3',
    'depends': ['purchase','metro_rungis_purchase_order_report'],
    'installable': True,
    'auto_install': False,
    'application': False,
    'data': [
        'security/ir.model.access.csv',
        'views/data.xml',
        'wizard/po_line_wiz_view.xml',
        'views/purchase_order_view.xml',
    ],
}
