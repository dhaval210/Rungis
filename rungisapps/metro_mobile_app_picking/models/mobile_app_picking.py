# Copyright (C) 2019 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, models
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class MobileAppPicking(models.Model):
    _name = 'mobile.app.picking'
    _inherit = ['mobile.app.mxin']

    # Overload Section
    @api.model
    def get_custom_fields_list(self):
        picking_id = self.env.context.get('picking_id', False)
        StockPicking = self.env['stock.picking']
        if picking_id:
            picking = StockPicking.browse(picking_id)
            return [
                x.name
                for x in picking.picking_type_id.mobile_product_field_ids]
        return []

    @api.model
    def get_picking_types(self):
        """Return Picking Types available for the Mobile App
        :return: [picking_type_1_vals, picking_type_2_vals, ...]
        .. seealso:: _export_picking_type() for picking type vals details.
        """
        StockPickingType = self.env['stock.picking.type']
        picking_types = StockPickingType.search(
            self._get_picking_type_domain())
        return [
            self._export_picking_type(picking_type)
            for picking_type in picking_types]

    @api.model
    def get_pickings(self, params):
        """ Return pickings of a given picking type
        :param params: {'picking_type': picking_type_1_vals}
        :return: [picking_1_vals, picking_2_vals, ...]
        .. seealso::
            _export_picking_type() for picking type vals details
            _export_picking() for picking vals details
        """
        StockPicking = self.env['stock.picking']
        picking_type_id = self._extract_param(params, 'picking_type.id')
        pickings = StockPicking.search(
            self._get_picking_domain(picking_type_id))
        return [
            self._export_picking(picking) for picking in pickings]

    @api.model
    def get_moves(self, params):
        """ Return moves of a given picking.
        :param params: {'picking': picking_vals}
        :return: [move_1_vals, move_2_vals, ...]
        .. seealso::
            _export_picking() for picking vals details
            _export_move() for move vals details
        """
        StockMoveLine = self.env['stock.move.line']
        picking_id = self._extract_param(params, 'picking.id')
        if picking_id is False:
            raise ValidationError(_("The picking_id must be set."))
        lines = StockMoveLine.search([('picking_id', '=', picking_id)])
        custom_fields = self.with_context(
            picking_id=picking_id)._get_custom_fields_dict()
        return [
            self._export_move_line(line, custom_fields)
            for line in lines]

    @api.model
    def set_quantity(self, params):
        """ Set done quantity for a given move.
        :param params: {'move': move_vals, 'quantity': integer}
        """
        StockMoveLine = self.env['stock.move.line']
        move_line_id = self._extract_param(params, 'move.id')
        qty_done = self._extract_param(params, 'qty_done', 0)
        move_line = StockMoveLine.search([('id', '=', move_line_id)])
        if move_line:
            move_line.qty_done = qty_done
        return True

    @api.model
    def try_validate_picking(self, params):
        """ simulate the click on "Validate" button, to know if
        backorder is possible, etc.
        :param params: {'picking': picking_vals}
        """
        StockPicking = self.env['stock.picking']
        picking_id = self._extract_param(params, 'picking.id')
        picking = StockPicking.search([('id', '=', picking_id)])

        if not picking:
            raise ValidationError("No picking with picking_id %s found. Is the picking assigned to a Gate?" % picking_id)

        ready_picking_count = StockPicking.search_count([
            ("picking_type_id", "=", picking.picking_type_id.id),
            ("state", "=", "assigned")
        ])

        res = picking.with_context(
            skip_overprocessed_check=True).button_validate()
        if not res and ready_picking_count <= 1:
            return "picking_validated_no_left"
        elif not res:
            return "picking_validated"
        model = res.get('res_model', False)
        if model == 'stock.immediate.transfer':
            return 'immediate_transfer'
        elif model == 'stock.backorder.confirmation':
            return 'backorder_confirmation'
        else:
            raise UserError(_(
                "incorrect value for model %s" % (model)))

    @api.model
    def confirm_picking(self, params):
        """ Confirm a given picking
        :param params: {
            'picking': picking_vals,
            'action': string,
        }
        action can :
        - 'immediate_transfer' if no quantity has been set
        - 'with_backorder', to create a backorder
        - 'without_backorder', to cancel the backorder
        """

        StockPicking = self.env['stock.picking']
        WizardImmediate = self.env['stock.immediate.transfer']
        WizardBackorder = self.env['stock.backorder.confirmation']

        picking_id = self._extract_param(params, 'picking.id')
        action = self._extract_param(params, 'action')
        picking = StockPicking.sudo().search([('id', '=', picking_id)])

        if action == 'immediate_transfer':
            wizard = WizardImmediate.create(
                {'pick_ids': [(6, 0, picking.ids)]})
            try:
                wizard.sudo().process()
            except Exception as e:
                _logger.error(e)
                raise e
        else:
            wizard = WizardBackorder.create(
                {'pick_ids': [(6, 0, picking.ids)]})
            if action == 'with_backorder':
                try:
                    wizard.sudo().process()
                except Exception as e:
                    _logger.error(e)
                    raise e
            else:
                wizard.sudo().process_cancel_backorder()
        return True

    # Domain Section
    @api.model
    def _get_picking_type_domain(self):
        return [('mobile_available', '=', True)]

    @api.model
    def _get_picking_domain(self, picking_type_id=False):
        return [
            ('state', '=', 'assigned'),
            ('picking_type_id', '=', picking_type_id),
        ]

    # Export Section
    @api.model
    def _export_picking_type(self, picking_type):
        return {
            'id': picking_type.id,
            'name': picking_type.name,
            'warehouse': self._export_warehouse(picking_type.warehouse_id),
            'code': picking_type.code,
            'color': picking_type.color,
            'count_picking_ready': picking_type.count_picking_ready,
            'highlight_picking': picking_type.hightlight_picking,
        }

    @api.model
    def _export_warehouse(self, warehouse):
        return {
            'id': warehouse.id,
            'code': warehouse.code,
            'name': warehouse.name,
        }

    @api.model
    def _export_picking(self, picking):
        if not picking:
            return {}
        return {
            'id': picking.id,
            'name': picking.name,
            'state': picking.state,
            'origin': picking.origin,
            'backorder': self._export_picking(picking.backorder_id) if picking.sudo().backorder_id.gate_id.id is not False else 0,
            'partner': self._export_partner(picking.partner_id),
        }

    @api.model
    def _export_move(self, move, custom_fields):
        return {
            'id': move.id,
            'uom': self._export_uom(move.product_uom),
            'product': self._export_product(move.product_id, custom_fields),
            'qty_expected': move.product_uom_qty,
            'qty_done': move.quantity_done,
        }

    @api.model
    def _export_move_line(self, line, custom_fields):
        return {
            'id': line.id,
            'uom': self._export_uom(line.product_uom_id),
            'product': self._export_product(line.product_id, custom_fields),
            'qty_expected': line.product_uom_qty,
            'qty_done': line.qty_done,
            'package_id': line.package_id.name,
            'result_package_id': line.result_package_id.name,
            # write or line.lot_name, this might fix the error
            'lot_id': line.lot_id.name or line.lot_name,
            'location_dest_id': line.location_dest_id.id,
        }

    @api.model
    def _export_product(self, product, custom_fields):
        res = super(MobileAppPicking, self)._export_product(product, custom_fields)
        res.update({"no_expiry": product.no_expiry})
        return res
