# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models
class StockLocation(models.Model):
    _inherit = 'stock.location'

    product_turnover = fields.Selection([('a', 'A'), ('b', 'B'), ('c', 'C')], default=False)

    # def get_putaway_strategy(self, product):
    #     ''' Returns the location where the product has to be put, if any compliant putaway strategy is found. Otherwise returns None.'''
    #     current_location = self
    #     putaway_location = self.env['stock.location']
    #     while current_location and not putaway_location:
    #         if current_location.putaway_strategy_id:
    #             putaway_location = current_location.putaway_strategy_id.with_context(current_location=current_location).putaway_apply(product)
    #         current_location = current_location.location_id
    #     return putaway_location

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_turnover = fields.Selection([('a', 'A'), ('b', 'B'), ('c', 'C')], default=False)


class PutAwayStrategy(models.Model):
    _inherit = 'product.putaway'

    product_turnover = fields.Boolean("Take product turnover into account")
    storage_location = fields.Boolean("Take storage location into account")
    empty_location = fields.Boolean("Only propose empty locations")
    metro_putaway = fields.Boolean("Metro Putaway")

    def putaway_apply(self, product):
        loc = self.env['stock.location']
        put_away = self._get_putaway_rule(product)
        if put_away:
            loc = put_away.fixed_location_id
        if loc and self.metro_putaway:    
            if self.product_turnover:
                locations = self.env['stock.location'].search([('id', 'child_of', loc.id), ('product_turnover', '=', product.product_turnover)])
            else:
                locations = self.env['stock.location'].search([('id', 'child_of', loc.id)])

            if locations and self.empty_location:
                empty_locations = self.env['stock.location']
                for l in locations:
                    if l.usage == 'internal':
                        if self.env['stock.quant'].search_count([('location_id', '=', l.id)]) == 0:
                            empty_locations |= l
                locations = empty_locations

            if locations and self.storage_location:
                distances = locations.mapped(lambda l: (l, (loc.posx - l.posx)**2 + (loc.posy - l.posy)**2 + (loc.posz - l.posz)**2))
                skip_loc = 0 if not self._context.get('skip_loc') else min(self._context.get('skip_loc',[1])[0], len(distances)-1)
                locations = sorted(distances, key=lambda d: d[1])[skip_loc][0]
                previous_loc = self._context.get('skip_loc',[1, self.env['stock.location']])[1]
                if locations ==  previous_loc or loc == previous_loc:
                    # we consider that there are no more empty locations if the previous putaway location for this product:
                    # - is the same as the one we're indicating now
                    # - is the fixed location for this product
                    # in this case we return the fixed location
                    return loc

            if locations:
                return locations
        return loc
            
        
