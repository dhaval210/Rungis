{
    'name': 'MRP Production Putaway Strategy',
    'version': '12.0.1.0.0',
    'summary': ' EMO-1032 ',
    'description': 'EMO-1032:This module allows to apply putaway strategies '
                   'to the products ''resulting from the manufacturing '
                   'orders.'
                   'The finished products will be placed in the location'
                   'designated by the putaway strategy (if they '
                   'do not ''have another destination move), based on the '
                   'finished products location'
                   'that was defined in the manufacturing order.',
    'author': ' Odoo PDA',
    'category': 'Manufacture',
    'depends': [
        'stock',
        'mrp'],
    'license': 'LGPL-3',
    'installable': True,
}
