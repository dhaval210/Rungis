# -*- coding: utf-8 -*-
{
    'name': "Dashboard Definitions - METRO Systems",

    'summary': """This module provides a set of KPIs and Statistics for the Metro Dashboard Module.,RUN-501""",

    'description': """
        This module provides KPIs and Statistics of the following categories:

        * Web Shop
        * Supply Chain Management
        * Value Added Service
        * Finance and Controlling
        * Sales
        * Category Management

        It also provides definitions for variables which are than used by some KPI's or Statistics.
    
        For more detailed informations please take a look at the `DOCS.md` file.,RUN-501
    """,

    'author': "Odoo PDA",
    'website': "http://www.odoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Metro',
    'version': '12.0.0.11',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        "metro_dashboard",
    ],

    # always loaded
    'data': [
        "data/variables.xml",
        "data/goal_definitions.xml",
        "data/statistic_definitions.xml",
        "data/gamification_challenges.xml",
    ],
    # only loaded in demonstration mode
    'demo': [],
}
