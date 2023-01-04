from odoo import api, fields, models
from odoo.addons.queue_job.job import job
from odoo.exceptions import ValidationError, UserError, AccessError
from odoo.tools.float_utils import float_is_zero
import logging

_logger = logging.getLogger(__name__)


class TspbvValidate(models.Model):
    _name = 'tspbv.validate'

    @job(default_channel='root.tspbv.validate_picking')
    def validate_session(self, model, picking_ids, model_rec):
        # complete order based on model
        if model == 'stock.picking':
            self.picking_validate(model_rec)
        elif model == 'stock.picking.batch':
            for picking in picking_ids:
                try:
                    self.picking_validate(picking)
                except UserError as e:
                    _logger.exception(e)
            pickings = model_rec.mapped('picking_ids').filtered(
                lambda picking: picking.state not in ('cancel', 'done'))
            if len(pickings) == 0:
                model_rec.done()
                model_rec.write({
                    'voice_picked': True,
                })
        else:
            return ValidationError('invalid model supplied')

    def picking_validate(self, model_rec):
        env = self.env
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
            bp_ids = [p.id for p in model_rec]
            backorder_pick = self.env['stock.picking'].search([('backorder_id', 'in', bp_ids)])
            if len(backorder_pick):
                backorder_pick.write({'async_pick': False})                
        if no_quantities_done:
            model_rec.action_cancel()
        elif not check_backorder:
            model_rec.button_validate()
        if len(zero_lines) > 0 and not no_quantities_done:
            zero_lines.write({'voice_picked': False})
