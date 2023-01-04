# -*- coding: utf-8 -*-

from . import models

from odoo import api, SUPERUSER_ID

# if CDN is enable it will disable here
def _init(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    website_module = env['ir.module.module'].search([('name','=','website'),('state','=','installed')])
    if website_module:
        cdn_activated_search = env['res.config.settings'].search([('cdn_activated','=',True)])
        if cdn_activated_search:
            for cdn in cdn_activated_search:
                cdn.cdn_activated = False




