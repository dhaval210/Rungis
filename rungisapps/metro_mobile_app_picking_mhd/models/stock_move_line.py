import dateparser
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class MoveLine(models.Model):
    _inherit = 'stock.move.line'

    lot_mhd = fields.Date(string='MHD')

    @api.multi
    def write(self, vals):
        res = []
        for line in self:
            if (
                'lot_mhd' in vals and
                vals.get('lot_mhd') is not False
            ):
                mhd = vals.get('lot_mhd')
            elif (
                'lot_name' in vals and
                line.lot_mhd is not False
            ):
                mhd = fields.Date.to_string(line.lot_mhd)
            else:
                mhd = False
            # Delete the lot_name from vals if value if -1 (equals -1 if no lot was entered/could be extracted)
            if vals.get('lot_name') == -1:
                del vals['lot_name']

            if (
                'lot_name' in vals and
                mhd is not False and
                'lot_id' not in vals
            ):
                if line.product_id.tracking != 'none':
                    picking_type_id = line.move_id.picking_type_id
                    if picking_type_id:
                        lot = self.env["stock.production.lot"].search([
                            ("name", "=", vals.get("lot_name")),
                            ("product_id", "=", line.product_id.id),
                            ("company_id", "=", line.picking_id.company_id.id),
                        ])
                        po_partner = lot.purchase_order_ids.mapped("partner_id.id")
                        use_existing = True
                        # If the current partner is different than the partner the lot was created with
                        # Try to create a new lot instead of using the existing one
                        if len(po_partner) > 0:
                            if line.picking_id.partner_id.id not in po_partner:
                                use_existing = False
                        # Use existing lot for stock.move.line if option is enabled and lot was found
                        if picking_type_id.use_existing_lots and lot.id and use_existing:
                            vals.update({"lot_id": lot.id})
                            lot_mhd = datetime.strptime(vals.get("lot_mhd"), "%m/%d/%Y").date()
                            # Edge case: set use_date to entered mhd if no use date was set before
                            # Fixes error "bool" object has no attribute "date"
                            if not lot.use_date:
                                dates = lot._get_dates(
                                    product_id=line.product_id.id,
                                    ref_date=lot_mhd,
                                )
                                lot.write(dates)
                            elif lot.use_date.date() != lot_mhd:
                                lot.message_post(
                                    body="The use date in picking {} differs from the use date in this lot.<br/>New: {}<br/>Old: {}".format(line.picking_id.name, lot_mhd, lot.use_date.date())
                                )
                                dates = lot._get_dates(
                                    product_id=line.product_id.id,
                                    ref_date=lot_mhd,
                                )
                                lot.write(dates)
                            # del vals["lot_mhd"]
                        # Create new lot if option is enabled and no lot was found
                        else:
                            if (
                                vals.get('lot_name')
                            ):
                                lot = self.env['stock.production.lot'].create({
                                    'name': vals.get('lot_name'),
                                    'product_id': line.product_id.id,
                                    'use_date': mhd,
                                    'company_id': line.picking_id.company_id.id,
                                })
                                vals.update({'lot_id': lot.id})
                                mhd = dateparser.parse(mhd)
                                dates = lot._get_dates(
                                    product_id=line.product_id.id,
                                    ref_date=mhd
                                )
                                lot.write(dates)
                    elif line.move_id.inventory_id:
                        continue
                    if 'lot_id' not in vals and line.lot_id is False:
                        raise UserError(
                            _('You need to supply a lot/serial number for %s.')
                            % line.product_id.name
                        )
            res += [super(MoveLine, line).write(vals)]
        return res
