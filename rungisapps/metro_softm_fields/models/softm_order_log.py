from odoo import api, fields, models


class PurchaseLog(models.Model):
    _name = 'softm.order.log'
    _description = 'Log PO Changes'

    order_r_id = fields.Many2one(
        'purchase.order')

    mode = fields.Selection(selection=[
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
    ])
    order_ref_id = fields.Integer()
    send_to_softm = fields.Boolean(default=False)
    odoo_id = fields.Integer(compute='_compute_fields', store=True)
    po_name = fields.Char(compute='_compute_fields', store=True)
    po_currency_id = fields.Char(compute='_compute_fields', store=True)
    po_company_id = fields.Integer(compute='_compute_fields', store=True)
    po_partner_ref = fields.Char(compute='_compute_fields', store=True)
    po_partner_id = fields.Integer(compute='_compute_fields', store=True)
    po_user = fields.Char(compute='_compute_fields', store=True)
    po_date_order = fields.Datetime(compute='_compute_fields', store=True)
    po_date_planned = fields.Datetime(compute='_compute_fields', store=True)

    @api.depends('order_r_id')
    def _compute_fields(self):
        for rec in self:
            if rec.po_name is False:
                rec.odoo_id = rec.order_r_id.id
                rec.po_name = rec.order_r_id.name
                rec.po_date_order = rec.order_r_id.date_order
                rec.po_currency_id = rec.order_r_id.currency_id.name
                rec.po_company_id = rec.order_r_id.company_id.id
                rec.po_partner_ref = rec.order_r_id.partner_id.ref
                rec.po_user = rec.order_r_id.user_id.email
                rec.po_partner_id = rec.order_r_id.partner_id.id
                rec.po_date_planned = rec.order_r_id.po_date_planned
        return True
