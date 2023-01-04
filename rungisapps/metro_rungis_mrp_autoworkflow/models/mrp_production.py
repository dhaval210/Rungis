# -*- coding: utf-8 -*-

from odoo import models, _, api, fields
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    auto_check = fields.Boolean(default=False)

    @api.model
    def create(self, vals_list):
        res = super(MrpProduction, self).create(vals_list)
        res.update({
            'auto_check': True
        })
        return res

    def picking_validation(self):
        for picking in self.picking_ids:
            if picking.state == 'confirmed':
                picking.action_assign()
                wiz_act = picking.button_validate()
                wiz = self.env[wiz_act['res_model']].browse(wiz_act['res_id'])
                wiz.process()
            elif picking.state == 'assigned':
                wiz_act = picking.button_validate()
                wiz = self.env[wiz_act['res_model']].browse(wiz_act['res_id'])
                wiz.process()

    def mrp_auto_flow(self):
        self.picking_validation()
        location_src_id = self.picking_ids.filtered(
            lambda l: 'PC' in l.picking_type_id.
                sequence_id.prefix).move_line_ids_without_package.mapped(
            'location_id')
        wiz_act = self.with_context(auto_check=True).open_produce_product()
        wiz = self.env[wiz_act['res_model']].browse(wiz_act['res_id'])
        wiz.sudo().action_do_produce_generate_lot()
        self.button_mark_done()
        picking_ids = self.picking_ids.filtered(
            lambda l: 'SFP' in l.picking_type_id.
                sequence_id.prefix)
        for picking_id in picking_ids:
            picking_id.move_line_ids_without_package.write({
                'location_dest_id': location_src_id.id
            })
        self.picking_validation()

    @api.multi
    def open_produce_product(self):
        res = super(MrpProduction, self).open_produce_product()
        context = self._context
        auto_check = False
        if 'auto_check' in context:
            auto_check = context['auto_check']
        if auto_check:
            line_product = [line.product_id for line in self.move_raw_ids]
            target_line = self.picking_ids.filtered(lambda p: 'MH/PC' in p.name).move_ids_without_package
            if len(target_line) > 1:
                raise UserError(_("Only One Component Needed for Manufacturing."))
            ex_lot_id = target_line.move_line_ids[0].lot_id if target_line.move_line_ids else False
            last_lot_id = self.env['stock.production.lot'].search(
                [('name', '=', ex_lot_id.name), ('product_id', '=', line_product[0].id)], limit=1)
            if not ex_lot_id and last_lot_id:
                raise UserError(_("The Product Needs Lot."))
            lot_id = self.env['stock.production.lot'].search(
                [('name', '=', ex_lot_id.name), ('product_id', '=', self.product_id.id)], limit=1)
            if lot_id:
                lot_id.sudo().write({
                    'lot_attribute_line_ids': [(6, 0, ex_lot_id.lot_attribute_line_ids.ids)]
                })
            if not lot_id:
                lot_attribute_line_ids = [attribute.copy().id for attribute in ex_lot_id.lot_attribute_line_ids]
                lot_id = self.env['stock.production.lot'].sudo().create({
                    'name': ex_lot_id.name,
                    'product_id': self.product_id.id,
                    'use_date': ex_lot_id.use_date,
                    'removal_date': ex_lot_id.removal_date,
                    'life_date': ex_lot_id.life_date,
                    'alert_date': ex_lot_id.alert_date,
                    'company_id': ex_lot_id.company_id.id,
                    'lot_attribute_line_ids': [(6, 0, lot_attribute_line_ids)]
                    if lot_attribute_line_ids else []
                })
            wiz = self.env['mrp.product.produce'].with_context({'active_id': self.id}).create({'production_id': self.id,
                                                          'product_qty': self.product_qty,
                                                          'product_id': self.product_id.id,
                                                          'product_uom_id': self.product_uom_id.id,
                                                          'cw_product_qty': self.product_cw_uom_qty,
                                                          'product_cw_uom_id': self.product_cw_uom_id.id,
                                                          'lot_id': lot_id.id,
                                                          'produce_line_ids': [(0, 0, {
                                                              'product_id': self.move_raw_ids[0].product_id.id,
                                                          }), ]
                                                          })
            wiz._onchange_product_qty()
            res["res_id"] = wiz.id
            return res
        else:
            return res
