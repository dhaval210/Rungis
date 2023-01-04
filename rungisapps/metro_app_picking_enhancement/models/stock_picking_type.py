# Copyright (C) 2019-Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'
    
    show_destination_mobile = fields.Boolean(
        string='show destination location in mobile app',
        default=False)

    disable_product_scan = fields.Boolean(string='Disable product barcode scan', default=False)
    disable_pack_scan = fields.Boolean(string='Disable package barcode scan', default=False)
    disable_lot_scan = fields.Boolean(string='Disable lot barcode scan', default=False)
    force_internal_process = fields.Boolean(string="Force Internal Process on HHT", default=False)
