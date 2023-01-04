# -*- coding: utf-8 -*-


from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    buyer_ranking = fields.Integer(string="Buyer Ranking", help="Buyer ranking based on the count of purchase order")

    @api.depends('purchase_order_count')
    def get_buyer_rank(self):
        supplier_ids = self.with_context(active_test=False).search([])
        purchase_order_groups = self.env['purchase.order'].read_group(
            domain=[('user_id', 'in', supplier_ids.ids), ('state', '=', 'purchase'),
                    ('amount_untaxed', '<=', 250), ('amount_untaxed', '>=', 1)],
            fields=['user_id', 'amount_untaxed'], groupby=['user_id']
        )
        sorted_list = sorted(purchase_order_groups, key=lambda k: k['amount_untaxed'], reverse=True)
        i = 0
        for recd in sorted_list:
            i += 1
            recd.update(rank=i)
            user = self.browse(recd['user_id'][0])
            if user:
                user.buyer_ranking = recd['rank']
