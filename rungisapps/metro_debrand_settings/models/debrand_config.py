# -*- coding: utf-8 -*-
import ast

from odoo import fields, models, api
from odoo.http import request


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    debrand_name = fields.Char(store=True, string='Display Name')
    background_color = fields.Char(store=True)
    text_color = fields.Char(sting='Text color', store=True)
    unsubscribe_auditlog = fields.Boolean(string='UnSubscribe Rules')
    delete_mail_server = fields.Boolean(string='Delete Mail Server')
    ir_cron = fields.Many2many('ir.cron', string='Schedule Action',
                               required=False)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        ir_crons = ICPSudo.get_param('metro_debrand.ir_cron')
        db_name = self.env.cr.dbname
        restore_date = request.env['ir.config_parameter'].sudo(). \
            search([('key', '=', 'database.create_date')]).value
        restore_date_slipt = restore_date.split(' ')
        date_restore = restore_date_slipt[0]
        base_url = request.httprequest.url_root
        display_string = ' You are currently WORKING in' + " " + base_url \
                         + " " + 'Database Name' + " " + db_name + " " \
                         + 'Restore Date' + " " + str(date_restore)
        res.update(
            background_color=get_param('metro_debrand.background_color'),
            text_color=get_param('metro_debrand.text_color'),
            unsubscribe_auditlog=get_param(
                'metro_debrand.unsubscribe_auditlog'),
            delete_mail_server=get_param('metro_debrand.delete_mail_server'),
            ir_cron=[(6, 0, ast.literal_eval(str(ir_crons)))],
            debrand_name=display_string,
        )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param("metro_debrand.debrand_name", self.debrand_name)
        ICPSudo.set_param("metro_debrand.background_color",
                          self.background_color)
        ICPSudo.set_param("metro_debrand.text_color", self.text_color)
        ICPSudo.set_param("metro_debrand.unsubscribe_auditlog",
                          self.unsubscribe_auditlog)
        ICPSudo.set_param("metro_debrand.delete_mail_server",
                          self.delete_mail_server)
        ICPSudo.set_param("metro_debrand.ir_cron", self.ir_cron.ids)

        # getting all Scheduled Action
        active_cron = self.env['ir.cron'].search([('active', '=', True)])
        for actives in active_cron:
            if str(actives.id) in ICPSudo.set_param("metro_debrand.ir_cron",
                                                    self.ir_cron.ids):
                actives.active = False
            else:
                actives.active = True

        # Delete all OutGoing mail servers
        if self.delete_mail_server:
            outgoing_mail = self.env['ir.mail_server'].search([('smtp_host',
                                                                '!=', None)])
            for mail in outgoing_mail:
                mail.unlink()

        # Unsubscribe all audit rule
        if self.unsubscribe_auditlog:
            if self.env['ir.module.module'].search(
                    [('name', '=', 'auditlog'), ('state', '=', 'installed')]):
                subscribe_auditlog = self.env['auditlog.rule'].search(
                    [('state', '=', 'subscribed')])
                for subscribe in subscribe_auditlog:
                    subscribe.write({'state': 'draft'})
