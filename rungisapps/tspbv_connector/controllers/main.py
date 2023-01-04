import werkzeug
import time
from odoo import http
from odoo.exceptions import ValidationError, UserError, AccessError
from werkzeug.wrappers import Response
from werkzeug.contrib.sessions import Session

from odoo.http import OpenERPSession
from odoo.addons.web.controllers.main \
    import db_monodb, ensure_db, set_cookie_and_redirect, login_and_redirect
import logging
from odoo.tools.float_utils import float_is_zero

_logger = logging.getLogger(__name__)


class TspbvController(http.Controller):
    def get_session(self):
        env = http.request.env()
        Session = env['tspbv.session']
        uid = env.uid
        return Session.search([('user_id', '=', uid)], limit=1)

    @http.route('/tspbv/init', auth='none')
    def init(self, db, user, password, workflow_id=1):
        # this only works with dbfilter set to a specific db
        # return 'test'
        resp = login_and_redirect(
            db,
            user,
            password,
            redirect_url='/tspbv/success'
        )
        # # uid = OpenERPSession.authenticate(http.request, db, user, password)
        # uid = http.request.session.authenticate(db, login=user, password=password)
        # return werkzeug.utils.redirect('/tspbv/success?workflow_id=' + workflow_id)
        # # return http.redirect(
        return resp

    def check_user_access(self):
        env = http.request.env()
        try:
            env['stock.overprocessed.transfer'].check_access_rights('create')
            env['stock.overprocessed.transfer'].check_access_rights('read')
            env['stock.overprocessed.transfer'].check_access_rights('write')
            env['stock.backorder.confirmation'].check_access_rights('create')
            env['stock.backorder.confirmation'].check_access_rights('read')
            env['stock.backorder.confirmation'].check_access_rights('write')
            env['stock.picking.batch'].check_access_rights('read')
            env['stock.picking.batch'].check_access_rights('write')
            env['stock.picking'].check_access_rights('read')
            env['stock.picking'].check_access_rights('write')
            env['stock.move.line'].check_access_rights('read')
            env['stock.move.line'].check_access_rights('write')
            env['stock.move'].check_access_rights('read')
            env['stock.move'].check_access_rights('write')
            env['stock.location'].check_access_rights('read')
            env['res.users'].check_access_rights('read')
            env['res.config.settings'].check_access_rights('read')
            env['stock.quant'].check_access_rights('read')
        except AccessError as identifier:
            return False
        return True

    @http.route('/tspbv/success', auth='user')
    def success(self):
        env = http.request.env()
        if not self.check_user_access():
            # returns no permission template and terminates connection
            return self.dialoglist('permission', False)
        if env.user.workflow_id.id is False:
            env.user.workflow_id = env.ref('tspbv_connector.workflow_1')
        workflow = env['tspbv.workflow'].search([
            ('id', '=', env.user.workflow_id.id)
        ])
        init_xml = workflow.generate_init_xml(0)
        return http.request.make_response(
            init_xml,
            [('Content-Type', 'text/xml')]
        )

    @http.route('/tspbv/dialoglist', auth='user')
    # parameter may change based on generate_dialoglist_xml method
    def dialoglist(self, dialoglist_code, record_id):
        env = http.request.env()
        # session = self.get_session()  # not used?
        dialoglist = env['tspbv.dialoglist'].search([
            ('default_code', '=', dialoglist_code)
        ])
        dialoglist = dialoglist.generate_dialoglist_xml(record_id)
        return http.request.make_response(
            dialoglist,
            [('Content-Type', 'text/xml')]
        )

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
        # return self.dialoglist(
        #     dialoglist_code,
        #     model_rec_id
        # )
        # for current simple cases, transport will require different return and location needs lines
        return self.lines(dialoglist_code)

    def idle(self, dialoglist_code, record_id):
        # wait X seconds
        env = http.request.env()
        session = self.get_session()
        if (session.picking_retries > 5):
            session.write({'picking_retries': 0})
            return self.dialoglist(
                env.ref('tspbv_connector.dialoglist_5_1').default_code,
                record_id
            )

        # time.sleep(10)
        return self.dialoglist(
            dialoglist_code,
            record_id
        )

    @http.route('/tspbv/lines', auth='user')
    def lines(self, dialoglist_code, skip=False):
        env = http.request.env()
        session_data = self.get_session()
        if skip:
            highest_sort = session_data.current_line_ids.sorted(
                key=lambda r: r.sort, reverse=True
            )[0].sort
            session_data.current_item_id.write({
                'sort': highest_sort + 1
            })
        line_ids = session_data.current_line_ids.sorted(
            key=lambda r: r.sort
        ).ids

        for line_id in line_ids:
            index = session_data.current_line_ids.ids.index(line_id)
            line = session_data.current_line_ids[index]
            if not line.voice_picked:
                data = {
                    'current_item_id': line.id,
                    'current_location_id': line.location_id.id,
                }
                if not session_data.location_dest_id:
                    data['location_dest_id'] = line.location_dest_id.id
                session_data.write(data)
                # parameter may change based on generate_dialoglist_xml method
                return self.dialoglist(
                    dialoglist_code,
                    line.id
                )           
        # check if finished call finish or something else
        return self.dialoglist(
            env.ref('tspbv_connector.dialoglist_9').default_code,
            session_data.location_dest_id
        )
        # return self.finish(
        #     'finish'
        # )
        # todo call complete picking/s route

    @http.route('/tspbv/item/load', auth='user')
    def item_load(self, dialoglist_code):
        session_data = self.get_session()
        return self.dialoglist(
            dialoglist_code,
            session_data.current_item_id
        )

    @http.route('/tspbv/item/commit', auth='user', csrf=False)
    def item_commit(self, dialoglist_code, qty):
        # http.request.params
        # set qty to stock move
        session_data = self.get_session()
        session_data.current_item_id.write({
            'voice_picked': True, 'qty_done': qty
        })
        return self.lines(dialoglist_code)
        # return self.dialoglist(
        #     dialoglist_code,
        #     session_data.current_item_id
        # )

    @http.route('/tspbv/item/scrap', auth='user')
    def item_scrap(self, dialoglist_code, qty):
        # http.request.params
        # scrap qty
        session_data = self.get_session()
        env = http.request.env()
        location_id = session_data.current_item_id.picking_id.location_id
        picking = session_data.current_item_id.picking_id
        product = session_data.current_item_id.product_id
        item_qty = session_data.current_item_id.product_qty

        # create scrap
        data = {
            'product_id': product.id,
            'product_uom_id': session_data.current_item_id.product_uom_id.id,
            'scrap_qty': qty,
            'location_id': session_data.current_item_id.location_id.id,
        }
        # assign lot when set
        if session_data.current_item_id.lot_id:
            data['lot_id'] = session_data.current_item_id.lot_id

        scrap = env['stock.scrap'].create(data)
        # scrap qty
        scrap.action_validate()

        # redirect to template if available
        available_qty = env['stock.quant']._get_available_quantity(
            product,
            location_id
        )

        if available_qty > item_qty:
            # rereserve qty for correct location
            model_rec_id = session_data.model_res_id
            model_rec_id = env[session_data.model_id.model].search(
                [('id', '=', model_rec_id)],
                limit=1
            )
            picking.action_assign()
            self.set_session_data(
                session_data,
                session_data.model_id,
                model_rec_id
            )
            return self.lines(dialoglist_code)

        # else cancel (onhold) picking
        return self.cancel(env.ref('tspbv_connector.dialoglist_10').default_code)

    @http.route('/tspbv/transport', auth='user')
    def transport(self, dialoglist_code):
        # get transport units
        # record_id 1 as temp workaround
        return self.dialoglist(
            dialoglist_code,
            1
        )

    @http.route('/tspbv/cancel', auth='user')
    def cancel(self, dialoglist_code):
        # set picking to hold
        env = http.request.env()
        session = self.get_session()
        model_rec = env[session.model_id.model].search([
            ('id', '=', session.model_res_id)
        ], limit=1)
        if model_rec.id:
            model_rec.write({
                'state': 'on_hold'
            })
        return self.dialoglist(
            dialoglist_code,
            session.model_res_id
        )

    @http.route('/tspbv/finish', auth='user')
    def finish(self, dialoglist_code):
        env = http.request.env()
        session = self.get_session()
        model_name = session.model_id.model
        model_rec = env[model_name].search([
            ('id', '=', session.model_res_id)
        ], limit=1)
        pickings = []

        # complete order based on model
        if model_name == 'stock.picking':
            self.picking_validate(model_rec)
        elif model_name == 'stock.picking.batch':
            for picking in session.picking_ids:
                try:
                    self.picking_validate(picking)
                except UserError as e:
                    _logger.exception(e)
            pickings = model_rec.mapped('picking_ids').filtered(
                lambda picking: picking.state not in ('cancel', 'done'))
            if len(pickings) == 0:
                model_rec.done()
                model_rec.write({'voice_picked': True})
        else:
            return ValidationError('invalid model supplied')

        session.write({'location_dest_id': False})
        session.unlink()
        if (
            model_name == 'stock.picking.batch' and
            len(pickings) == 0
        ):
            return self.dialoglist(
                'batch_finish',
                0
            )
        return self.dialoglist(
            dialoglist_code,
            0
        )

    @http.route(['/tspbv/fetch_x2m_data'], type='json', auth='public')
    def get_o2x_data(self, **kwargs):
        env = http.request.env()
        o2x_records = kwargs.get('o2x_records')
        o2x_datas = []
        for record in o2x_records:
            o2x_model = record.get('relation', False)
            o2x_ids = record.get('raw_value', False)
            if o2x_model:
                o2x_obj = env[o2x_model]
                o2x_datas.append(o2x_obj.search_read([('id', 'in', o2x_ids)]))
        return o2x_datas

    def picking_validate(self, model_rec):
        env = http.request.env()
        params = env['ir.config_parameter'].sudo()
        backorder = params.get_param('tspbv_connector.allow_backorder')
        precision_digits = env['decimal.precision'].precision_get('Product Unit of Measure')
        if model_rec._get_overprocessed_stock_moves() and not model_rec._context.get('skip_overprocessed_check'):
            overprocessed_wizard = env['stock.overprocessed.transfer'].create({'picking_id': model_rec.id})
            overprocessed_wizard.action_confirm()
        zero_lines = model_rec.move_line_ids.filtered(lambda m: m.qty_done == 0)            
        check_backorder = model_rec._check_backorder()
        no_quantities_done = all(
            float_is_zero(
                move_line.qty_done, precision_digits=precision_digits) for move_line in model_rec.move_line_ids.filtered(
                    lambda m: m.state not in ('done', 'cancel')
            )
        )
        if check_backorder:
            backorder_confirm = env['stock.backorder.confirmation'].create(
                {'pick_ids': [(4, p.id) for p in model_rec]})
            if backorder:
                backorder_confirm.process()
            else:
                backorder_confirm.process_cancel_backorder()
        if no_quantities_done:
            model_rec.action_cancel()
        elif not check_backorder:
            model_rec.button_validate()
        if len(zero_lines) > 0 and not no_quantities_done:
            zero_lines.write({'voice_picked': False})

    def set_session_data(self, session_id, model_id, model_rec_id):
        line_ids, session_picks = self.get_lines(model_id, model_rec_id)
        # set model and record id to session
        session_id.write({
            'model_id': model_id.id,
            'model_res_id': model_rec_id.id,
            'current_line_ids': [(6, 0, line_ids)],
            'picking_ids': [(6, 0, session_picks)],
            'picking_retries': 0
        })

    def get_lines(self, model, model_rec):
        env = http.request.env()
        if model.model:
            if model.model == 'stock.picking':
                return model_rec.move_line_ids_without_package.sorted(
                        key=lambda r: r.location_id.sort
                    ).ids
            elif model.model == 'stock.picking.batch':
                line_ids = []
                pickings = model_rec.mapped('picking_ids').filtered(
                    lambda picking: picking.state not in ('cancel', 'done'))                
                count = 1
                session_picks = []
                user = model_rec.user_id
                for picking in pickings:
                    for ml in picking.move_line_ids_without_package:
                        ml.write({'sort': ml.location_id.sort})
                    session_picks += [picking.id]
                    line_ids += picking.move_line_ids_without_package.ids
                    if count == user.picker_count:
                        break
                    count += 1
                return line_ids, session_picks
            raise ValidationError(("model: %s is not allowed", model.model))
        raise ValidationError("parameter model is no valid model")
