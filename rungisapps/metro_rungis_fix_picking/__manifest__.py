{
    'name': 'Rungis Fix Pickings',
    'version': '12.0.1.0.0',
    'summary': 'RUN-1168',
    'description':
        """
        RUN-1168: https://jira.metrosystems.net/browse/RUN-1168
        """,  
    'category': 'enhancement',
    'author': 'Hucke Media Gmbh & Co KG.',
    'website': 'https://hucke-media.de',
    'license': 'AGPL-3',
    'depends': [
        'stock',
        'metro_cw_enhancement'
    ],
    'data': [
        'security/stock_picking_security.xml',
        'views/stock_picking.xml',
        'wizard/message_wiz.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
