from odoo import api, SUPERUSER_ID


def set_last_purchase_price(cr, registry):
    """This will update the last purchase price for all products
    """
    env = api.Environment(cr, SUPERUSER_ID, dict())
    product_obj = env['product.product']
    products = product_obj.search([('purchase_ok', '=', True)])
    products.set_product_last_purchase()