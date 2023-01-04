from odoo import api, models, _


class MoveLine(models.Model):
    _inherit = 'stock.move.line'

    @api.onchange('qty_done')
    def _onchange_qty_done(self):
        """ When the user is encoding a move line for a tracked product, we apply some logic to
        help him. This onchange will warn him if he set `qty_done` to a non-supported value.
        """
        res = {}

        params = self.env['ir.config_parameter'].sudo()
        block_exceeding = params.get_param(
            'metro_block_exceeding_qty_done.block_exceeding_qty'
        )
        if block_exceeding == 'True':
            filter_id = params.get_param(
                'metro_block_exceeding_qty_done.block_qty_filter_id'
            )
            filter_domain = self.env['ir.filters'].search([
                ('id', '=', filter_id)]
            )._get_eval_domain()

            # check if there is still an open record
            model_rec_ids = self.env['stock.picking.type'].search(
                filter_domain
            )
            if self.picking_id.picking_type_id.id in model_rec_ids.ids:
                if self.qty_done > self.product_uom_qty:
                    message = _('You can only pick a maximum of %s for the product.') % self.product_uom_qty
                    res['warning'] = {'title': _('Warning'), 'message': message}
                    return res
        return super()._onchange_qty_done()
