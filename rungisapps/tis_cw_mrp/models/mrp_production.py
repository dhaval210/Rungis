# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    catch_weight_ok = fields.Boolean(invisible='1', related='product_id.catch_weight_ok')
    cw_product_qty = fields.Float(
        'CW Quantity To Produce',
        digits=dp.get_precision('Product CW Unit of Measure'))
    product_cw_uom_id = fields.Many2one(
        'uom.uom', 'Product CW Unit of Measure')
    cw_qty_produced = fields.Float(compute="_get_cw_produced_qty", string="Quantity Produced")
    product_cw_uom_qty = fields.Float(string='Total CW Quantity', compute='_compute_product_uom_cw_qty', store=True)

    @api.depends('product_uom_id', 'product_qty', 'product_id.uom_id', 'product_cw_uom_id', 'cw_product_qty',
                 'product_id.cw_uom_id')
    def _compute_product_uom_cw_qty(self):
        for production in self:
            if production.product_id.cw_uom_id != production.product_cw_uom_id:
                production.product_cw_uom_qty = production.product_cw_uom_id._compute_quantity(
                    production.cw_product_qty,
                    production.product_id.cw_uom_id)
            else:
                production.product_cw_uom_qty = production.cw_product_qty

    @api.multi
    @api.depends('workorder_ids.state', 'move_finished_ids', 'is_locked')
    def _get_cw_produced_qty(self):
        for production in self:
            done_moves = production.move_finished_ids.filtered(
                lambda x: x.state != 'cancel' and x.product_id.id == production.product_id.id)
            cw_qty_produced = sum(done_moves.mapped('cw_qty_done'))
            production.cw_qty_produced = cw_qty_produced
        return True

    @api.onchange('product_qty')
    def onchange_product_qty(self):
        if self.product_id and self.product_qty and self.bom_id.product_qty:
            factor = self.product_uom_id._compute_quantity(self.product_qty,
                                                           self.bom_id.product_uom_id) / self.bom_id.product_qty
            self.cw_product_qty = self.bom_id.cw_product_qty * factor

    @api.onchange('product_id', 'picking_type_id', 'company_id')
    def onchange_product_id(self):
        res = super(MrpProduction, self).onchange_product_id()
        if not self.product_id:
            self.bom_id = False
        else:
            domain_dict = res.get('domain')
            domain_dict.update({'product_cw_uom_id': [('category_id', '=', self.product_id.cw_uom_id.category_id.id)]})
            bom = self.env['mrp.bom']._bom_find(product=self.product_id, picking_type=self.picking_type_id,
                                                company_id=self.company_id.id)
            if bom.type == 'normal':
                self.cw_product_qty = self.bom_id.cw_product_qty
                self.product_cw_uom_id = self.bom_id.product_cw_uom_id.id
            else:
                self.product_cw_uom_id = self.product_id.cw_uom_id.id
        return res

    @api.onchange('bom_id')
    def _onchange_bom_id(self):
        super(MrpProduction, self)._onchange_bom_id()
        self.cw_product_qty = self.bom_id.cw_product_qty
        self.product_cw_uom_id = self.bom_id.product_cw_uom_id.id

    @api.multi
    def _generate_moves(self):
        for production in self:
            if production.bom_id.product_tmpl_id.product_variant_id._is_cw_product():
                cw_factor = production.product_cw_uom_id._compute_quantity(production.cw_product_qty,
                                                                           production.bom_id.product_cw_uom_id) / production.bom_id.cw_product_qty
                context = self._context.copy()
                if context.get('cw_params'):
                    context['cw_params'].update({'cw_quantity_factor': cw_factor})
                else:
                    context['cw_params'] = {'cw_quantity_factor': cw_factor}
                self.env.context = context
        return super(MrpProduction, self)._generate_moves()

    def _generate_finished_moves(self):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(MrpProduction, self)._generate_finished_moves()
        if not self.product_id._is_cw_product():
            return super(MrpProduction, self)._generate_finished_moves()
        move = self.env['stock.move'].create({
            'name': self.name,
            'date': self.date_planned_start,
            'date_expected': self.date_planned_start,
            'picking_type_id': self.picking_type_id.id,
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'product_cw_uom': self.product_cw_uom_id.id,
            'product_uom_qty': self.product_qty,
            'product_cw_uom_qty': self.cw_product_qty,
            'location_id': self.product_id.property_stock_production.id,
            'location_dest_id': self.location_dest_id.id,
            'company_id': self.company_id.id,
            'production_id': self.id,
            'warehouse_id': self.location_dest_id.get_warehouse().id,
            'origin': self.name,
            'group_id': self.procurement_group_id.id,
            'propagate': self.propagate,
            'move_dest_ids': [(4, x.id) for x in self.move_dest_ids],
        })
        move._action_confirm()
        return move

    def _generate_raw_move(self, bom_line, line_data):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(MrpProduction, self)._generate_raw_move(bom_line, line_data)
        cw_original_quantity = (self.cw_product_qty - self.cw_qty_produced) or 1.0 if self.product_id._is_cw_product() \
            else (self.product_qty - self.qty_produced) or 1.0
        res = super(MrpProduction, self)._generate_raw_move(bom_line, line_data)
        quantity = line_data['cw_qty']
        res.write({
            'product_cw_uom': bom_line.product_cw_uom_id.id, })
        if quantity:
            res.write({
                'product_cw_uom': bom_line.product_cw_uom_id.id,
                'product_cw_uom_qty': quantity,
                'cw_unit_factor': quantity / cw_original_quantity,
            })
        return res

    def _get_raw_move_data(self, bom_line, line_data):

        res = super(MrpProduction, self)._get_raw_move_data(bom_line, line_data)
        if not 'cw_qty' in line_data:
            return res
        cw_quantity = line_data['cw_qty']
        if bom_line.child_bom_id and bom_line.child_bom_id.type == 'phantom':
            return
        if bom_line.product_id.type not in ['product', 'consu']:
            return
        cw_original_quantity = (self.cw_product_qty - self.cw_qty_produced) or 1.0 if self.product_id._is_cw_product() \
            else (self.product_qty - self.qty_produced) or 1.0
        res.update({
            'product_cw_uom_qty': cw_quantity,
            'product_cw_uom': bom_line.product_cw_uom_id.id,
            'cw_unit_factor': cw_quantity / cw_original_quantity,
        })
        return res

    def _workorders_create(self, bom, bom_data):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(MrpProduction, self)._workorders_create(bom, bom_data)
        quantity = self.product_qty - sum(self.move_finished_ids.mapped('quantity_done'))
        quantity = quantity if (quantity > 0) else 0
        cw_quantity = self.cw_product_qty - sum(self.move_finished_ids.mapped('cw_qty_done'))
        cw_quantity = cw_quantity if (cw_quantity > 0) else 0

        if self.product_id.tracking == 'serial':
            cw_quantity = cw_quantity / quantity

        if self.product_id.tracking == 'lot':
            context = self._context.copy()
            if context.get('cw_params'):
                context['cw_params'].update({'generate_lot_ids_qty': cw_quantity})
            else:
                context['cw_params'] = {'generate_lot_ids_qty': cw_quantity}
            self.env.context = context
        return super(MrpProduction, self)._workorders_create(bom, bom_data)

    @api.multi
    def _update_raw_move(self, bom_line, line_data):
        if not self.env.user.has_group('tis_catch_weight.group_catch_weight'):
            return super(MrpProduction, self)._update_raw_move( bom_line, line_data)
        cw_quantity = line_data.get('cw_qty', 0)
        context = self._context.copy()
        if context.get('cw_params'):
            context['cw_params'].update({'decrease_reserved_qty': cw_quantity})
        else:
            context['cw_params'] = {'decrease_reserved_qty': cw_quantity}
        self.env.context = context
        self.ensure_one()
        move = self.move_raw_ids.filtered(
            lambda x: x.bom_line_id.id == bom_line.id and x.state not in ('done', 'cancel'))
        if move:
            if cw_quantity and cw_quantity > 0:
                move[0].with_context(do_not_unreserve=True).write({'product_cw_uom_qty': cw_quantity})
                if move[0].raw_material_production_id.product_id._is_cw_product():
                    move[0].unit_factor = cw_quantity / move[0].raw_material_production_id.cw_product_qty
        return super(MrpProduction, self)._update_raw_move(bom_line, line_data)
