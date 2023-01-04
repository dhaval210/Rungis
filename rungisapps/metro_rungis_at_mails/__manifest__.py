{
    'name': 'Mail notification for master data updation',
    'version': '12.0.1.0.2',
    'summary': 'This module helps to notify about the updations in the master data product list,RUN-869',
    'description': 'RUN-869 : https://jira.metrosystems.net/browse/RUN-869 ',
                   'https://jira.metrosystems.net/browse/RUN-966'
    'category': 'Enhancement',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'maintainer': 'Cybrosys Techno Solutions',
    'license': 'AGPL-3',
    'depends': ['product','sale','base','mail'],
    'data': ['data/mail_template.xml',
             'views/product_template.xml'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
