{
    'name': 'Metro Backorder Notification',
    'version': '12.0.1.0.3',
    'summary': 'EMO-2.6 Send notification on cancelled backorders, Run-921,RUN-1254',
    'description': """
                    RUN-921:https://jira.metrosystems.net/browse/RUN-921
                    RUN-1254:https://jira.metrosystems.net/browse/RUN-1254
                    """,
    

    'category': 'Notification',
    'author': 'Thore Baden, Hucke Media Gmbh & Co. KG',
    'maintainer': 'Thore Baden',
    'website': 'https://www.hucke-media.de/',
    'license': 'AGPL-3',
    'contributors': [
        'Thore Baden',
    ],
    'depends': [
        'base_automation',
        'stock',
    ],
    'data': [
        'data/base_automation_template.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
