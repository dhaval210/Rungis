from odoo import models, fields, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    last_purchase_price = fields.Float(
        string='Last Purchase Price', company_dependent=True, currency_id='currency_id')
    currency_id = fields.Many2one('res.currency', compute='compute_currency_id')

    def compute_currency_id(self):
        for rec in self:
            rec.currency_id = rec.env.user.company_id.id

    def get_last_price(self, product, company_id):
        PurchaseOrderLine = self.env['purchase.order.line']
        domain = [('product_id', '=', product.id),
                    ('state', 'in', ['purchase', 'done'])]
        if company_id:
            domain.append(('company_id', '=', company_id))        
        line = PurchaseOrderLine.search(domain, order="date_planned desc, id desc", limit=1)
        if len(line) > 0:
            return product.uom_id._compute_lpp_quantity(
                line.price_unit, line.product_uom)
        return 0.0

    @api.multi
    def set_product_last_purchase(self, company_id=None):
        for product in self:
            price_unit_uom = self.get_last_price(product, company_id)
            if price_unit_uom != product.with_context(force_company=company_id).last_purchase_price:
                product.with_context(force_company=company_id).write({
                    "last_purchase_price": price_unit_uom,
                })
            if price_unit_uom != product.product_tmpl_id.with_context(force_company=company_id).last_purchase_price:                
                product.product_tmpl_id.set_product_template_last_purchase(price_unit_uom,company_id)

            return True

    def update_product_last_purchase(self, company_id=None):
        products = self.search([('last_purchase_price', '=', 0), ('qty_available', '>', 0)])
        for product in products:
            price_unit_uom = self.get_last_price(product, company_id)
            if price_unit_uom != product.with_context(force_company=company_id).last_purchase_price:
                product.write({
                    "last_purchase_price": price_unit_uom,
                })
            if price_unit_uom != product.product_tmpl_id.with_context(force_company=company_id).last_purchase_price:
                product.product_tmpl_id.set_product_template_last_purchase(price_unit_uom)

    def update_lpp(self):
        self.update_product_last_purchase(1)
        self.update_product_last_purchase(4)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    last_purchase_price = fields.Float(
        string='Last Purchase Price', track_visibility='onchange', company_dependent=True)

    def set_product_template_last_purchase(self, price_unit,company_id=None):
        return self.with_context(force_company=company_id).write({
            "last_purchase_price": price_unit,
        })
