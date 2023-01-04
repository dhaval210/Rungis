import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MoveLine(models.Model):
    _inherit = 'stock.move.line'

    metro_mhd = fields.Date(string='MHD')

    @api.multi
    def write(self, vals):
        res = []
        for line in self:
            if (
                'metro_mhd' in vals and
                vals.get('metro_mhd') is not False
            ):
                mhd = vals.get('metro_mhd')
            elif line.metro_mhd is not False:
                mhd = fields.Date.to_string(line.metro_mhd)
            else:
                mhd = False
            if (
                line.picking_id.picking_type_id.code == 'incoming' and
                'lot_name' in vals and
                mhd is not False and
                'lot_id' not in vals
            ):
                if line.product_id.tracking != 'none':
                    picking_type_id = line.move_id.picking_type_id
                    if picking_type_id:
                        if picking_type_id.use_create_lots:
                            if (
                                vals.get('lot_name') and
                                line.lot_name != vals.get("lot_name")
                            ):
                                lot = self.env['stock.production.lot'].create({
                                    'name': vals.get('lot_name'),
                                    'product_id': line.product_id.id,
                                    'use_date': mhd,
                                })
                                vals.update({'lot_id': lot.id})
                                dates = lot._get_dates(
                                    product_id=line.product_id.id,
                                    ref_date=datetime.datetime.strptime(mhd, '%Y-%m-%d')
                                )
                                lot.write(dates)
                        elif (
                            not picking_type_id.use_create_lots and
                            not picking_type_id.use_existing_lots
                        ):
                            continue
                    elif line.move_id.inventory_id:
                        continue
                    if 'lot_id' not in vals and line.lot_id.id == None:
                        raise UserError(
                            _('You need to supply a lot/serial number for %s.')
                            % line.product_id.name
                        )
                res += [super(MoveLine, line).write(vals)]
            else:
                res += [super(MoveLine, line).write(vals)]
        return res
