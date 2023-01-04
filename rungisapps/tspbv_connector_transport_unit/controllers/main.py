from odoo import http
from odoo.exceptions import ValidationError
from odoo.addons.tspbv_connector.controllers.main import TspbvController
import logging
import time

_logger = logging.getLogger(__name__)


class TransportUnitTspbvController(TspbvController):
    @http.route('/tspbv/start', auth='user')
    def start(self, model, dialoglist_code, idle=False):
        if idle:
            time.sleep(10)

        # allowed models & config parameter
        allowed_models = {
            'stock.picking': 'tspbv_connector.assign_picking_filter_id',
            'stock.picking.batch': ('tspbv_connector.'
                                    'assign_batch_picking_filter_id')
        }
        env = http.request.env()
        Model = env['ir.model']
        uid = env.uid

        # check allowed models
        if model not in allowed_models:
            raise ValidationError(
                ('the use of the model: %s is not allowed', model))

        # get & check odoo model parameter
        model_id = Model.search([('model', '=', model)], limit=1)
        if not model_id.id:
            raise ValidationError(
                ('model: %s not found or not installed yet', model))

        # get user session
        session_id = self.get_session()

        # create session if no exists
        if not session_id.id:
            _logger.info('create session for user %s', env.user.name)
            session_id = env['tspbv.session'].create(
                {'user_id': uid}
            )
        if not session_id.id:
            raise ValidationError('could not create session!!!!!!')
        # get filter domain from configuration
        params = env['ir.config_parameter'].sudo()
        filter_id = params.get_param(allowed_models.get(model))
        filter_domain = env['ir.filters'].search([
            ('id', '=', filter_id)]
        )._get_eval_domain()
        my_domain = [('user_id', '=', uid)]
        my_domain += filter_domain

        # check if there is still an open record
        model_rec_id = env[model].search(my_domain, limit=1)

        if not model_rec_id.id:
            # get model record without assigned user
            my_domain = [('user_id', '=', False)]
            my_domain += filter_domain
            model_rec_id = env[model].search(
                my_domain,
                limit=1
            )

            if model_rec_id.id:
                model_rec_id.write(
                    {'user_id': uid}
                )
                self.set_session_data(session_id, model_id, model_rec_id)
                # and user to model record
            else:
                retries = session_id.picking_retries + 1
                session_id.write({'picking_retries': retries})
                # parameter may change based on generate_dialoglist_xml method
                return self.idle(
                    env.ref('tspbv_connector.dialoglist_5').default_code,
                    1
                )

        # reset in case of switch between stock.picking & stock.picking.batch
        if session_id.model_id != model_id:
            self.set_session_data(session_id, model_id, model_rec_id)
        else:
            session_id.write({'picking_retries': 0})
        # return dialoglist
        # parameter may change based on generate_dialoglist_xml method
        if env.user.workflow_id.transport_unit_dialoglist.id is not False:
            dialoglist = env.user.workflow_id.transport_unit_dialoglist
            return self.dialoglist(
                dialoglist.default_code,
                session_id
            )
        else:
            return self.lines('location')
        # for current simple cases, transport will require different return and location needs lines
        # return self.lines(dialoglist_code)

    @http.route('/tspbv/transport', auth='user')
    def transport(self, dialoglist_code):
        return self.lines(dialoglist_code)

    @http.route('/tspbv/transport_label', auth='user')
    def transport_label(self, dialoglist_code, print=False):
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
        return self.dialoglist(
            dialoglist_code,
            session_data.id
        )

    @http.route('/tspbv/label', auth='user')
    def label(self, dialoglist_code, print=True):
        # do print action
        session_data = self.get_session()
        env = http.request.env()
        if print == 'True':
            pdf = env.ref('metro_rungis_report.label').render_qweb_pdf(
                session_data.current_item_id.picking_id.id
            )
            pdf = env.ref('metro_rungis_report.label2').render_qweb_pdf(
                session_data.current_item_id.picking_id.id
            )            
        if dialoglist_code == 'qty' or dialoglist_code == 'qty-fast':
            data_id = session_data.current_item_id
        else:
            data_id = session_data.current_item_id.picking_id.id
        return self.dialoglist(
            dialoglist_code,
            data_id
        )

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
            if env.user.workflow_id.stash_dialoglist.id is not False:
                dialoglist = env.user.workflow_id.stash_dialoglist
                return self.dialoglist(
                    dialoglist.default_code,
                    session_data.current_item_id.picking_id
                )
            else:
                return self.lines('location')
        elif not session_data.current_item_id.catch_weight_ok:
            session_data.current_item_id.write({
                'voice_picked': True, 'qty_done': qty
            })
            if env.user.workflow_id.stash_dialoglist.id is not False:
                dialoglist = env.user.workflow_id.stash_dialoglist
                return self.dialoglist(
                    dialoglist.default_code,
                    session_data.current_item_id.picking_id
                )
            else:
                return self.lines('location')
        else:
            session_data.current_item_id.write({
                'qty_done': qty
            })
            dialoglist_code = env.ref('tspbv_connector_cw.dialoglist_cw_1').default_code
        return self.lines(dialoglist_code)
