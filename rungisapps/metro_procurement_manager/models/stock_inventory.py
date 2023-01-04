from odoo import api, fields, models,_
from odoo.exceptions import Warning as UserWarning
from odoo.exceptions import ValidationError


class Inventory(models.Model):
    _inherit = 'stock.inventory'

    def action_start(self):
        # nobody is allowed to do inventory while scheduler is active
        locations = self.env['stock.location'].search([
            ('id', 'child_of', [self.location_id.id])
        ]).ids
        exclude_location = self.get_excluded_locations()
        if any(item in locations for item in exclude_location):
            raise UserWarning('picking in progress for this or a sub location. stop the scheduler first')

        # normal user is not allowed to do inventory, when pickings are still in ready state
        if not self.env.user.has_group('metro_procurement_manager.group_inventory_master'):
            exclude_location = self.get_excluded_by_picking()
            if (
                exclude_location is not False and
                any(item in locations for item in exclude_location)
            ):
                raise UserWarning('there are still pickings in progress. wait until finished')
        return super().action_start()

    @api.model
    def create(self, values):
        self.check_excluded_locations(values)
        return super().create(values)

    @api.multi
    def write(self, values):
        for inv in self:
            inv.check_excluded_locations(values)
        return super().write(values)

    def check_excluded_locations(self, values):
        # nobody is allowed to do inventory while scheduler is active
        exclude_location = self.get_excluded_locations()
        if (
            'location_id' in values and
            values['location_id'] in exclude_location
        ):
            raise UserWarning('picking in progress for this or a sub location. stop the scheduler first')

        # normal user is not allowed to do inventory, when pickings are still in ready state
        if not self.env.user.has_group('metro_procurement_manager.group_inventory_master'):
            exclude_location = self.get_excluded_by_picking()
            if (
                exclude_location is not False and
                'location_id' in values and
                values['location_id'] in exclude_location
            ):
                raise UserWarning('there are still pickings in progress. wait until finished')
        return True

    def get_excluded_by_picking(self):
        types = self.env['stock.picking.type'].search([
            ('allow_block', '=', True),
        ])
        if types and len(types):
            pickings = self.env['stock.picking'].search([
                ('state', '=', 'assigned'),
                ('picking_type_id', 'in', types.ids),
            ])
            if len(pickings):
                type_ids = pickings.mapped('picking_type_id').ids
                if len(type_ids):
                    return self.get_excluded_locations(False, type_ids)
        return False

    def get_excluded_locations(self, block=True, ids=False):
        domain = [
            ('allow_block', '=', True),
        ]
        if block is True:
            domain += [('block_stock_assignment', '=', False)]
        if ids is not False:
            domain += [('id', 'in', ids)]
        types = self.env['stock.picking.type'].search(domain)
        locations = types.mapped('default_location_src_id').ids
        exclude_locations = self.env['stock.location'].search([
            ('id', 'child_of', locations)
        ]).ids
        return exclude_locations

    @api.multi
    def action_validate(self):
        for line in self.line_ids:
            if line.product_id.standard_price == 0.0:
                raise ValidationError(_('Inventory Adjustment with Zero Cost is not possible. Please check the cost of product: ' + line.product_id.display_name))
        res = super(Inventory, self).action_validate()
        return res

    def action_reset_product_qty(self):
        for line in self.line_ids:
            if not line.preset_reason_id:
                raise ValidationError(_('Please enter the Preset Reason for the product: ' + line.product_id.display_name))
        super(Inventory, self).action_reset_product_qty()
        return True

