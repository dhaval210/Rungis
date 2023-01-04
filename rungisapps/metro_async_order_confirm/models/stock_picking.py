from odoo import models, api
from odoo.addons.queue_job.job import job


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @job(default_channel='root.stock_picking')
    @api.multi
    def async_validate_packing(self):
        for record in self:
            wiz = self.env['stock.immediate.transfer'].create({
                'pick_ids': [(4, record.id)]
            })
            wiz.process()

            if record._check_backorder():
                backorder_confirm = self.env['stock.backorder.confirmation'].create(
                    {'pick_ids': [(4, p.id) for p in record]})
                backorder_confirm.process_cancel_backorder()

            if record.picking_type_code == 'outgoing' and record.sale_id.client_order_ref:
                purchase_id = self.env['purchase.order'].sudo().search([
                    ('name', '=', record.sale_id.client_order_ref),
                    ('company_id', '=', 4)
                ], limit=1)
                if purchase_id:
                    for sale_move_line in record.move_line_ids_without_package:
                        lot_attribute_lines = sale_move_line.lot_id.lot_attribute_line_ids
                        lot_id = self.env['stock.production.lot'].sudo().search(
                            [('name', '=', sale_move_line.lot_id.name),
                            ('company_id', '=', purchase_id.company_id.id),
                            ('product_id', '=', sale_move_line.lot_id.product_id.id)], limit=1)
                        if lot_id and lot_id.purchase_order_ids:
                            lot_id = lot_id.filtered(lambda lot: purchase_id.partner_id.id in lot.purchase_order_ids.mapped('partner_id.id'))
                        if lot_id:
                            lot_id.sudo().write({
                                'lot_attribute_line_ids': [(6, 0, sale_move_line.lot_id.lot_attribute_line_ids.ids)]
                                if sale_move_line.lot_id.lot_attribute_line_ids else []
                            })
                        if not lot_id:
                            lot_id = self.env['stock.production.lot'].sudo().create({
                                'name': sale_move_line.lot_id.name,
                                'product_id': sale_move_line.product_id.id,
                                'use_date': sale_move_line.lot_id.use_date,
                                'removal_date': sale_move_line.lot_id.removal_date,
                                'life_date': sale_move_line.lot_id.life_date,
                                'alert_date': sale_move_line.lot_id.alert_date,
                                'company_id': purchase_id.company_id.id,
                                'lot_attribute_line_ids': [(6, 0, sale_move_line.lot_id.lot_attribute_line_ids.ids)]
                                if sale_move_line.lot_id.lot_attribute_line_ids else []
                            })
                        purchase_move_id = purchase_id.picking_ids[0].move_ids_without_package.filtered(lambda pick: pick.product_id == sale_move_line.product_id)
                        self.env['stock.move.line'].sudo().create({
                            'product_id': sale_move_line.product_id.id,
                            'product_uom_id': sale_move_line.product_uom_id.id,
                            'location_id': purchase_move_id.location_id.id,
                            'location_dest_id': purchase_move_id.location_dest_id.id,
                            'lot_id': lot_id.id,
                            'product_uom_qty': sale_move_line.qty_done,
                            'product_cw_uom_qty': sale_move_line.cw_qty_done,
                            'lot_attribute_line_ids': [(6, 0, lot_attribute_lines.ids)],
                            'lot_name': lot_id.name,
                            'picking_id': purchase_move_id.picking_id.id,
                            'move_id': purchase_move_id.id,
                            'inter_company_line': True
                        })
            record.async_state = 'done'
        return True
