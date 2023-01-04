
from odoo import api, fields, models,_

class IrAttachment(models.Model):
    _inherit='ir.attachment'
    
    to_transfert = fields.Boolean('attachment to transfer',default=False)
    data_to_transfert = fields.Boolean('attachment to transfer',default=False)