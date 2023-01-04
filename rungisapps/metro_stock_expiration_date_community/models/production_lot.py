# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import datetime
from odoo import api, fields, models, _


class StockProductionLot(models.Model):
    _name = 'stock.production.lot'
    _inherit = ['stock.production.lot', 'mail.thread']

    #reimplement the field to add the tracking
    use_date = fields.Datetime(string='Best before Date',
                               help='This is the date on which the goods with this Serial Number start deteriorating, without being dangerous yet.',
                               track_visibility = 'onchange')

    def _get_dates(self, product_id=None, ref_date=None):
        """Returns dates based on number of days configured in current lot's product."""
        #If self is empty we cannot do anything, this call happen with the super of create see production_lot of product_expiry module
        if not self:
            return super(StockProductionLot, self)._get_dates(product_id=product_id)

        product = self.env['product.product'].browse(product_id) or self.product_id
        #lot_id is not yet set, but a lot is unique per name and product so find the operation base on the product
        #and the lot_name, of course the one with a use date
        op_id = self.env['stock.move.line'].search([('product_id', '=', self.product_id.id), ('use_date', '!=', False),'|',('lot_name','=',self.name),('lot_id.name','=',self.name)], limit=1)
        #Find the ref date based on the use date

        if ref_date:
            ref_date = ref_date - datetime.timedelta(days=product.use_time)

        else:
            if op_id:
                ref_date = datetime.datetime.strptime(str(op_id.use_date), '%Y-%m-%d') - datetime.timedelta(days=product.use_time)
            else:
                ref_date = datetime.datetime.now()


        #Copy paste for production_lot of product_expiry module, just change now with ref_date
        mapped_fields = {
            'life_date': 'life_time',
            'use_date': 'use_time',
            'removal_date': 'removal_time',
            'alert_date': 'alert_time'
        }
        res = dict.fromkeys(mapped_fields.keys(), False)
        product = self.env['product.product'].browse(product_id) or self.product_id
        if product:
            for field in mapped_fields.keys():
                duration = getattr(product, mapped_fields[field])
                if duration:
                    date = ref_date + datetime.timedelta(days=duration)
                    res[field] = fields.Datetime.to_string(date)
        return res

    @api.model
    def create(self, vals):
        """
            Overwrite the create since we need to trigger the get dates once the object is created
        """
        res = super(StockProductionLot, self).create(vals)
        active_model = res._context.get('active_model', False)
        if active_model and active_model == 'purchase.order':
            dates = res._get_dates()
            res.write(dates)
        return res

    @api.onchange('life_date', 'use_date', 'removal_date', 'alert_date')
    def _onchange_dates(self):
        if self.product_id:
            if self.product_id.life_time + self.product_id.life_time + self.product_id.removal_time + self.product_id.alert_time != 0:
                dates = self._get_dates(ref_date=datetime.datetime.strptime(str(self.use_date), '%Y-%m-%d %H:%M:%S'))
                if dates:
                    self.life_date = dates['life_date']
                    self.use_date = dates['use_date']
                    self.removal_date = dates['removal_date']
                    self.alert_date = dates['alert_date']
            else:
                self.life_date = False
                self.use_date = False
                self.removal_date = False
                self.alert_date = False


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    no_expiry = fields.Boolean(string='No expiry date', related='product_id.no_expiry',
        help='Technical field to hide the BBD on the stock.pack.operation.lot', readonly=True)
    use_date = fields.Date(string='Best before Date',
                           compute='_onchange_lot_id', store=True,
                           readonly=False,help='This is the date on which the goods with this Serial Number start deteriorating, without being dangerous yet.')
    readonly_use_date = fields.Boolean(string='Readonly Use date if already set on Lot', compute='_onchange_lot_id', store=False, readonly=True)
    # picking_id = fields.Many2one('stock.picking', related='move_id.picking_id')

    @api.model
    def default_get(self, fields):
        res = super(StockMoveLine, self).default_get(fields)
        if 'location_dest_id' in fields and self.env.context.get('default_product_id') and self.env.context.get('default_picking_type_id'):
            loc = self.env['stock.location']
            if self.env.context.get('default_product_id'):
                product_id = self.env['product.product'].browse(self.env.context['default_product_id'])
                putaway_strategy = self.env['stock.picking.type'].browse(self.env.context['default_picking_type_id']).default_location_dest_id.putaway_strategy_id
                loc = putaway_strategy.putaway_apply(product_id)
            if loc:
                res['location_dest_id'] = loc.id
        return res

    @api.depends('lot_id')
    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        cached_use_date = {}
        if self.ids:
            self._cr.execute("""
                SELECT id, use_date
                FROM stock_move_line
                WHERE id IN %s
            """, (tuple(self.ids),))
            cached_use_date = dict(self._cr.fetchall())

        for op_lot in self:
            if op_lot.lot_id:
                op_lot.use_date = fields.Date.from_string(op_lot.lot_id.use_date)
                op_lot.readonly_use_date = True
            else:
                if op_lot.id:
                    op_lot.use_date = cached_use_date.get(op_lot.id) or False
                op_lot.readonly_use_date = False

    @api.onchange('use_date')
    def _onchange_use_date(self):
        for op_lot in self:
            if not op_lot.lot_id and op_lot.use_date:
                quality_point = op_lot.env['quality.control.point'].sudo().search([
                    ('picking_type_id', '=', op_lot.move_id.picking_id.picking_type_id.id),
                    ('quality_control_point_line_ids.test_type', '=','time_ratio'),
                    ('product_id', '=', op_lot.product_id.id)], limit=1)
                if quality_point:
                    for q_point in quality_point.quality_control_point_line_ids:
                        if q_point.test_type == 'time_ratio':
                            if not fields.Date.from_string(op_lot.use_date) == datetime.date.today():
                                if fields.Date.from_string(op_lot.use_date) <= datetime.date.today() or (
                                        fields.Date.from_string(op_lot.use_date) - datetime.date.today()).days / float(
                                        op_lot.product_id.product_tmpl_id.use_time) < q_point.time_ratio:
                                    return {'warning': {'title': 'Shelf time ratio alert', 'message': 'The expiration date is below the allowed shelf time ratio, a quality alert will be created for this line.'}}





