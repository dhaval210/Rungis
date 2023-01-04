from odoo import api, fields, models, http
from odoo.tools.float_utils import float_compare, float_round, float_is_zero
import logging

_logger = logging.getLogger(__name__)

class AppPicking(models.Model):
    _inherit = 'mobile.app.picking'

    @api.model
    def get_line_params(self, params):
        res = {}
        qty_done = self._extract_param(params, 'qty_done', 0)
        lot = self._extract_param(params, 'lot_name', -1)
        location_dest = self._extract_param(params, 'location_dest_id', 0)
        result_package_id = self._extract_param(params, 'result_package_id', False)
        res.update({
            'lot_name': lot,
            'qty_done': qty_done,
            'location_dest_id': location_dest,
        })
        return res

    @api.model
    def save_line(self, params):
        """ Set done quantity for a given move.
        :param params: {'move': move_vals, 'quantity': integer, 'lot_mhd': date, 'lot_name': string, 'pack_number': string, 'location_dest_id': integer}
        """
        StockMoveLine = self.env['stock.move.line']
        move_line_id = self._extract_param(params, 'move.id')
        move_line = StockMoveLine.search([('id', '=', move_line_id)])
        res = self.get_line_params(params)
        if move_line and len(res):
            if res['location_dest_id'] == 0:
                res['location_dest_id'] = move_line.location_dest_id.id
            move_line.sudo().write(res)
            if move_line.package_level_id is not False:
                move_line.package_level_id.sudo().write({
                    'location_dest_id': res['location_dest_id']
                })
            return True
        return False

    @api.model
    def save_new_line(self, params):
        # temp save dest location
        del params['result_package_id']
        location_dest = self._extract_param(params, 'location_dest_id', 0)
        move_line_id = self._extract_param(params, 'id')
        params.update({'move': params})
        # remove before save
        del params['location_dest_id']
        # save line without dest location
        self.save_line(params)
        # duplicate move.line
        StockMoveLine = self.env['stock.move.line']
        move_line = StockMoveLine.search([('id', '=', move_line_id)])
        if move_line.id > 0:
            quantity_left_todo = float_round(
                move_line.product_uom_qty - move_line.qty_done,
                precision_rounding=move_line.product_uom_id.rounding,
                rounding_method='UP'
            )
            done_to_keep = move_line.qty_done
            # new line with done values
            new_move_line = move_line.copy(
                default={
                    'product_uom_qty': 0,
                    'qty_done': move_line.qty_done,
                    'lot_mhd': move_line.lot_id.use_date.date()
                }
            )
            # update old line with new reserved values
            vals = {
                'product_uom_qty': quantity_left_todo,
                'qty_done': 0.0,
                'pack_mhd': False,
                'lot_mhd': False,
                'lot_id': False,
                'lot_name': False,
            }
            move_line.write(vals)
            # update new line with new reserved values
            new_move_line.write(
                {
                    'product_uom_qty': done_to_keep,
                    'location_dest_id': location_dest,
                }
            )
            return new_move_line.id
        return False

    @api.model
    def get_available_locations(self):
        locationsByBarcode = {}
        StockLocation = self.env['stock.location']
        locations = StockLocation.search_read(
            [
                ('usage', '=', 'internal'),
                ('barcode', '!=', None)
            ],
            [
                'barcode',
                'parent_path',
                'name'
            ]
        )
        for location in locations:
            locationsByBarcode.update({location['barcode']: location})
        return locationsByBarcode

    @api.model
    def get_all_locations(self, location_id, product_id, op_default_dest_id):
        putaway = self.get_putaway_location(location_id, product_id)
        if putaway.id:
            return putaway

        locationsByBarcode = {}
        StockLocation = self.env['stock.location']
        locations = StockLocation.search_read(
            [
                ('id', 'child_of', op_default_dest_id),
                ('barcode', '!=', None)
            ],
            [
                'barcode',
                'parent_path',
                'name'
            ]
        )
        for location in locations:
            locationsByBarcode.update({location['barcode']: location})
        return locationsByBarcode

    @api.model
    def get_putaway_location(self, location_id, product_id):
        loc = self.env['stock.location'].browse(location_id)
        prod = self.env['product.product'].browse(product_id)
        return loc.get_putaway_strategy(prod)

    @api.model
    def print_picking(self, rec_id):
        pdf = self.env.ref('stock.action_report_picking').sudo().render_qweb_pdf(
            int(rec_id)
        )
        return pdf[0]

    @api.model
    def get_picking_by_scan(self, value, operation_type=False, picking_id=False):
        """get_picking_by_scan tries to find a picking based on a scanned barcode

        It tries to find a picking based on:
            1. Checks if the scanned barcode is a picking or order name (origin)
            2. Searches for packs with the scanned value and finds pickings based on the pack
            3. Searches for lots with the scanned value and finds pickings based on the lot

        Args:
            value (str): Value of scanned barcode
            operation_type (int, optional): id of operation type. Defaults to False.
            picking_id (int, optional): id of picking, required for finding correct lots

        Returns:
            dict: Containing the picking id and picking_type_id
        """
        StockPicking = self.env['stock.picking']
        # Find pickings based on the picking name or the origin
        picking = StockPicking.search(
            [
                '|',
                ('name', '=', value),
                ('origin', '=', value),
                ('state', '=', 'assigned')
            ],
            limit=1
        )
        disable_product_scan = False
        disable_pack_scan = False
        disable_lot_scan = False

        picking_type = None
        # If operation type is given find more information about that
        if operation_type:
            StockPickingType = self.env['stock.picking.type']
            picking_type = StockPickingType.browse([operation_type])
        # If a picking type was found get settings from there
        if picking_type and picking_type.id > 0:
            disable_product_scan = picking_type.disable_product_scan
            disable_pack_scan = picking_type.disable_pack_scan
            disable_lot_scan = picking_type.disable_lot_scan

        # If a picking was found return it
        if len(picking) > 0 and picking.id is not False:
            return {
                'picking': picking.id,
                'picking_type_id': picking.picking_type_id.id
            }
        else:
            # Find pickings based on the package of move lines
            StockPackage = self.env['stock.quant.package']
            # Find the package with the scanned value
            pack = StockPackage.search([
                ('name', '=', value),
            ], limit=1)
            # If a package was found and pickings can be found by packs, find the related picking
            if len(pack) > 0 and pack.id is not False and disable_pack_scan is False:
                StockPackageLevel = self.env['stock.package_level']
                pl = StockPackageLevel.search([
                    ('package_id', '=', pack.id),
                ])
                picking_ids = pl.mapped('picking_id')
                picking = StockPicking.search([
                    ('id', 'in', picking_ids.ids),
                    ('state', '=', 'assigned')
                ], limit=1)
                # If a picking was found by pack, return it
                if len(picking) > 0 and picking.id is not False:
                    return {
                        'picking': picking.id,
                        'picking_type_id': picking.picking_type_id.id
                    }
            else:
                # Find pickings based on the lot of the move lines
                StockLot = self.env['stock.production.lot']
                # Search the lot itself, company_id?
                lot = StockLot.search([
                        ('name', '=', value),
                    ],
                    limit=1
                )
                # If a lot was found and pickings can be found by lots, find the related picking
                if lot.id is not False and disable_lot_scan is False:
                    StockMoveLine = self.env['stock.move.line']
                    # Build domain for finding move lines
                    domain = [
                        ('lot_id', '=', lot.id),
                        ('state', '=', 'assigned')
                    ]
                    if picking_type and picking_type.id:
                        domain.append(("picking_id.picking_type_id", "=", picking_type.id))
                    if picking_id is not None and picking_id is not False:
                        domain.append(("picking_id", "=", picking_id))
                    # Get stock.move.line with the lot
                    ml = StockMoveLine.search(
                        domain,
                        limit=1
                    )
                    # If a line was found return it's picking
                    if ml.id is not False:
                        return {
                            'picking': ml.picking_id.id,
                            'picking_type_id': ml.picking_id.picking_type_id.id
                        }
            return False

    @api.model
    def _export_move_line(self, line, custom_fields):
        res = super()._export_move_line(line, custom_fields)
        res.update({
            'location_from': line.location_id.name,
            'location_to': line.location_dest_id.name,
            'force_internal_process': line.picking_id.picking_type_id.force_internal_process,
            'picking_id': line.picking_id.id
        })
        return res

    @api.model
    def _export_picking_type(self, picking_type):
        res = super()._export_picking_type(picking_type)
        res.update({
            'show_location_info': picking_type.show_destination_mobile,
            'disable_product_scan': picking_type.disable_product_scan,
            'disable_package_scan': picking_type.disable_pack_scan,
            'disable_lot_scan': picking_type.disable_lot_scan,
            'force_internal_process': picking_type.force_internal_process,
            'op_def_loc_id': picking_type.default_location_dest_id.id
        })
        return res
