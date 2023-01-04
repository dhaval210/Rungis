from odoo import http
from odoo.addons.tspbv_connector.controllers.main import TspbvController
import logging

_logger = logging.getLogger(__name__)


class CwTspbvController(TspbvController):
    @http.route('/tspbv/item/commit', auth='user', csrf=False)
    def item_commit(self, dialoglist_code, qty, cw=False):
        # http.request.params
        # set qty to stock move
        env = http.request.env()
        session_data = self.get_session()
        if cw:
            # change float string to float
            qty = qty.replace('komma', '.')
            qty = qty.replace(' ', '')
            qty = float(qty)
            session_data.current_item_id.write({
                'voice_picked': True, 'cw_qty_done': qty
            })
        elif not session_data.current_item_id.catch_weight_ok:
            session_data.current_item_id.write({
                'voice_picked': True, 'qty_done': qty
            })
        else:
            session_data.current_item_id.write({
                'qty_done': qty
            })
            dialoglist_code = env.ref('tspbv_connector_cw.dialoglist_cw_1').default_code
        return self.lines(dialoglist_code)
