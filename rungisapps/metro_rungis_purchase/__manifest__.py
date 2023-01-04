{
    'name': 'Purchase Enhancement',
    'version': '12.0.1.0.12',
    'summary': 'Purchase Enhancement:RUN-1039,RUN-1031,RUN-1082,RUN-1199,RUN-1105,RUN-1210',
    'description': 'RUN-1039 : https://jira.metrosystems.net/browse/RUN-1039 '
    		       'RUN-1031 : https://jira.metrosystems.net/browse/RUN-1031 '
    		       'RUN-1082 : https://jira.metrosystems.net/browse/RUN-1082 '
    		       'RUN-1199 : https://jira.metrosystems.net/browse/RUN-1199 '
    		       'RUN-1105 : https://jira.metrosystems.net/browse/RUN-1105 '
                   'RUN-1210 : https://jira.metrosystems.net/browse/RUN-1210',
    'category': 'Purchases',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'maintainer': 'Cybrosys Techno Solutions',
    'license': 'AGPL-3',
    'depends': ['purchase', 'base','stock','purchase_stock','tis_catch_weight'],
    'data': [
        'views/purchase_order_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
