# -*- coding: utf-8 -*-

import random
import string
from odoo import models, fields, api, _
from odoo.exceptions import Warning as UserWarning


class ResPartner(models.Model):
    """Implement company wide unique identification number."""

    _inherit = 'res.partner'

    identification_id = fields.Char(string='Identification No', copy=False)

    old_identification_id = fields.Char(string='Old Identification No', copy=False)

    @api.model
    def _generate_identification_id(self):
        """Generate a random partner/customer identification number"""
        company = self.env.user.company_id
        partner_id = False
#        if self.customer == True:
        if company.partner_id_gen_method == 'sequence':
            partner_id = company.partner_id_sequence.next_by_id()
        elif company.partner_id_gen_method == 'random':
            partner_id_random_digits = company.partner_id_random_digits
            tries = 0
            max_tries = 50
            while tries < max_tries:
                rnd = random.SystemRandom()
                partner_id = ''.join(rnd.choice(string.digits)
                                     for _ in
                                     xrange(partner_id_random_digits))
                if not self.search_count([('ref', '=', partner_id)]):
                    break
                tries += 1
            if tries == max_tries:
                raise UserWarning(_('Unable to generate an Partner/Customer ID number that \
                is unique.'))
        return partner_id

    @api.model
    def create(self, vals):
        if vals.get('customer', False) or vals.get('supplier', False):
            # if not vals.get('ref') and not vals.get('parent_id', False): # 13march
            if not vals.get('ref'):
                vals['ref'] = self._generate_identification_id()
        return super(ResPartner, self).create(vals)

    @api.multi
    def write(self, vals):
        result = super(ResPartner, self).write(vals)

        check_field_list= ['customer', 'supplier', 'parent_id']
        if any(field_val in vals for field_val in check_field_list):
            for partner in self:
                if not partner.customer and not partner.supplier:
                    partner.old_identification_id = partner.ref
#                     partner.ref = False
                # elif (partner.customer or partner.supplier) and partner.parent_id: # 13march
                #     partner.old_identification_id = partner.ref # 13march
#                     partner.ref = False
                # elif (partner.customer or partner.supplier) and not partner.parent_id: # 13march
                elif (partner.customer or partner.supplier):
                    if not partner.ref and partner.old_identification_id:
                        partner.ref = partner.old_identification_id
                    elif not partner.ref:
                        partner.ref = self._generate_identification_id()
        return result

    # def init(self, force=False):
    #     partners = self.search([('identification_id', '!=', False)])
    #     for partner in partners:
    #         partner.write({'ref': partner.identification_id})

#     def init(self): #This method is comment in V12 during migration since we do not need it in V12.. it was for  V10 for old / existing records..
#         partners = self.search([
#             ('ref', '=', False),
#             '|',('customer', '=', True),
#             ('supplier', '=', True)
#         ])
#         for partner in partners:
#             ref = self._generate_identification_id()
#             partner.write({'ref': self._generate_identification_id()})