from odoo import models, fields


class StockLot(models.Model):
    _inherit = 'stock.production.lot'

    def aproduct_auto_workflow(self):
        lot_ids = self._context.get('active_ids') or self.ids
        lots = self.browse(lot_ids)
        not_done_locations = []
        for lot_id in lots:
            aproduct_id = self.sync_aproduct(lot_id.product_id)
            if aproduct_id:
                bom_id = self.check_create_aproduct_bom(aproduct_id, lot_id.product_id)
                quant_ids = lot_id.quant_ids.filtered(lambda quant: quant.location_id.usage == 'internal')
                for quant_id in quant_ids:
                    warehouse_id = quant_id.location_id.get_warehouse()
                    if not warehouse_id or quant_id.location_id.id in warehouse_id.aproduct_exclude_location_ids.ids:
                        not_done_locations.append({
                            'product_id': lot_id.product_id.name,
                            'location_id': quant_id.location_id.name,
                            'reason': 'Location has no warehouse' if not warehouse_id else 'Location is excluded from'
                                                                                           ' Aproduct workflow'
                        })
                        continue
                    if not warehouse_id.used_for_aproduct:
                        not_done_locations.append({
                            'product_id': lot_id.product_id.name,
                            'location_id': quant_id.location_id.name,
                            'reason': 'This warehouse is not used for Aproduct auto workflow'
                        })
                        continue
                    val = {
                        'product_tmpl_id': aproduct_id.product_tmpl_id.id,
                        'product_id': aproduct_id.id,
                        'product_uom_id': quant_id.product_uom_id.id,
                        'product_qty': quant_id.quantity,
                        'bom_id': bom_id.id,
                        'location_src_id': warehouse_id.pbm_loc_id.id,
                        'location_dest_id': warehouse_id.sam_loc_id.id,
                    }
                    if aproduct_id.catch_weight_ok:
                        val.update({
                            'cw_product_qty': quant_id.cw_stock_quantity,
                            'product_cw_uom_id': quant_id.product_cw_uom.id,
                        })
                    mo_id = self.env['mrp.production'].create(val)
                    self.make_stock_pickings(quant_id.location_id, mo_id)
                    picking_type = mo_id.picking_type_id.warehouse_id.pbm_type_id.id
                    mo_id.picking_ids.filtered(lambda l: picking_type != l.picking_type_id.id).\
                        move_line_ids_without_package.write({
                            'cw_qty_done': mo_id.cw_product_qty,
                            'qty_done': mo_id.product_qty
                        })
                    mo_id.mrp_auto_flow()
                    cost_loss = lot_id.product_id.standard_price * lot_id.product_id.categ_id.get_aproduct_factor()
                    total_loss = cost_loss * mo_id.cw_product_qty if lot_id.product_id.catch_weight_ok else cost_loss * mo_id.product_qty
                    get_param = self.env['ir.config_parameter'].sudo().get_param
                    account_id = get_param('metro_rungis_mrp_autoworkflow.aproduct_loss_account_id')
                    line_vals = [(0, 0, {
                        'account_id': lot_id.product_id.categ_id.property_stock_valuation_account_id.id,
                        'name': 'Aproduct value loss',
                        'debit': 0,
                        'credit': total_loss
                    }), (0, 0, {
                        'account_id': int(account_id) if account_id else False,
                        'name': 'Aproduct value loss',
                        'debit': total_loss,
                        'credit': 0
                    })]
                    self.env['account.move'].create({
                        'ref': mo_id.name,
                        'date': fields.Date.today(),
                        'company_id': lot_id.product_id.company_id.id,
                        'journal_id': lot_id.product_id.categ_id.property_stock_journal.id,
                        'line_ids': line_vals,
                    }).action_post()
                    template = self.env.ref('metro_rungis_mrp_autoworkflow.'
                                            'aproduct_manufacture_template')
                    context = {
                        'product_id': lot_id.product_id,
                        'qty': mo_id.product_qty,
                        'uom_id': mo_id.product_uom_id,
                        'warehouse': lot_id.product_id.softm_location_number,
                        'user_id': self.env.user
                    }
                    template.with_context(context).send_mail(mo_id.id)
            else:
                not_done_locations.append({
                    'product_id': lot_id.product_id.name,
                    'location_id': 'No location',
                    'reason': 'No Aproduct found'
                })
        return not_done_locations

    def sync_aproduct(self, product):
        if 'N' in product.default_code:
            code = product.default_code.replace('N', 'A')
        elif 'R' in product.default_code:
            code = product.default_code.replace('R', 'A')
        else:
            code = 'A' + product.default_code
        aproduct_id = self.env['product.product'].sudo().search([
            ('default_code', '=', code),
            ('company_id', '=', 1)
        ], limit=1)
        if aproduct_id:
            attribute_line_ids = [attribute.copy().id for attribute in product.attribute_line_ids]
            factor = product.categ_id.get_aproduct_factor()
            aproduct_id.write({
                'name': product.name,
                'taxes_id': product.taxes_id.ids,
                'standard_price': product.standard_price * factor,
                'categ_id': product.categ_id.id,
                'hs_code_id': product.hs_code_id.id,
                'origin_country_id': product.origin_country_id.id,
                'last_purchase_price': product.last_purchase_price * factor,
                'sale_ok': True,
                'purchase_ok': False,
                'softm_location_number': product.softm_location_number,
                'attribute_line_ids': [(6, 0, attribute_line_ids)]
            })
            return aproduct_id
        return False

    def check_create_aproduct_bom(self, aproduct_id, product_id):
        bom_ids = aproduct_id.bom_ids.filtered(lambda bom: bom.bom_line_ids.filtered(lambda line: line.product_id.id == product_id.id))
        if bom_ids:
            return bom_ids[0]
        else:
            bom_val = {
                'product_tmpl_id': aproduct_id.product_tmpl_id.id,
                'product_uom_id': aproduct_id.uom_id.id,
                'product_qty': 1,
                'type': 'normal',
                'ready_to_produce': 'all_available',
            }
            if product_id.catch_weight_ok:
                bom_val.update({
                    'product_cw_uom_id': aproduct_id.cw_uom_id.id,
                    'cw_product_qty': aproduct_id.average_cw_quantity,
                })
            bom_id = self.env['mrp.bom'].create(bom_val)
            bom_line_val = {
                'product_tmpl_id': product_id.product_tmpl_id.id,
                'product_id': product_id.id,
                'product_uom_id': product_id.uom_id.id,
                'product_qty': 1,
                'auto_lot_creation': True,
                'bom_id': bom_id.id
            }
            if product_id.catch_weight_ok:
                bom_line_val.update({
                    'product_cw_uom_id': product_id.cw_uom_id.id,
                    'cw_product_qty': product_id.average_cw_quantity,
                })
            self.env['mrp.bom.line'].create(bom_line_val)
            return bom_id

    def make_stock_pickings(self, location, mo_id):
        picking_type = mo_id.picking_type_id.warehouse_id.pbm_type_id
        for picking in mo_id.picking_ids:
            if picking.picking_type_id.id == picking_type.id:
                picking.location_id = location.id
                for move in picking.move_ids_without_package:
                    move.location_id = location.id
            else:
                picking.location_dest_id = location.id
                for move in picking.move_ids_without_package:
                    move.location_dest_id = location.id
