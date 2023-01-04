"""Copyright 2017-18 Eficent Business and IT Consulting Services S.L.
 License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)."""

from odoo import api, models, _


class MrpProduction(models.Model):
    """inherit manufacturing module"""
    _inherit = 'mrp.production'

    @api.model
    def create(self, vals):
        """find location_dest from stock ,get location_id from product,
        return message to create function"""

        location_dest = self.env['stock.location'].browse(vals.get(
            'location_dest_id'))
        product = self.env['product.product'].browse(vals.get('product_id'))
        location_id = location_dest.get_putaway_strategy(product)
        if location_id:
            vals['location_dest_id'] = location_id.id
        manufacturing_order = super(MrpProduction, self).create(vals)
        if location_id:
            message = _(
                "Applied Putaway strategy to finished products.\n"
                "Finished Products Location: %s." %
                manufacturing_order.location_dest_id.complete_name)
            manufacturing_order.message_post(body=message,
                                             message_type='comment')
        return manufacturing_order
