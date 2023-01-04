from odoo import models, fields, api, exceptions, _

class PartnerType(models.Model):
    _name = 'partner.type'
    _description = 'Partner Type'

    name = fields.Char(string='Partner Type', required=True)
    account_payable_id = fields.Many2one('account.account', string='Account Payable')
    account_receivable_id = fields.Many2one('account.account', string='Account Receivable')

    _sql_constraints = [

       ('name_unique', 'UNIQUE(name)',
        "The Partner type name must be unique"),
    ]


class Partner(models.Model):
    _inherit = 'res.partner'

    partner_type_id = fields.Many2one('partner.type', string='Partner Type')

    @api.onchange('partner_type_id')
    def _onchange_accounts(self):

        #if no partner_type is finally set, default accounts are re-set
        if not self.partner_type_id:

            #should be a search on the name of account instead of [0] and [1]
            receivable = self.env['ir.property'].search([('res_id', '=', False),('company_id', '=', self.env.user.company_id.id)])[0]
            payable = self.env['ir.property'].search([('res_id', '=', False),('company_id', '=', self.env.user.company_id.id)])[1]
            if receivable:
                recordRec = receivable.value_reference.split(',')
                rec_id = recordRec[1]
                self.property_account_receivable_id = self.env['account.account'].search([('id', '=', rec_id)])
            if payable:
                recordPay = payable.value_reference.split(',')
                pay_id  = recordPay[1]
                self.property_account_payable_id = self.env['account.account'].search([('id', '=', pay_id)])

        else:
            self.property_account_receivable_id = self.partner_type_id.account_receivable_id
            self.property_account_payable_id = self.partner_type_id.account_payable_id


class AccountMove(models.Model):
    _inherit = "account.move"

    partner_type = fields.Char(string='Partner Type', related="partner_id.partner_type_id.name", store=True)
    origin = fields.Char(string='Source Document', related='line_ids.invoice_id.origin')


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    partner_type = fields.Char(string='Partner Type', related="partner_id.partner_type_id.name", store=True)
