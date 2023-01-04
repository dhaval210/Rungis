{
    'name': 'Metro DB2 Connector',
    'version': '12.0.1.0.23',
    'summary': 'RUN-615,RUN-912,RUN-887,RUN-913,RUN-975,RUN-993,RUN-1049',
    'description': '''
        RUN-615: https://jira.metrosystems.net/browse/RUN-615
        RUN-912: https://jira.metrosystems.net/browse/RUN-912
        RUN-887: https://jira.metrosystems.net/browse/RUN-887
        RUN-913: https://jira.metrosystems.net/browse/RUN-913
        RUN-975: https://jira.metrosystems.net/browse/RUN-975
        RUN-993: https://jira.metrosystems.net/browse/RUN-993
        RUN-993: https://jira.metrosystems.net/browse/RUN-1049
    ''',
    'category': 'Connector',
    'author': 'Thore Baden, Hucke Media GmbH & Co. KG',
    'website': 'https://www.hucke-media.de',
    'license': 'LGPL-3',
    'depends': [
        'connector',
        'queue_job',
        'sale',
    ],
    'external_dependencies': {
        'python': [
            'ibm_db',
        ],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/db2_backend.xml',
        'views/sale_order_line.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
