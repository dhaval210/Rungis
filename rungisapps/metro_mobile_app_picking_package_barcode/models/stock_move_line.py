from odoo import api, fields, models
from odoo.exceptions import ValidationError


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    pack_number = fields.Char()

    @api.multi
    def write(self, vals):
        res = []
        # if 'qty_done' in vals and self.product_uom_qty < vals.get('qty_done'):
        #     raise ValidationError("excess quantities are not allowed")
        for line in self:
            if (
                    line.picking_id.sudo().picking_type_id.code == 'incoming' and
                    not line.result_package_id.id and
                    vals.get('pack_number') and
                    vals.get('pack_number') is not False
            ):
                # do some checks
                package = self.env['stock.quant.package']
                if (not package.check_name(vals.get('pack_number'))):
                    raise ValidationError("pack number already in use")
                res += [super(StockMoveLine, line).write(vals)]
                pack = line.picking_id.put_in_pack()
                pack.write({'name': vals.get('pack_number')})
                # to fix last position no lot
                line.pack_number = False
                # line.lot_id = False
                # line.lot_name = False
            elif (line.picking_id.sudo().picking_type_id.code == 'incoming' and line.result_package_id.id and
                  vals.get('pack_number') and vals.get('pack_number') is not False):
                # update the given package
                package = line.result_package_id
                if (not package.check_name(vals.get('pack_number'))):
                    raise ValidationError("pack number already in use")
                line.result_package_id.write({'name': vals.get('pack_number')})
                res += [super(StockMoveLine, line).write(vals)]
            else:
                res += [super(StockMoveLine, line).write(vals)]
        return res
