# -*- coding: utf-8 -*-

{
    'name': 'Metro Debrand Settings',
    'version': '12.0.1.0.4',
    'summary': 'EMO-1197,RUN-105,EMO-1287',
    'description':  """
                    EMO-1197:https://jira.metrosystems.net/browse/EMO-1197,
                    RUN-105:https://jira.metrosystems.net/browse/RUN-105,
                    EMO-1287:https://jira.metrosystems.net/browse/EMO-1287
                    """,
    'author': 'Cybrosys for METRONOM GmbH',
    'category': 'Metro',
    'depends': ['base_setup', 'web_widget_color'],
    "data": [
        'views/webclient_templates.xml',
        'views/debrand_config_view.xml',
        'template/assets.xml'
    ],
    'license': 'Other proprietary',
    'installable': True,
    'post_init_hook': '_init',
}
