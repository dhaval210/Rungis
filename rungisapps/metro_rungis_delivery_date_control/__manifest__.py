{
    'name': 'Delivery date control',
    'version': '12.0.1.0.13',
    'summary': 'This module helps to control delivery date,RUN-1033',
    'description': 'RUN-1033 : https://jira.metrosystems.net/browse/RUN-1033 ',
    'category': 'Enhancement',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'maintainer': 'Cybrosys Techno Solutions',
    'license': 'AGPL-3',
    'depends': ['purchase', 'base','stock','purchase_stock'],
    'data': [
        'views/scheduled_date_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
