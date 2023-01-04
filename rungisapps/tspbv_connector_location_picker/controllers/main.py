from odoo import http
from odoo.exceptions import ValidationError
from odoo.addons.tspbv_connector_transport_unit.controllers.main import TspbvController
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
        user_location = env.user.picker_location_id.location_id.id
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
        my_domain = ['&', '&']
        my_domain += [('user_id', '=', uid)]
        my_domain += [('location_id', 'child_of', user_location)]
        my_domain += filter_domain

        # check if there is still an open record
        model_rec_id = env[model].search(my_domain, limit=1)

        if not model_rec_id.id:
            # get model record without assigned user
            my_domain = ['&', '&']
            my_domain = [('user_id', '=', False)]
            my_domain += [('location_id', 'child_of', user_location)]
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
        if env.user.workflow_id.transport_unit_dialoglist is not False:
            dialoglist = env.user.workflow_id.transport_unit_dialoglist
            return self.dialoglist(
                dialoglist.default_code,
                session_id
            )
        else:
            return self.lines('location')
        # for current simple cases, transport will require different return and location needs lines
        # return self.lines(dialoglist_code)
