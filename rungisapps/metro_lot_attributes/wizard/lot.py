from odoo import models, fields


class LotLot(models.TransientModel):
    _name = 'lot.lot'

    def action_get_lots(self):
        model = self.env['stock.lot.attribute.lines'].search([])
        lots = []
        attr_lines = model.search(
            [('attribute_id', "!=", False), ('value_ids', "=", False), ('mandatory', '=', True)])
        for attr in attr_lines:
            if not attr.value_ids and attr.lot_id:
                lots.append(attr.lot_id.id)
        lots = list(set(lots))
        new_lots = []
        for lot in lots:
            new_lots.append({
                'lot_id': lot
            })
        return new_lots

    lot_lines = fields.One2many('missing.lot', 'wizard_id', string="Purchases",
                                     default=action_get_lots)


class PurchaseOrderLineHistory(models.TransientModel):
    _name = "missing.lot"

    wizard_id = fields.Many2one('lot.lot')
    lot_id = fields.Many2one('stock.production.lot', 'Lot/Serial Number')


