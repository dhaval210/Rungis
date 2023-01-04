{
    'name': 'Metro Rungis Purchase Vendor Confirmation',
    'version': '12.0.1.0.3',
    'summary': 'Order Response / Delivery Note Recording:RUN-1240',
    'description': """
                RUN-1240 :https://jira.metrosystems.net/browse/RUN-1240
                """,
    'category': 'Purchases',
    'author': 'Wipro Technologies - Abhay Singh Rathore',
    'company': 'Wipro Technologies',
    'website': "https://wipro.com/",
    'maintainer': 'Wipro Technologies',
    'license': 'AGPL-3',
    'depends': ['purchase','metro_rungis_purchase', 'metro_rungis_views', 'mail'],
    'installable': True,
    'auto_install': False,
    'application': False,
    'data': [
        'security/ir.model.access.csv',
        'views/data.xml',
        'wizard/delivery_note_wiz_view.xml',
        'views/purchase_order_view.xml',
    ],
}
