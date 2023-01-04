from odoo import models, fields, api
from odoo.exceptions import ValidationError
import string

class MetroExtend_StockMove(models.Model):
    _inherit = 'stock.move'

    movement_key = fields.Char(string="Bewegungsschlüssel")
    send_to_softm = fields.Boolean(string="SoftM Status")
    special_wishes = fields.Char(string="Sonderwünsche")

    # def _compute_sequence(self, move_id=False):
    #     for move in self:
    #         if move_id:
    #             line = move_id
    #         else:
    #             line = move.purchase_line_id
    #         if line.sequence:
    #             move.purchase_line_sequence = line.sequence
    #             continue
    #         if len(move.move_orig_ids):
    #             move._compute_sequence(move.move_orig_ids[0])
    #     return True

    # purchase_line_sequence = fields.Integer(
    #     compute="_compute_sequence"
    # )
    softm_location_number = fields.Integer(
        related="picking_id.location_dest_id.softm_location_number"
    )
    process_number = fields.Integer(string="Vorgangsnummer (Mehrplatzlager)")
    process_position = fields.Integer(
        string="Vorgangsposition (Mehrplatzlager)"
    )
    tour_id = fields.Many2one(comodel_name='transporter.route')

    lot_numbers = fields.Char(compute='_compute_lot_numbers', store=True)
    softm_fishing_area = fields.Char(compute='_compute_lot_numbers', store=True)
    softm_sub_fishing_area = fields.Char(compute='_compute_lot_numbers', store=True)

    @api.depends('move_line_ids')
    def _compute_lot_numbers(self):
        for move in self:
            lots = move.move_line_ids.mapped("lot_id")
            if len(lots):
                lot_string = ', '.join(lots.mapped("name"))
                filtered_string = ''.join([x for x in lot_string if x in string.printable])
                move.lot_numbers = filtered_string
                fishing_area_keys = []
                sub_fishing_area_keys = []
                for ml in move.move_line_ids:
                    if ml.lot_id:
                        for attr_line in ml.lot_id.lot_attribute_line_ids:
                            if 'sub fishing area' in attr_line.attribute_id.name.lower():
                                if attr_line.value_ids.softm_key:
                                    sub_fishing_area_keys += [attr_line.value_ids.softm_key]
                            elif 'fishing area' in attr_line.attribute_id.name.lower():
                                if attr_line.value_ids.softm_key:
                                    fishing_area_keys += [attr_line.value_ids.softm_key]
                if len(sub_fishing_area_keys):
                    sub_fishing_area_keys = list(set(sub_fishing_area_keys))
                    move.softm_sub_fishing_area = ', '.join(sub_fishing_area_keys)
                if len(fishing_area_keys):
                    fishing_area_keys = list(set(fishing_area_keys))
                    move.softm_fishing_area = ', '.join(fishing_area_keys)

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        distinct_fields = super()._prepare_merge_moves_distinct_fields()
        distinct_fields.append('process_number')
        distinct_fields.append('process_position')
        distinct_fields.append('special_wishes')
        return distinct_fields

    def _get_new_picking_values(self):
        """ Prepares a new picking for this move as it could not be assigned
        to another picking. This method is designed to be inherited. """
        values = super()._get_new_picking_values()
        if (
            self.move_dest_ids is not False and
            self.process_number == 0
        ):
            for move_dest in self.move_dest_ids:
                if move_dest.process_number != 0:
                    self.process_number = move_dest.process_number
                    self.process_position = move_dest.process_position
                    break

        values.update({
           'transporter_route_id': self.tour_id.id
        })
        return values

    @api.multi
    def _prepare_procurement_values(self):
        """ Prepare specific key for moves or other components that will be created from a stock rule
        comming from a sale order line. This method could be override in order to add other custom key that could
        be used in move/po creation.
        """
        values = super()._prepare_procurement_values()
        self.ensure_one()
        values.update({
            'special_wishes': self.special_wishes,
            'process_number': self.process_number,
            'process_position': self.process_position,
            'sale_line_id': self.sale_line_id.id if self.sale_line_id else False
        })
        return values
