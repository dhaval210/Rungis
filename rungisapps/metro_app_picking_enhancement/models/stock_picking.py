from odoo import api, models, fields
from odoo.http import request


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def open_mobile_app_url(self):
        self.ensure_one()
        base_path = request.httprequest.url_root
        app_path = base_path + "metro_app_picking_enhancement/static/www/index.html"
        type_path = "{}#/picking_type/{}".format(
            app_path, self.picking_type_id.id
        )
        picking_path = "{}/picking/{}/list_move_line".format(
            type_path, self.id
        )
        client_action = {
            "type": "ir.actions.act_url",
            "name": "Edit From Mobile App",
            "target": "new",
            "url": picking_path,
        }
        return client_action
