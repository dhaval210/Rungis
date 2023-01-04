from odoo import api, fields, models
from datetime import datetime
import dateparser


class MobileAppPicking(models.Model):
    _inherit = 'mobile.app.picking'

    @api.model
    def decode_gs1_barcode(self, barcode):
        try:
            barcode_decoded = self.env['gs1_barcode'].decode(barcode)
        except Exception:
            return False
        product = barcode_decoded.get('02', False)
        if not product:
            # Sometimes the product does not yet have a GTIN. In this case
            # try the AI 240 'Additional product identification assigned
            # by the manufacturer'.
            product = barcode_decoded.get('240', False)
        mhd = barcode_decoded.get('15', False)
        if mhd is False:
            mhd = barcode_decoded.get('17', False)
        if mhd is not False:
            mhd = dateparser.parse(mhd)
            mhd = mhd.strftime("%m/%d/%Y")
        return {
            'product': product,
            'pack': barcode_decoded.get('01', False),
            'lot': barcode_decoded.get('10', False),
            'mhd': mhd,
            'qty': barcode_decoded.get('30', False),
            'weight': barcode_decoded.get('310', False),
        }

    @api.model
    def get_picking_by_scan(self, value, operation_type=False, picking_id=False):

        try:
            barcode_decoded = self.env['gs1_barcode'].decode(value)
            package_barcode = barcode_decoded.get('01', False)
            product_barcode = barcode_decoded.get('02', False)
            if not product_barcode:
                # Sometimes the product does not yet have a GTIN. In this case
                # try the AI 240 'Additional product identification assigned
                # by the manufacturer'.
                product_barcode = barcode_decoded.get('240', False)
            lot_barcode = barcode_decoded.get('10', False)

            disable_product_scan = False
            disable_pack_scan = False
            disable_lot_scan = False
            if operation_type is not False:
                StockPickingType = self.env['stock.picking.type']
                picking_type = StockPickingType.search(
                    [
                        ('id', '=', operation_type)
                    ],
                    limit=1
                )
            if picking_type and picking_type.id > 0:
                disable_product_scan = picking_type.disable_product_scan
                disable_pack_scan = picking_type.disable_pack_scan
                disable_lot_scan = picking_type.disable_lot_scan

            if package_barcode is not False:
                StockPackage = self.env['stock.quant.package']
                pack = StockPackage.search(
                    [
                        ('name', '=', value),
                    ],
                    limit=1
                )
                if len(pack) > 0 and pack.id is not False and disable_pack_scan is False:
                    StockPackageLevel = self.env['stock.package_level']
                    StockPicking = self.env['stock.picking']
                    pl = StockPackageLevel.search(
                        [
                            ('package_id', '=', pack.id),
                        ]
                    )
                    picking_ids = pl.mapped('picking_id')
                    picking = StockPicking.search(
                        [
                            ('id', 'in', picking_ids.ids),
                            ('state', '=', 'assigned')
                        ],
                        limit=1
                    )
                    if len(picking) > 0 and picking.id is not False:
                        return {
                            'picking': picking.id,
                            'picking_type_id': picking.picking_type_id.id
                        }
            if lot_barcode is not False:
                StockLot = self.env['stock.production.lot']
                lot = StockLot.search([
                        ('name', '=', value),
                    ],
                    limit=1
                )
                if lot.id is not False and disable_lot_scan is False:
                    StockMoveLine = self.env['stock.move.line']
                    ml = StockMoveLine.search([
                        ('lot_id', '=', lot.id),
                        ('state', '=', 'assigned')
                        ],
                        limit=1
                    )
                    if ml.id is not False:
                        return {
                            'picking': ml.picking_id.id,
                            'picking_type_id': ml.picking_id.picking_type_id.id
                        }
            return False                        
        except Exception:
            return super().get_picking_by_scan(value, operation_type, picking_id)
