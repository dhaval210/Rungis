from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('picking_id') and vals.get('product_id'):
                existing_ids = self.search([
                    ('product_id', '=', vals['product_id'])
                ])
                if not len(existing_ids):
                    product = self.env['product.product'].browse(
                        vals['product_id']
                    )
                    if not product.collect_data:
                        product.write({'collect_data': True})
                        note = (
                            'collect data for product: ' +
                            str(product.name) +
                            ' (' +
                            str(product.default_code) +
                            ')'
                        )
                        self.env['mail.activity'].create({
                            'res_id': vals['picking_id'],
                            'res_model_id': self.env['ir.model'].search([
                                ('model', '=', 'stock.picking')
                            ]).id,
                            'activity_type_id': self.env.ref(
                                'mail.mail_activity_data_todo'
                            ).id,
                            'note': note,
                            'user_id': self.env.user.id,
                        })
        return super().create(vals_list)
