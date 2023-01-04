from odoo import models,_
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def unlink(self):
        raise UserError(_('deletion is not possible and the user needs to be archived. '))
