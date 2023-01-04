
{
    'name': 'Discounts in product supplier info',
    'version': '12.0.1.0.1',
    'summary': ' EMO-1059 ',
    'description': 'EMO-1059:Discounts in product supplier info',
    'author': ' Odoo PDA',
    'category': 'Purchase Management',
    'depends': [
        'product',
        'purchase_discount',
        'sale_management'],
    'data': [
        'views/product_supplierinfo_view.xml',
        'views/res_partner_view.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'images': ['images/purchase_discount.png'],
}