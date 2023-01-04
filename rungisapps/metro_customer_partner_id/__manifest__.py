{
    'name': 'Customer Partner ID',
    'version': '12.0.1.0.6',
    'summary': 'EMO-1158,EMO:RUN-90',
    'description': """
        EMO-1158:The customer ID is generated only when below condition is met:
        v3 - Changed Vendor list View""",
    'author': 'Odoo PDA',
    'category': 'Sales',
    'depends': [
        'base',
        'sale',
        'sale_management',
        'purchase',
        # 'metro_myanmar_township',
    ],
    'data': [
        'data/partner_sequence.xml',
        'views/res_company_view.xml',
        # 'views/res_config_views.xml',
        'views/res_partner_views.xml',
        'views/sale_view.xml',
        'views/purchase_view.xml',
        'views/account_vendor_view.xml'
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
}
