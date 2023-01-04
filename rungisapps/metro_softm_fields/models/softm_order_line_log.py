from odoo import api, fields, models


class SoftmLineLog(models.Model):
    _name = 'softm.order.line.log'
    _description = 'PO Line Log'

    order_lr_id = fields.Many2one(comodel_name='purchase.order.line')
    mode = fields.Selection(selection=[
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
    ])
    send_to_softm = fields.Boolean(default=False)
    ol_seq = fields.Integer(
        string='Sequence',
        compute='_compute_fields',
        store=True
    )
    order_line_ref_id = fields.Integer()
    ol_product_id = fields.Integer(compute='_compute_fields', store=True)
    order_ref_id = fields.Integer(compute='_compute_fields', store=True)
    order_ref_name = fields.Char(compute='_compute_fields', store=True)
    ol_location_number = fields.Char(compute='_compute_fields', store=True)

    ol_product_qty = fields.Float(compute='_compute_fields', store=True)
    ol_product_uom = fields.Integer(compute='_compute_fields', store=True)
    ol_price_unit = fields.Float(compute='_compute_fields', store=True)

    ol_product_cw_qty = fields.Float(compute='_compute_fields', store=True)
    ol_product_cw_uom = fields.Integer(compute='_compute_fields', store=True)

    ol_product_uom_so_qty = fields.Float(
        compute='_compute_fields',
        store=True
    )
    ol_product_uom_so_id = fields.Integer(
        compute='_compute_fields',
        store=True
    )
    ol_product_uom_price_unit = fields.Float(
        compute='_compute_fields',
        store=True
    )

    ol_date_planned = fields.Datetime(compute='_compute_fields', store=True)
    ol_company_id = fields.Integer(compute='_compute_fields', store=True)

    @api.depends('order_lr_id')
    def _compute_fields(self):
        for rec in self:
            if rec.ol_product_id == 0 and rec.mode != 'delete':
                pol = rec.order_lr_id
                rec.ol_seq = abs(pol.id) % 1000
                rec.order_ref_id = pol.order_id.id
                rec.order_ref_name = pol.order_id.name
                rec.ol_company_id = pol.order_id.company_id.id
                rec.ol_product_id = pol.product_id.id
                rec.ol_location_number = pol.softm_location_number

                rec.ol_product_qty = pol.product_qty
                rec.ol_product_uom = pol.product_uom
                rec.ol_price_unit = pol.price_unit

                rec.ol_product_cw_qty = pol.product_cw_uom_qty
                rec.ol_product_cw_uom = pol.product_cw_uom

                sale_uom = pol.product_id.uom_id
                if len(pol.product_uom):
                    rec.ol_product_uom_so_qty = pol.product_uom._compute_quantity(
                        rec.ol_product_qty,
                        sale_uom
                    )
                    rec.ol_product_uom_price_unit = pol.product_uom._compute_price(
                        rec.ol_price_unit,
                        sale_uom
                    )                  
                rec.ol_product_uom_so_id = sale_uom

                rec.ol_date_planned = pol.new_date_planned
        return True
