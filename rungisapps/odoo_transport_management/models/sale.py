# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Sale(models.Model):
    _inherit = 'sale.order'
    
    transporter_id = fields.Many2one(
        'res.partner',
        string="Transporter"
    )

    @api.multi #Pass value of client to pay in create invoice.
    def _prepare_invoice(self):
       res = super(Sale, self)._prepare_invoice()
       if self.transporter_id:
           vals = {
               'transporter_id': self.transporter_id.id,
           }
           res.update(vals)
       return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
