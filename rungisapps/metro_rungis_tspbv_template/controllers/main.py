from odoo import http
from odoo.addons.tspbv_connector_location_picker.controllers.main import TspbvController


class TransportUnitTspbvController(TspbvController):

    @http.route('/tspbv/item/load', auth='user')
    def item_load(self, dialoglist_code):
        env = http.request.env()
        session_data = self.get_session()
        if env.user.workflow_id == env.ref('metro_rungis_tspbv_template.workflow_2'):
            dialoglist_code = 'qty-fast'
        return self.dialoglist(
            dialoglist_code,
            session_data.current_item_id
        )

    @http.route('/tspbv/transport_location', auth='user')
    def transport_location(self, dialoglist_code, print=False):
        # do print action
        session_data = self.get_session()
        env = http.request.env()
        if print == 'True':
            pdf = env.ref('metro_rungis_report.label').render_qweb_pdf(
                session_data.picking_ids.ids
            )
            pdf = env.ref('metro_rungis_report.label2').render_qweb_pdf(
                session_data.picking_ids.ids
            )            
        return self.lines(dialoglist_code)
