# -*- encoding: utf-8 -*-

{
    'name': 'Metro Purchase Schedule',
    'version': '12.0.1.0.8',
    'summary': 'RUN-384, RUN-647',  
    'description':
        """
        RUN-384:https://jira.metrosystems.net/browse/RUN-384
        RUN-647:https://jira.metrosystems.net/browse/RUN-647
        """,
    'author': ' Cybrosys for METRONOM GmbH',
    'category': 'Metro',
    'depends': [
        'contacts',
        'purchase',
        'calendar',
        'supplier_calendar'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/purchase_schedule.xml',
        'views/res_config_view.xml'
    ],
    'license': 'Other proprietary',
    'installable': True,
}
