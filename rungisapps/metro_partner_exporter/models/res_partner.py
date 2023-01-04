from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sap_exported = fields.Boolean('SAP exported')
    due_invoices_reminder = fields.Boolean()


    @api.multi
    def write(self, vals):
        """
        With each modification made unsed sap_exported field so that the record is re-exported on the next cron
        run
        :param vals:
        :return:
        """
        if 'sap_exported' not in vals:
            vals['sap_exported'] = False
        return super().write(vals)


class ResPartnerBank(models.Model):

    _inherit='res.partner.bank'

    @api.multi
    def write(self, vals):
        res = super().write(vals)
        if 'acc_number' or 'bank_id' in vals:
            for record in self:
                if record.partner_id and record.partner_id.sap_exported:
                    record.partner_id.write({'sap_exported': False})
        return res


class ResBank(models.Model):
    _inherit = 'res.bank'

    @api.multi
    def write(self, vals):
        res = super().write(vals)
        if 'bic' in vals:
            for record in self:
                partner_banks = self.env['res.partner.bank'].search([('bank_id', '=', record.id)])
                for partner_bank in partner_banks:
                    if partner_bank.partner_id and partner_bank.partner_id.sap_exported:
                        partner_bank.partner_id.write({'sap_exported': False})
        return res