from email.policy import default
from odoo.exceptions import ValidationError
from odoo import models, fields, api, _
from datetime import datetime, timedelta, time
import pytz
import math


class OrderGridLine(models.TransientModel):
    _name = "order.grid.line"
    _description = 'Order Grid Line'

    product_id = fields.Many2one(comodel_name='product.product')
    current_order_date = fields.Datetime(help="date when the PO has to be send to the vendor")
    current_delivery_date = fields.Datetime(help="date when the PO will arrive in the warehouse")
    suggested_qty = fields.Float(help="sum of reordering rule + forecasted sales")
    qty = fields.Float(help="buying qty which will be used in the PO")
    on_hand_qty = fields.Float(string="available qty", help="current available qty on hand in the warehouse")
    uom_id = fields.Many2one(comodel_name='uom.uom')
    reach_date = fields.Datetime(help="date that will be reached until sold or bbd (lifetime) reached")
    avg_sale_qty = fields.Float(help="avg qty sold by week")
    lifetime = fields.Integer(help="lifetime in days for the product")
    next_order_date = fields.Datetime(help="next date when the PO has to be send to the vendor")
    next_delivery_date = fields.Datetime(help="next date when the PO will arrive in the warehouse")
    checkbox = fields.Boolean(default=False, help="just to keep track if done work, no function behind this, also not required")
    is_danger = fields.Boolean(default=False, help="to highlight rows which did not reach the reach_date")
    is_success = fields.Boolean(default=False, help="to highlight rows which did reach the reach_date")
    warn = fields.Html(help="warning text for unsold qty")
    wizard_id = fields.Many2one('order.grid.report', string="Wizard")
    vendor_id = fields.Many2one(comodel_name='res.partner', domain="[('supplier', '=', True)]", help="line specific vendor (used for category filter)")
    lpp = fields.Float(string="LPP", related="product_id.last_purchase_price")
    ordered_qty = fields.Float(
        string="already ordered qty",
        help="already ordered qty for the current order date",
        default=0.00
    )

    @api.onchange('qty')
    def onchange_qty_reach_date(self):
        self.warn = ''
        lifetime = self.lifetime
        if self.product_id.no_expiry is True:
            if self.product_id.categ_id.id is not False and self.product_id.categ_id.ultra_fresh_threshold > 0:
                lifetime = self.product_id.categ_id.ultra_fresh_threshold
                self.warn = '<i class="fa fa-exclamation-triangle"/> ultra fresh <i class="fa fa-exclamation-triangle"/><br/>'
            else:
                lifetime = 365 * 50
        fallback_date = self.current_delivery_date + timedelta(days=lifetime)
        line_data = self.env['cache.order.grid'].search_read([
            ('vendor_id', '=', self.vendor_id.id),
            ('warehouse_id', '=', self.wizard_id.warehouse_id.id),
            ('product_id', '=', self.product_id.id),
            ('date', '>=', self.current_delivery_date - timedelta(days=1)),
            ('date', '<=', fallback_date),
        ], ['qty_on_hand', 'date', 'daily_qty_diff'],order="date")
        fallback_date = datetime.combine(fallback_date, datetime.min.time())
        first = True
        qty = 0
        first_qty = 0
        hit = False
        for ld in line_data:
            if first is True:
                if ld['qty_on_hand'] < 0:
                    qty = self.qty
                else:
                    qty = ld['qty_on_hand'] + self.qty
                first_qty = qty
                first = False
                continue
            qty += ld['daily_qty_diff']
            if lifetime == 0:
                self.reach_date = datetime.combine(ld['date'], datetime.min.time())
                break
            if qty < 0:
                self.reach_date = datetime.combine(ld['date'], datetime.min.time())
                hit = True
                if lifetime == 0:
                    self.warn += 'end of lifetime reached'
                break
            lifetime -= 1
        if hit is False:
            if self.qty == 0 and self.on_hand_qty == 0:
                self.reach_date = fields.Datetime().now()
            elif qty == 0 and self.next_delivery_date < fallback_date:
                self.reach_date = self.next_delivery_date
            else:
                self.reach_date = datetime.combine(fallback_date, datetime.min.time())
                remaining_qty = qty
                if first_qty < 0:
                    remaining_qty -= first_qty
                self.warn += 'end of lifetime reached (unsold qty: {0})'.format(remaining_qty)
        if self.reach_date < self.next_delivery_date and self.suggested_qty != 0:
            self.is_danger = True
            self.is_success = False
        else:
            self.is_danger = False
            self.is_success = True

    def open_supplierinfo_view(self):
        action = {}
        action["type"] = 'ir.actions.act_window'
        action["res_model"] = 'product.supplierinfo'
        action["context"] = "{}"
        action["domain"] = "[('product_tmpl_id', '=', {}), ('name', '=', {})]".format(self.product_id.product_tmpl_id.id, self.vendor_id.id)
        action['view_id'] = self.env.ref('metro_order_grid.product_supplierinfo_tree_view').id
        action['view_mode'] = 'tree'
        action['view_type'] = 'form'
        action['target'] = 'new'
        return action

    def open_quant_view(self):
        action = {}
        action["type"] = 'ir.actions.act_window'
        action["res_model"] = 'stock.quant'
        action["context"] = "{'search_default_internal_loc': 1}"
        action["domain"] = "[('product_id', '=', {})]".format(self.product_id.id)
        action['view_id'] = self.env.ref('metro_order_grid.stock_quant_view_tree').id
        action['view_mode'] = 'tree'
        action['view_type'] = 'form'
        action['target'] = 'new'
        return action

    def open_detail_view(self):
        date_str = datetime.now().strftime('%Y-%m-%d')
        domain = '''
            [
                ("date", ">=", "{}"), ("product_id", "=", {}), ("vendor_id", "=", {}), ("warehouse_id", "=", {}), 
                "|", "|", "|", "|", "|", "|", "|",
                ("is_delivery_date", "=", True),
                ("is_order_date", "=", True),
                ("outgoing_confirmed_qty", ">", 0),
                ("outgoing_demand_qty", ">", 0),
                ("outgoing_planned_qty", ">", 0),
                ("incoming_planned_qty", ">", 0),
                ("incoming_confirmed_qty", ">", 0),
                ("removal_qty", ">", 0)]
        '''.format(date_str, self.product_id.id, self.vendor_id.id, self.wizard_id.warehouse_id.id)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'cache.order.grid',
            'view_id': self.env.ref('metro_order_grid.order_grid_view_tree').id,
            'view_mode': 'tree',
            'view_type': 'form',
            'domain': domain,
            'target': 'new',
        }

    def open_avg_sale_line_view(self):
        date_str = datetime.now() - timedelta(days=365)
        now = datetime.now().strftime('%Y-%m-%d')
        date_str = date_str.strftime('%Y-%m-%d')
        domain = '''[
            "&","&",
            ("product_id", "=", {}),
            ("company_id", "=", {}),
            "|",
                "&", "&",
                ("so_commitment_date", ">=", "{}"),
                ("state", "=", "sale"),
                ("company_id", "!=", 4),
                "&",
                ("so_commitment_date", ">=", "{}"),
                ("state", "in", ["draft", "sent"])
        ]'''.format(
            self.product_id.id,
            self.env.user.company_id.id,
            date_str,
            now
        )
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.line',
            'view_id': self.env.ref('metro_order_grid.sale_order_line_view_tree').id,
            'view_mode': 'tree',
            'view_type': 'form',
            'domain': domain,
            'context': {'group_by': ['so_commitment_date:week','so_commitment_date:day']},
            'target': 'new',
        }


class OrderGrid(models.TransientModel):
    _name = "order.grid.report"
    _description = 'Order Grid Report'

    is_vendor_grid = fields.Boolean(
        default=True,
        compute='_compute_is_vendor_grid',
        help="indicator for the grid view mode")
    grid_type = fields.Selection(
        selection=[('vendor', 'Vendor'), ('category', 'Category')],
        default="vendor",
        help="used for switching the view mode",
    )

    vendor_id = fields.Many2one(comodel_name='res.partner', domain="[('supplier', '=', True)]", help="vendor list (supplier = True only)")
    category_id = fields.Many2one(comodel_name='product.category', help="used to filter products of specific category")
    category_vendor_id = fields.Many2one(comodel_name='res.partner', string="Dummy Vendor", domain="[('supplier', '=', True)]", help="dummy vendor for category purchases (supplier = True only)")

    warehouse_id = fields.Many2one(comodel_name='stock.warehouse', help="warehouse list")
    ordered_qty_flag = fields.Boolean(
        help="to determine wether to show or hide the ordered_qty column",
        default=False
    )
    grid_line_ids = fields.One2many('order.grid.line', 'wizard_id')

    @api.onchange('grid_type')
    def _compute_is_vendor_grid(self):
        for grid in self:
            if grid.grid_type == 'vendor':
                grid.is_vendor_grid = True
                grid.category_id = False
            else:
                grid.is_vendor_grid = False
                grid.vendor_id = False

    def generate_lines(self):
        current_order_date = '1990-01-01 00:00:00'
        next_order_date = '1990-01-01 00:00:00'
        current_delivery_date = '1990-01-01 00:00:00'
        next_delivery_date = '1990-01-01 00:00:00'
        self.ordered_qty_flag = False
        existing_lines = self.env['order.grid.line'].search([('wizard_id', '=', self.id)])
        sellers = {}
        if len(existing_lines) > 0:
            self.write({
                'grid_line_ids': [(5, False, False)]
            })

        if self.category_id.id is False:
            data = self.env['cache.order.grid'].search([
                ('vendor_id', '=', self.vendor_id.id),
                ('warehouse_id', '=', self.warehouse_id.id),
                ('date', '>=', fields.Date().today())
            ])
            # product_ids = data.mapped('product_id')
            product_ids = []
            prod_data = self.env['cache.order.grid'].search_read([
                ('vendor_id', '=', self.vendor_id.id),
                ('warehouse_id', '=', self.warehouse_id.id),
                ('date', '>=', fields.Date().today())
            ], ['product_id'])
            product_ids += [pd['product_id'][0] for pd in prod_data]
            some_ids = data.ids
            sellers.update({self.vendor_id.id: []})
            product_data = self.env['product.product'].search([
                ('id', 'in', product_ids)
            ])
            sellers[self.vendor_id.id] = product_data
        else:
            product_ids = self.env['product.product'].search([
                '|',
                ('categ_id', 'child_of', self.category_id.id),
                ('categ_ids', 'in', [self.category_id.id]),
            ])
            some_ids = []
            for product_data in product_ids:
                seller_ids = product_data.seller_ids
                if len(seller_ids) > 0:
                    if seller_ids[0].name.id not in sellers:
                        sellers.update({seller_ids[0].name.id: []})
                    sellers[seller_ids[0].name.id] += [product_data]

        lines = []
        for seller, product_ids in sellers.items():
            current_order_date = '1990-01-01 00:00:00'
            next_order_date = '1990-01-01 00:00:00'
            current_delivery_date = '1990-01-01 00:00:00'
            next_delivery_date = '1990-01-01 00:00:00'
            if self.category_id.id is not False:
                p_ids = [prd['id'] for prd in product_ids]
                data = self.env['cache.order.grid'].search([
                    ('vendor_id', '=', seller),
                    ('warehouse_id', '=', self.warehouse_id.id),
                    ('product_id', 'in', p_ids),
                    ('date', '>=', fields.Date().today())
                ])
                some_ids = data.ids
            for product_id in product_ids:

                # get current data
                line_data = self.env['cache.order.grid'].search_read([
                    ('id', 'in', some_ids),
                    ('product_id', '=', product_id.id),
                    ('date', '=', fields.Date().today()),
                ], ['qty_on_hand', 'max_qty'], limit=1)
                # get product data
                product_data = self.env['product.product'].browse([product_id.id])
                vendor = self.vendor_id
                vendor_id = self.vendor_id.id
                if self.category_id.id is False:
                    vendor_id = self.vendor_id.id
                    vendor = self.vendor_id
                else:
                    seller_ids = product_data.seller_ids
                    if len(seller_ids) > 0:
                        vendor = seller_ids[0].name
                        vendor_id = seller_ids[0].name.id
                    else:
                        continue

                # calculate reach date
                reach_date = self.get_reach_date(data, product_id)
                # set lifetime

                if (
                    product_data.no_expiry is True and
                    product_data.categ_id.id is not False and
                    product_data.categ_id.ultra_fresh_threshold > 0
                ):
                    lifetime = product_data.categ_id.ultra_fresh_threshold
                else:
                    lifetime = product_data.life_time

                # calculate date if not already done
                if current_order_date == '1990-01-01 00:00:00':
                    current_order_date, next_order_date, current_delivery_date, next_delivery_date = self.get_dates(some_ids, product_id, vendor)
                    check_po_exists = self.check_po_exists(vendor_id, current_delivery_date)

                is_danger = False
                is_success = False
                if reach_date < next_delivery_date:
                    is_danger = True
                    # calculate based on missing qty & order point
                    qty = self.calculate_default_qty(
                        product_id,
                        next_delivery_date,
                        current_delivery_date,
                        lifetime,
                        line_data,
                        vendor_id,
                    )
                else:
                    is_success = True
                    qty = 0

                avg_sale_qty = self.get_avg_sale_qty(product_id)
                ordered_qty = 0
                if check_po_exists is True:
                    ordered_qty = self.get_ordered_qty(product_id, current_delivery_date)
                if ordered_qty > 0 and self.ordered_qty_flag is not True:
                    self.ordered_qty_flag = True

                lines += [[0, 0, {
                    'product_id': product_id.id,
                    'current_order_date': current_order_date,
                    'current_delivery_date': current_delivery_date,
                    'suggested_qty': qty,
                    'qty': qty,
                    'uom_id': product_id.uom_id.id,
                    'ordered_qty': ordered_qty,
                    'on_hand_qty': line_data[0]['qty_on_hand'],
                    'reach_date': reach_date,
                    'avg_sale_qty': avg_sale_qty,
                    'lifetime': lifetime,
                    'next_order_date': next_order_date,
                    'next_delivery_date': next_delivery_date,
                    'wizard_id': self.id,
                    'is_danger': is_danger,
                    'is_success': is_success,
                    'vendor_id': vendor_id,
                }]]

        self.write({'grid_line_ids': lines})

        for line in self.grid_line_ids:
            line.onchange_qty_reach_date()

        return True

    def get_avg_sale_qty(self, product_id):
        avg_qty = 0
        data = self.env['cache.product.qty.grid'].search([
            ('product_id', '=', product_id.id),
            ('warehouse_id', '=', self.warehouse_id.id),
        ], limit=1)
        if data.id is not False:
            avg_qty = data.avg_sale_qty
        return avg_qty

    def check_po_exists(self, vendor_id, current_delivery_date):
        po_data = self.env['purchase.order'].search([
            ('partner_id', '=', vendor_id),
            ('po_date_planned', '=', current_delivery_date),
            ('state', '!=', 'cancel'),
        ], limit=1)
        if len(po_data) > 0:
            return True
        return False

    def get_ordered_qty(self, product_id, current_delivery_date):
        pol_lines = self.env['purchase.order.line'].search([
            ('product_id', '=', product_id.id),
            ('date_planned', '=', current_delivery_date),
            ('state', '!=', 'cancel'),
        ])
        return sum(pol['product_uom_qty'] for pol in pol_lines)

    def calculate_default_qty(self, product_id, next_delivery_date, current_delivery_date, lifetime, line_data, vendor_id):
        future_date = current_delivery_date + timedelta(days=lifetime)
        domain = [
            ("product_id", "=", product_id.id),
            ("so_commitment_date", ">", current_delivery_date),
            ("so_commitment_date", "<=", future_date),
        ]
        sol_lines = self.env['sale.order.line'].search_read(domain, ['product_uom_qty'])
        pol_lines = self.env['purchase.order.line'].search([
            ('product_id', '=', product_id.id),
            ('date_planned', '>=', current_delivery_date),
            ('date_planned', '<=', future_date),
        ])

        so_qty = sum(sol['product_uom_qty'] for sol in sol_lines)
        po_qty = sum(pol['product_uom_qty'] for pol in pol_lines)

        qty_lines = self.env['cache.order.grid'].search([
            ('vendor_id', '=', vendor_id),
            ('warehouse_id', '=', self.warehouse_id.id),
            ('product_id', '=', product_id.id),
            ('date', '<', future_date),
            ('date', '>=', current_delivery_date),
        ])
        so_qty_cache = sum(ql['outgoing_planned_qty'] + ql['outgoing_confirmed_qty'] for ql in qty_lines)
        po_qty_cache = sum(ql['incoming_planned_qty'] + ql['incoming_confirmed_qty'] for ql in qty_lines)

        missing_qty_lines = self.env['cache.order.grid'].search([
            ('vendor_id', '=', vendor_id),
            ('warehouse_id', '=', self.warehouse_id.id),
            ('product_id', '=', product_id.id),
            ('date', '=', next_delivery_date)
        ])
        qty = 0

        so_diff = so_qty - so_qty_cache
        po_diff = po_qty - po_qty_cache
        if (missing_qty_lines.qty_on_hand - so_diff + po_diff) < 0:
            future_qty_lines = self.env['cache.order.grid'].search([
                ('vendor_id', '=', vendor_id),
                ('warehouse_id', '=', self.warehouse_id.id),
                ('product_id', '=', product_id.id),
                ('date', '>=', current_delivery_date),
                ('date', '<=', future_date),
            ])
            start_qty_date = current_delivery_date - timedelta(days=1)
            start_qty_line = self.env['cache.order.grid'].search([
                ('vendor_id', '=', vendor_id),
                ('warehouse_id', '=', self.warehouse_id.id),
                ('product_id', '=', product_id.id),
                ('date', '=', start_qty_date),
            ], limit=1)
            qty = start_qty_line.qty_on_hand * -1

            qty -= sum(fql.daily_qty_diff for fql in future_qty_lines) - so_diff + po_diff
        if qty < 0:
            qty = 0
        if qty > 0 and qty < missing_qty_lines.min_qty:
            qty = line_data[0]['max_qty']
        return qty

    def get_reach_date(self, data, product_id):
        reach_date = False
        reach_date_data = self.env['cache.order.grid'].search_read([
            ('id', 'in', data.ids),
            ('product_id', '=', product_id.id),
            ('qty_on_hand', '<', 0),
        ], ['id', 'date'], limit=1, order='date')
        if len(reach_date_data) > 0 and reach_date_data[0]['id'] is not False:
            reach_date = reach_date_data[0]['date']
        else:
            if product_id.no_expiry is False:
                reach_date_cache_data = self.env['cache.order.grid'].search_read([
                    ('id', 'in', data.ids),
                    ('product_id', '=', product_id.id),
                    ('qty_on_hand', '>', 0),
                ], ['id', 'date'], limit=1, order='id desc')
                if len(reach_date_cache_data) > 0 and reach_date_cache_data[0]['id'] is not False:
                    reach_date = reach_date_cache_data[0]['date']
                else:
                    reach_date = fields.Date().today()
            else:
                if product_id.categ_id.id is not False and product_id.categ_id.ultra_fresh_threshold > 0:
                    lifetime = product_id.categ_id.ultra_fresh_threshold
                else:
                    lifetime = 365 * 50
                reach_date = fields.Date().today() + timedelta(days=lifetime)
        return reach_date

    def get_dates(self, data, product_id, vendor):
        current_order_date = datetime.strptime('1990-01-01', '%Y-%m-%d').date()
        next_order_date = datetime.strptime('1990-01-01', '%Y-%m-%d').date()
        current_delivery_date = datetime.strptime('1990-01-01', '%Y-%m-%d').date()
        next_delivery_date = datetime.strptime('1990-01-01', '%Y-%m-%d').date()
        min_delivery_date = datetime.strptime('1990-01-01', '%Y-%m-%d').date()
        tz = pytz.timezone(self.env.user.tz or 'UTC')
        order_dates = self.env['cache.order.grid'].search([
            ('id', 'in', data),
            ('product_id', '=', product_id.id),
            ('date', '>=', fields.Date().today()),
            ('vendor_id', '=', vendor.id),
            ('is_order_date', '=', True),
        ], limit=2, order='date')

        first = True
        for order_date in order_dates:
            if first is True:
                current_order_date = order_date.date
                first = False
                continue
            next_order_date = order_date.date

        current_order_date, next_order_date = self.check_order_date_time(
            vendor,
            product_id,
            data,
            current_order_date,
            next_order_date
        )

        for supplier_schedule in vendor.schedule_ids:
            hour = int(supplier_schedule.time)
            minute = int(round((supplier_schedule.time * 60) % 60, 0))
            if int(supplier_schedule.order_deadline) == current_order_date.weekday():
                min_delivery_date = current_order_date + timedelta(supplier_schedule.delivery_lead_time)
                current_order_date = datetime.combine(current_order_date, time(hour=hour, minute=minute, second=0))
                offset = tz.utcoffset(current_order_date)
                current_order_date -= offset
            if int(supplier_schedule.order_deadline) == next_order_date.weekday():
                next_order_date = datetime.combine(next_order_date, time(hour=hour, minute=minute, second=0))
                offset = tz.utcoffset(next_order_date)
                next_order_date -= offset

        delivery_dates = self.env['cache.order.grid'].search([
            ('id', 'in', data),
            ('product_id', '=', product_id.id),
            ('is_delivery_date', '=', True),
            ('vendor_id', '=', vendor.id),
            ('date', '>=', min_delivery_date),
        ], limit=2, order='date')

        first = True
        for delivery_date in delivery_dates:
            if first is True:
                current_delivery_date = delivery_date.date
                first = False
                continue
            next_delivery_date = delivery_date.date
        return [
            current_order_date,
            next_order_date,
            current_delivery_date,
            next_delivery_date
        ]

    def check_order_date_time(self, vendor, product_id, data, current_order_date, next_order_date):
        tz = pytz.timezone(self.env.user.tz or 'UTC')
        for supplier_schedule in vendor.schedule_ids:
            hour = int(supplier_schedule.time)
            minute = int(round((supplier_schedule.time * 60) % 60, 0))
            if int(supplier_schedule.order_deadline) == current_order_date.weekday():
                current_order_date_time = datetime.combine(current_order_date, time(hour=hour, minute=minute, second=0))
                offset = tz.utcoffset(current_order_date_time)
                current_order_date_time -= offset
                if fields.Datetime.now() > current_order_date_time:
                    current_order_date = next_order_date
                    new_next_order_date = self.env['cache.order.grid'].search([
                        ('id', 'in', data),
                        ('product_id', '=', product_id.id),
                        ('date', '>', current_order_date),
                        ('vendor_id', '=', vendor.id),
                        ('is_order_date', '=', True),
                    ], limit=1, order='date')
                    next_order_date = new_next_order_date.date    
        return [current_order_date, next_order_date]    

    def cancel_grid(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'target': 'main',
        }

    def po_line_dict(self, grid_line):
        return {
            'name': grid_line.product_id.name,
            'product_id': grid_line.product_id.id,
            'product_qty': grid_line.qty,
            'date_planned': grid_line.current_delivery_date,
            'product_uom': grid_line.product_id.uom_id.id,
            'price_unit': 1
        }

    def check_order_date(self, grid_line):
        tz = pytz.timezone(self.env.user.tz or 'UTC')
        cod = grid_line.current_order_date
        offset = tz.utcoffset(cod)
        cod += offset
        if fields.Datetime.now() > cod:
            err_msg = """
                cutoff time was: {}. You can't create a puchase order for that order day anymore
            """.format(cod.strftime('%d.%m.%Y %H:%M'))
            raise ValidationError(_(err_msg))

    def generate_po_lines(self, grid_lines):
        lines = []
        for grid_line in grid_lines:
            if grid_line.qty > 0:
                self.check_order_date(grid_line)
                lines += [[0, 0, self.po_line_dict(grid_line)]]
        return lines

    def get_lines_by_partner(self, grid_lines):
        lines = {}
        for grid_line in grid_lines:
            if grid_line.qty > 0:
                self.check_order_date(grid_line)
                if grid_line.vendor_id not in lines:
                    lines.update({grid_line.vendor_id: []})
                lines[grid_line.vendor_id] += [grid_line]
        return lines

    def create_po(self, lines, partner_id):
        if len(lines) > 0:
            purchase_order = self.env['purchase.order'].create({
                    'partner_id': partner_id,
                    'grid_id': self.id,
                    'picking_type_id': self.warehouse_id.in_type_id.id,
                    'currency_id': 1,
                    'order_line': lines
            })
            for order_line in purchase_order.order_line:
                order_line._onchange_quantity()
            return purchase_order
        return False

    def update_order_grid_data(self, partner_id):
        self.env['cache.order.grid'].populate_cache_order_grid(
            supplier=partner_id.name,
            force_update=True,
            start_date=datetime.now().strftime('%Y-%m-%d'),
        )

    def open_multi_purchase_view(self, purchase_ids):
        action = {}
        action["type"] = 'ir.actions.act_window'
        action["res_model"] = 'purchase.order'
        action["domain"] = "[('id', 'in', {})]".format(purchase_ids)
        action['view_mode'] = 'tree,form'
        action['view_type'] = 'form'
        action['target'] = 'main'
        return action

    def generate_po(self):
        if self.category_id.id is False or self.category_vendor_id.id is not False:
            partner_id = self.vendor_id
            if self.category_vendor_id.id is not False:
                partner_id = self.category_vendor_id
            lines = self.generate_po_lines(self.grid_line_ids)
            purchase_order = self.create_po(lines, partner_id.id)
            if len(lines) == 0:
                raise ValidationError('no quantity was entered')
            self.update_order_grid_data(partner_id)
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.order',
                'res_id': purchase_order.id,
                'view_mode': 'form',
                'target': 'main',
            }
        else:
            purchase_ids = []
            lines_by_partner = self.get_lines_by_partner(self.grid_line_ids)
            if len(lines_by_partner) > 0:
                for partner_id, plines in lines_by_partner.items():
                    if len(plines) > 0:
                        plines = self.generate_po_lines(plines)
                        purchase_order = self.create_po(plines, partner_id.id)
                        self.update_order_grid_data(partner_id)
                        purchase_ids += [purchase_order.id]
            else:
                raise ValidationError('no quantity was entered')
            if len(purchase_ids) > 0:
                return self.open_multi_purchase_view(purchase_ids)
            else:
                raise ValidationError('no purchase order created')
