
from odoo import models, fields, api


class ResPartnerConfiguration(models.TransientModel):
    _inherit = 'res.config.settings'

    def _default_id_sequence(self):
        sequence = self.env.user.company_id.partner_id_sequence
        if not sequence:
            sequence = self.env.ref(
                'metro_customer_partner_id.seq_partnerid_ref')
        return sequence and sequence.id or False

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id
    )
    partner_id_gen_method = fields.Selection(selection=[('random', 'Random'),
                                                        ('sequence',
                                                         'Sequence'),
                                                        ],
                                             string="ID Generation Method",
                                             default='random')
    partner_id_random_digits = fields.Char(string='# of Digits',
                                           help="Number of digits making up "
                                                "the ID")
    partner_id_sequence = fields.Many2one('ir.sequence', string='Partner ID '
                                          'Sequence', readonly=False,
                                          help="Pattern to be used for "
                                               "partner ID Generation",
                                          default=_default_id_sequence)

    @api.model
    def get_values(self):
        res = super(ResPartnerConfiguration, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res.update(
            partner_id_gen_method=get_param(
                'metro_customer_partner_id.partner_id_gen_method'),
            partner_id_random_digits=get_param(
                'metro_customer_partner_id.partner_id_random_digits'),
        )
        return res

    @api.multi
    def set_values(self):
        super(ResPartnerConfiguration, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param("metro_customer_partner_id.partner_id_gen_method",
                          self.partner_id_gen_method)
        ICPSudo.set_param("metro_customer_partner_id.partner_id_random_digits",
                          self.partner_id_random_digits)
        ICPSudo.set_param("metro_customer_partner_id.partner_id_sequence",
                          self.partner_id_sequence)
