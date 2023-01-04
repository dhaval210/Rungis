# -*- encoding: utf-8 -*-

{
    'name': 'Metro Purchase Sale Inter Company',
    'version': '12.0.1.0.18',
    'summary': 'RUN-774,RUN-1118,RUN-1122,RUN-1116, RUN-1178 ,RUN-1265,RUN-1304',
    'description':
        """
        RUN-774:https://jira.metrosystems.net/browse/RUN-774
        RUN-1118:https://jira.metrosystems.net/browse/RUN-1118
        RUN-1122:https://jira.metrosystems.net/browse/RUN-1122
        RUN-1116:https://jira.metrosystems.net/browse/RUN-1116
        RUN-1178:https://jira.metrosystems.net/browse/RUN-1178
        RUN-1265:https://jira.metrosystems.net/browse/RUN-1265
        RUN-1304:https://jira.metrosystems.net/browse/RUN-1304
        """,
    'author': ' Cybrosys for METRONOM GmbH',
    'category': 'Metro',
    'depends': [
        'purchase_sale_inter_company',
        'metro_cw8_sale_pick_pack_ship',
        'metro_cw_enhancement',
        'tis_catch_weight',
        'product'

    ],
    'data': [
        'data/system_parameter.xml',
        'views/res_partner.xml',
    ],
    'license': 'Other proprietary',
    'installable': True,
}
