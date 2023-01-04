from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import models, fields, _


class ResPartnerData(models.Model):
    _name = "res.partner.data"

    name = fields.Char("Name", translate=True)
    today = fields.Float('Today')
    last_week = fields.Float('Last Week')
    last_month = fields.Float('Last Month')
    last_quarter = fields.Float('Last Quarter')
    last_year = fields.Float('Last Year')
    this_year = fields.Float('This Year')
    partner_id = fields.Many2one('res.partner')

    def get_domains(self):
        today = fields.Date.today()
        weekday = today.weekday()

        return {
            "today": fields.Date.today(),
            "last_week": [today - timedelta(days=weekday, weeks=1),
                          today - timedelta(days=weekday, weeks=1) + timedelta(
                              days=7)],
            "last_month": [today.replace(day=1) - relativedelta(months=1),
                           today.replace(day=1) - timedelta(days=1)],
            "last_quarter": self.get_quarter(),
            "last_year": [
                today.replace(month=1, day=1) - relativedelta(years=1),
                today.replace(month=1, day=1) - timedelta(days=1)],
            "this_year": [today.replace(month=1, day=1),
                          today.replace(month=12, day=31)],
        }

    def get_quarter(self):
        current_date = datetime.today()
        current_quarter = round((current_date.month - 1) / 3 + 1)
        month = 3 * current_quarter
        first_date = datetime(current_date.year, month - 2, 1) - relativedelta(
            months=3)
        end = month + 1 if (month + 1) <= 12 else month - 11
        last_date = datetime(current_date.year, end, 1) + timedelta(
            days=-1) - relativedelta(months=3)
        return [first_date.date(), last_date.date()]


class ResPartner(models.Model):
    _inherit = "res.partner"

    data_ids = fields.One2many('res.partner.data', 'partner_id')

    def action_update_data(self):
        data_obj = self.env['res.partner.data']
        domains = data_obj.get_domains()
        for partner in self.search([('supplier', '=', True)]):
            partner.data_ids.unlink()
            purchase_order = self.env['purchase.order'].search([
                ('partner_id', '=', partner.id),
                ('po_date_planned', '>=', domains.get('last_year')[0])
            ])
            picking_ids = purchase_order.mapped('picking_ids').filtered(
                lambda x: x.state == "done")
            lot_ids = picking_ids.mapped('move_line_ids.lot_id')
            alot_ids = self.get_alot_ids(lot_ids)
            delivery_line_ids = self.env["stock.move.line"].search([
                ("picking_id.picking_type_id.code", "=", "outgoing"),
                ("picking_id.name", "ilike", "OUT"),
                ("lot_id", "in", lot_ids.ids),
            ])
            adelivery_line_ids = self.env["stock.move.line"].search([
                ("picking_id.picking_type_id.code", "=", "outgoing"),
                ("picking_id.name", "ilike", "OUT"),
                ("lot_id", "in", alot_ids.ids)
            ])
            expired_delivery_line_ids = self.env["stock.move.line"].search([
                ("picking_id.picking_type_id.code", "=", "outgoing"),
                ("picking_id.name", "ilike", "SCP"),
                ("lot_id", "in", alot_ids.ids.extend(lot_ids.ids))
            ])
            purchase_val = {
                "partner_id": partner.id,
                "name": _("Aggregated Purchase volume")
            }
            sale_val = {
                "partner_id": partner.id,
                "name": _("Regular Sales")
            }
            aproduct_sale_val = {
                "partner_id": partner.id,
                "name": _("AProduct Sales")
            }
            stock_val = {
                "partner_id": partner.id,
                "name": _("Current Stock")
            }
            astock_val = {
                "partner_id": partner.id,
                "name": _("Current Stock Aproduct")
            }
            profit_val = {
                "partner_id": partner.id,
                "name": _("Gross profit")
            }
            expired_val = {
                "partner_id": partner.id,
                "name": _("Expired products")
            }
            for key in domains:
                val = domains.get(key)
                po_val = self.get_total_po_value(val, purchase_order, alot_ids)
                so_val = self.get_total_so_value(val, delivery_line_ids)
                aso_val = self.get_total_so_value(val, adelivery_line_ids)
                purchase_val.update({
                    key: po_val[0]
                })
                sale_val.update({
                    key: so_val
                })
                aproduct_sale_val.update({
                    key: aso_val
                })
                stock_val.update({
                    key: po_val[1]
                })
                astock_val.update({
                    key: po_val[2]
                })
                profit_val.update({
                    key: so_val + aso_val - po_val[0]
                })
                expired_val.update({
                    key: self.get_total_exp_value(val, expired_delivery_line_ids)
                })
            self.env["res.partner.data"].create([sale_val, aproduct_sale_val, purchase_val, profit_val, stock_val, astock_val, expired_val])

    def get_total_po_value(self, domain, purchase_order, alot_ids):
        if type(domain) == list:
            orders = purchase_order.filtered(
                lambda x: domain[0] <= x.po_date_planned.date() <= domain[1])
        else:
            orders = purchase_order.filtered(
                lambda x: x.po_date_planned.date() >= domain >= x.po_date_planned.date())
        total = round(sum(orders.mapped('order_line.price_subtotal')), 2)
        move_line = orders.mapped("picking_ids").mapped("move_line_ids")
        stock = 0
        astock = 0
        for line in move_line:
            if line.lot_id.product_qty:
                po = orders.filtered(lambda x: line.picking_id.id in x.picking_ids.ids)
                po_lines = po.order_line.filtered(lambda x: x.product_id.id == line.product_id.id)
                if po_lines:
                    po_line = po_lines[0]
                    quantity = line.lot_id.cw_product_qty if line.lot_id.catch_weight_ok else line.lot_id.product_qty
                    stock += po_line.price_unit * quantity
                    alot_id = alot_ids.filtered(
                        lambda x: x.product_id.code == 'A' + line.lot_id.product_id.code
                                  and x.name == line.lot_id.name)
                    if alot_id.product_qty:
                        aquantity = alot_id.cw_product_qty if alot_id.catch_weight_ok else alot_id.product_qty
                        astock += (po_line.price_unit * 8 / 10) * aquantity
        return [total, round(stock, 2), round(astock, 2)]

    def get_total_so_value(self, domain, delivery_line_ids):
        if type(domain) == list:
            orders = delivery_line_ids.filtered(
                lambda x: domain[0] <= x.picking_id.scheduled_date.date() <= domain[1])
        else:
            orders = delivery_line_ids.filtered(
                lambda x: x.picking_id.scheduled_date.date() >= domain >= x.picking_id.scheduled_date.date())
        total = 0
        for order in orders:
            so = order.picking_id.sale_id
            so_lines = so.order_line.filtered(
                lambda x: x.product_id.id == order.product_id.id)
            if so_lines:
                so_line = so_lines[0]
                quantity = order.cw_qty_done if order.product_id.catch_weight_ok else order.qty_done
                total += so_line.price_unit * quantity
        return round(total, 2)

    def get_total_exp_value(self, domain, delivery_line_ids):
        if type(domain) == list:
            orders = delivery_line_ids.filtered(
                lambda x: domain[0] <= x.picking_id.scheduled_date.date() <= domain[1])
        else:
            orders = delivery_line_ids.filtered(
                lambda x: x.picking_id.scheduled_date.date() >= domain >= x.picking_id.scheduled_date.date())
        total = 0
        for order in orders:
            stock_line = self.env["stock.move.line"].search([
                ("lot_id", "=", order.lot_id.id),
                ("picking_id.purchase_id", "!=", False)
            ])

            po_lines = stock_line.picking_id.purchase_id.order_line.filtered(
                lambda x: x.product_id.id == order.product_id.id)
            if po_lines:
                po_line = po_lines[0]
                quantity = order.cw_qty_done if order.product_id.catch_weight_ok else order.qty_done
                total += po_line.price_unit * quantity
        return round(total, 2)

    def get_alot_ids(self, lot_ids):
        alot_ids = self.env["stock.production.lot"]
        for lot_id in lot_ids:
            aproduct_id = self.env["product.product"].search([
                ("default_code", "=", f"A{lot_id.product_id.default_code}"),
                ("company_id", "=", lot_id.company_id.id)
            ])
            if aproduct_id:
                alot_ids += self.env["stock.production.lot"].search([
                    ("name", "=", lot_id.name),
                    ("product_id", "=", aproduct_id.id)
                ])
        return alot_ids