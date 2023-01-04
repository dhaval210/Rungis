from odoo import http
from odoo.addons.tspbv_connector.controllers.main import TspbvController
from odoo.exceptions import ValidationError, UserError, AccessError
import logging

_logger = logging.getLogger(__name__)


class TransportUnitTspbvController(TspbvController):
    @http.route('/tspbv/finish', auth='user')
    def finish(self, dialoglist_code):
        env = http.request.env()
        session = self.get_session()
        params = env['ir.config_parameter'].sudo()

        model_name = session.model_id.model
        model_rec = env[model_name].search([
            ('id', '=', session.model_res_id)
        ], limit=1)
        batch_pick_count = []

        async_pick = bool(params.get_param('tspbv_connector.async_pick'))

        if async_pick is True:
            if session.model_id.model == 'stock.picking':
                model_rec.async_pick = True
            elif session.model_id.model == 'stock.picking.batch':
                session.picking_ids.write({
                    'async_pick': True
                })
                batch_pick_count = len(model_rec.picking_ids.filtered(
                    lambda m: m.async_pick is False and m.state not in ('cancel', 'done')
                ))
                if batch_pick_count == 0:
                    model_rec.write({
                        'async_pick': True
                    })

            env['tspbv.validate'].with_delay(eta=2).validate_session(
                session.model_id.model,
                session.picking_ids,
                model_rec
            )

        else:
            batch_pick_count = len(model_rec.picking_ids.filtered(
                lambda m: m.state not in ('cancel', 'done')
            ))            
            env['tspbv.validate'].validate_session(
                session.model_id.model,
                session.picking_ids,
                model_rec
            )

        session.write({'location_dest_id': False})
        session.unlink()
        if (
            model_name == 'stock.picking.batch' and
            batch_pick_count == 0
        ):
            return self.dialoglist(
                'batch_finish',
                0
            )        
        return self.dialoglist(
            dialoglist_code,
            0
        )

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
                    lambda picking: (
                        picking.state not in ('cancel', 'done') and
                        picking.async_pick is False
                    )
                ).sorted(
                    key=lambda r: r.run_up_point,
                    reverse=True
                )
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
