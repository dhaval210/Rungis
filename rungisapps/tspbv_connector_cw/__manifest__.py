{
    'name': 'Topsystem Pick by Voice Catchw8 Addon',
    'version': '12.0.1.1.0',
    'summary': 'Topsystem Pick by Voice Catchw8 Addon',
    'category': 'Warehouse',
    'author': 'Hucke Media GmBH & Co KG.',
    'maintainer': 'Thore Baden',
    'website': 'https://www.hucke-media.de/',
    'license': 'AGPL-3',
    'depends': [
        'tis_catch_weight',
        'tspbv_connector',
    ],
    'data': [
        'demo/tspbv_dialoglist_cw_weight.xml',
        'demo/tspbv_workflow_demo.xml',
    ],
    'demo': [
        #'demo/tspbv_dialoglist_cw_weight.xml',
        #'demo/tspbv_workflow_demo.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
