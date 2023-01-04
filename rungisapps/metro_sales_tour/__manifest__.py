# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': '*Prototype* Rungis Express Sales Tour Management',
    'version': '12.0.1.0.2',
    'summary': 'RUN-1279',
    'category': 'Metro',
    'author': "Gabriel Demmerle devadoo e.U.",
    'license': 'LGPL-3',
    'description': """
        Adds Tour assignment table on partner and as new menu entry in Sales,
        Adds calling time on partner,
        Adds calling time on SO,
        Adds sequence on SO for Dispo Kanban view,
        Creates SO in advance depending on Rahmentourenplan,
        Reassigns SO based on leaves entries, including substitute Salesman defined on Partner.
        RUN-1279:https://jira.metrosystems.net/browse/RUN-1279
    """,
    'depends': ['sale', 'hr_holidays', 'metro_hub_management', 'metro_softm_fields', 'odoo_transport_management', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'security/dispo_security.xml',
        'views/partner_views.xml',
        'views/tour_assignment.xml',
        'views/sale_order.xml',
        'views/hr_leave.xml',
        'views/transporter_route.xml',
        'views/menu_items.xml',
        'data/data.xml',
        'views/assets.xml'
    ],
    'demo': [
    ],
    'qweb': ['static/src/xml/kanban.xml'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
