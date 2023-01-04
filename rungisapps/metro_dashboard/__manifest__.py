# -*- coding: utf-8 -*-
{
    'name': "Dashboard - Metro Systems",

    'summary': """
    	This Module enables you to create and view Dashboards containing Metro specific KPI's or Statistics.,RUN-501""",

    'description': """
        With this module you can create, manage and delete dashboards which show the live values of Statistics and KPI's.

        Creating and managing a dashboard is very straight forward and only some minutes of work.
        Just choose from existing challenges (contain KPI's) and statistics which will than be parsed onto you dashboard and updated hourly.

        For more information please visit the `README.md` file which ships with the module.
        If you are a developer and want to create your own definitions for statistics or variables please look into the `DOCS.md` file.,

       https://jira.metrosystems.net/browse/RUN-501
    """,

    'author': "Odoo PDA",
    'website': "http://www.odoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Metro',
    'version': '12.0.0.28',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        "gamification",
        "metro_customers",
        "metro_min_amount_so"
    ],
    "qweb": [
        "static/src/xml/metro_share_button_template.xml",
        "static/src/xml/metro_chart_template.xml",
        "static/src/xml/metro_dashboard_timeframe_dropdown.xml",
    ],
    # always loaded
    'data': [
        "data/update_tiles.xml",
        "data/update_variables.xml",
        "security/metro_dashboard_groups.xml",
        'security/ir.model.access.csv',
        "views/metro_dashboard_menus.xml",
        "views/metro_static_files.xml",
        "views/metro_dashboard_api.xml",
        "views/metro_dashboard_tile.xml",
        "views/metro_dashboard.xml",
        "views/metro_dashboard_tile_line.xml",
        "views/metro_dashboard_vars.xml",
        "views/metro_dashboard_statistics.xml",
        "views/gamification_challenge.xml",
        "views/gamification_goal_definition.xml",
        "views/metro_dashboard_dataset.xml"
    ],
    # only loaded in demonstration mode
    'demo': [],
}
