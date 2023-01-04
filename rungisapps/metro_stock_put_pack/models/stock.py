# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_round


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    apply_packrules = fields.Boolean('Apply Pack Rules', help='Will check if pack rule are defined on the product before put-in-pack and apply them')


class StockPackRule(models.Model):
    _name = 'stock.pack.rule'

    name = fields.Char('Name', required=True)


class StockPackRuleValue(models.Model):
    _name = 'stock.pack.rule.value'

    name = fields.Char('Name', required=True)
    rule_id = fields.Many2one('stock.pack.rule', string='Rule', required=True)

    _sql_constraints = [
        ('name_rule_uniq', 'unique(name, rule_id)', 'The name of the value must be unique per rule in Pack!'),
    ]


class StockPackProductRule(models.Model):
    _name = 'stock.pack.product.rule'
    _order = "stock_packrule_id"

    stock_packrule_id = fields.Many2one('stock.pack.rule', string='Rule')
    product_id = fields.Many2one('product.template', string='Product')
    warehouse_id = fields.Many2one('stock.warehouse',  string='Warehouse')
    value_id = fields.Many2one('stock.pack.rule.value',  string='Value', domain="[('rule_id', '=', stock_packrule_id)]")


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _put_in_pack(self):
        not_apply_packrules = self.filtered(lambda p: not p.picking_type_id.apply_packrules)
        if not_apply_packrules:
            return super(StockPicking, not_apply_packrules)._put_in_pack()
        package = False
        for pick in self.filtered(lambda p: p.state not in ('done', 'cancel')):
            move_line_ids = pick.move_line_ids.filtered(lambda o: o.qty_done > 0 and not o.result_package_id)
            if move_line_ids:
                move_lines_to_pack = self.env['stock.move.line']
                for ml in move_line_ids:
                    if float_compare(ml.qty_done, ml.product_uom_qty,
                                     precision_rounding=ml.product_uom_id.rounding) >= 0:
                        move_lines_to_pack |= ml
                    else:
                        quantity_left_todo = float_round(
                            ml.product_uom_qty - ml.qty_done,
                            precision_rounding=ml.product_uom_id.rounding,
                            rounding_method='UP')
                        done_to_keep = ml.qty_done
                        new_move_line = ml.copy(
                            default={'product_uom_qty': 0, 'qty_done': ml.qty_done})
                        ml.write({'product_uom_qty': quantity_left_todo, 'qty_done': 0.0})
                        new_move_line.write({'product_uom_qty': done_to_keep})
                        move_lines_to_pack |= new_move_line

                # START =================================================================
                warehouse = pick.picking_type_id.warehouse_id
                products = move_lines_to_pack.mapped('product_id')
                if any(products.mapped('allow_variants')) and len(products.mapped('product_tmpl_id')) > 1:
                    raise UserError(_("It is only allowed to put products of the same 'template' in the same pack if only allow_variants is True"))
                if any(products.mapped('allow_same_category')) and len(products.mapped('categ_id')) > 1:
                    raise UserError(_("It is only allowed to put products of the same 'category' in the same pack if only allow_same_category is True"))

                stock_pack_rules = products.mapped('stock_product_rule_ids').filtered(lambda s: not s.warehouse_id or s.warehouse_id == warehouse)
                rules = self.env['stock.pack.product.rule']
                msg = "The packing rules forbids to include those products in the same pack: "
                if stock_pack_rules:
                    for p in products:
                        rule = stock_pack_rules.filtered(lambda s: s.product_id != p.product_tmpl_id)
                        for d in p.stock_product_rule_ids.filtered(lambda s: not s.warehouse_id or s.warehouse_id == warehouse):
                            rules |= rule.filtered(lambda s: s.stock_packrule_id == d.stock_packrule_id and s.value_id != d.value_id)
                    if len(rules):
                        raise UserError(_("%s \n %s" % (msg, '\n'.join([str(r.product_id.name+', '+r.stock_packrule_id.name+', '+str(r.value_id.name)) for r in rules]))))
                # END =================================================================
                package = self.env['stock.quant.package'].create({})
                package_level = self.env['stock.package_level'].create({
                    'package_id': package.id,
                    'picking_id': pick.id,
                    'location_id': False,
                    'location_dest_id': move_line_ids.mapped('location_dest_id').id,
                    'move_line_ids': [(6, 0, move_lines_to_pack.ids)]
                })
                move_lines_to_pack.write({
                    'result_package_id': package.id,
                })
            else:
                raise UserError(_('You must first set the quantity you will put in the pack.'))
        return package
