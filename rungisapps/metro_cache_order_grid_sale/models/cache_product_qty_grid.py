from odoo import models, fields
from datetime import timedelta
from odoo.addons.queue_job.job import job


class CacheProductQtyGrid(models.Model):
    _inherit = 'cache.product.qty.grid'

    avg_sale_qty = fields.Float(help="will be recalculated nightly by scheduled action")

    def cron_avg_sale_qty(self):
        grid_ids = self.search([])
        for grid_id in grid_ids:
            desc = 'calculate avg sale for product: ' + grid_id.product_id.name
            self.with_delay(priority=1, description=desc).get_avg_sale_qty_by_product(grid_id)

    @job(default_channel='root.order_grid.populate_warehouse')
    def get_avg_sale_qty_by_product(self, grid_id):
        today = fields.Datetime.now()
        last_year = fields.Datetime.now() - timedelta(days=365)
        product_id = grid_id.product_id
        avg_qty = 0
        weeks = 52
        oldest_line = self.env['sale.order.line'].sudo().search([
            ('product_id', '=', product_id.id),
        ], order='create_date asc', limit=1)
        if oldest_line.id is not False and oldest_line.create_date > last_year:
            monday1 = (oldest_line['create_date'] - timedelta(days=oldest_line['create_date'].weekday()))
            monday2 = (today - timedelta(days=today.weekday()))
            diff = int((monday2 - monday1).days / 7)
            weeks = diff
        elif oldest_line.id is False:
            weeks = 1

        order_lines = self.env['sale.order.line'].sudo().search_read([
            ('product_id', '=', product_id.id),
            ('create_date', '>=', last_year),
            ('state', '=', 'sale'),
            ('company_id', '!=', 4),
        ], ['product_uom_qty'])
        if len(order_lines) > 0:
            avg_qty = sum(ol['product_uom_qty'] for ol in order_lines)
            avg_qty = round(avg_qty / weeks, 0)
            grid_id.write({
                'avg_sale_qty': avg_qty
            })
