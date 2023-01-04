# -*- encoding: utf-8 -*-

{
    'name': 'Metro Putaway Override Location Community',
    'version': '12.0.1.0.1',
    'summary': 'RUN-353',
    'description': """RUN-353:https://jira.metrosystems.net/browse/RUN-353""",
    'author': ' Cybrosys for METRONOM GmbH',
    'category': 'Metro',
    'depends': [
        'metro_putaway_strategy',
    ],
    'data': [
        'views/stock_picking_view.xml'
    ],
    'license': 'Other proprietary',
    'installable': True,
}
