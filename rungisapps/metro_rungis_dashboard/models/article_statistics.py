from odoo import models, fields, api, tools


class ArticleStatistics(models.Model):
    _name = 'article.statistics'
    _auto = False
    _description = 'Article Statistics'
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', "Product", readonly=True)
    sub_category = fields.Char("Sub Category", readonly=True)
    category_id = fields.Many2one('product.category', "Category", readonly=True)
    date = fields.Datetime("Date", readonly=True)
    supplier_id = fields.Many2one('res.partner', "Customer", readonly=True)
    supplier_number = fields.Char("Customer Number", readonly=True)
    article_number = fields.Char("Article Number", readonly=True)
    sale_price_month = fields.Float("Sales in Last 1 Month",
                                    help="Sale price in last 1 Month", readonly=True)
    sale_price_6_month = fields.Float("Sales in Last 6 Month", readonly=True)
    stock_available = fields.Float("Stock Available", compute="get_stock")
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    currency_id = fields.Many2one(related="company_id.currency_id", string="Currency", readonly=True)

    def get_stock(self):
        product_ids = self.mapped('product_id')
        location_ids = self.env['stock.location'].search([('usage', '=', 'internal')])
        stock_quant_groups = self.env['stock.quant'].read_group(
            [('product_id', 'in', product_ids.ids), ('location_id', 'in', location_ids.ids)],
            ['product_id', 'quantity'], ['product_id'])
        for group in stock_quant_groups:
            records = self.filtered(lambda s: s.product_id.id == group['product_id'][0])
            for record in records:
                record.stock_available = group['quantity']

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = """ CREATE or REPLACE VIEW article_statistics AS (select row_number() OVER () as id, pp.id as product_id, 
                            pc.name as sub_category, pc.id as category_id, 
                            sr.date as date, rp.id as supplier_id, rp.ref as supplier_number, pp.default_code as article_number,
                            sr.company_id as company_id,
							case when sr.date >= CURRENT_DATE - INTERVAL '30 days' then sum(sr.price_subtotal) 
							else 0 end as sale_price_month,
							case when sr.date >= CURRENT_DATE - INTERVAL '6 months' then sum(sr.price_subtotal) 
							else 0 end as sale_price_6_month
                            from product_product as pp
                            left join product_template pt on pt.id = pp.product_tmpl_id
                            left join res_company rc on rc.id = pt.company_id
                            left join product_category pc on pc.id = pt.categ_id
                            left join sale_report sr on sr.product_id = pp.id
                            left join res_partner rp on sr.partner_id = rp.id
							where pp.active = true or pt.sale_ok = true and sr.state = 'sale' and sr.company_id = %s
							group by pp.id, pc.name, pc.id, sr.date, rp.id, rp.ref, pp.default_code, sr.company_id); """
        self.env.cr.execute(query, tuple(self.env.user.company_id.ids))
