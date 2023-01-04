{
    'name': 'Geolocalize from actual position',
    'version': '12.0.1.0.0',
    'summary': ' EMO-1123 ',
    'description': """ EMO-1123: 
                    Adds a button on the partner form to  geolocate from 
                    actual browser position and saves it in the  partner 
                    latitude and longitude fields.""",
    'author': 'Odoo PDA',
    'category': 'Metro',
    'depends': [
        'base_geolocalize',
        'contacts',
    ],
    'data': [
        'views/res_partner_views.xml',
        'views/assets.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
    'auto_install': False,
    'application': False,
}
