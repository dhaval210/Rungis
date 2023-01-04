import logging

from re import search as re_search
from datetime import datetime, timedelta

from odoo import _
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping


class SaleOrderLineImportMapper(Component):
    
    _name = 'db2.sale.order.line.mapper'
    _inherit = 'db2.import.mapper'
    _apply_on = 'db2.sale.order.line'

    direct = []

    def get_external(self, record):
        return str(record['OAUAUFN'].strip()) + '-' + str(record['OAUAUPO'].strip())

    @mapping
    def product_uom_qty(self, record):
        return {'product_uom_qty': float(record['OAUMGZTL'])}

    @mapping
    def demand_qty(self, record):
        return {'demand_qty': float(record['OAUMGBST'])}

    @mapping
    def price_unit(self, record):
        return {'price_unit': float(record['OAUPREIS'])}

    @mapping
    def so_pos_no(self, record):
        return {'so_pos_no': str(record['OAUAUPO'].strip())}

    @mapping
    def special_wishes(self, record):
        if len(record['OAUSOWU'].strip()) > 0:
            special_wish = record['OAUSOWU'].strip()
        else:
            special_wish = False
        return {'special_wishes': special_wish}

    @mapping
    def external_id(self, record):
        return {'external_id': self.get_external(record)}

    @mapping
    def company_id(self, record):
        company_id = self.backend_record.default_company_id.id
        if self.backend_record.split_companies is True:
            company_mapping = {
                'REA': 4, # Rungis AT
            }
            if record['OAUKGRP'] in company_mapping:
                company_id = company_mapping[record['OAUKGRP']]
        return {'company_id': company_id}

    @mapping
    def discount_amount(self, record):
        discount = 0
        result = {'discount': discount}
        return result

    @mapping
    def product_id(self, record):
        data = {}
        product = self.env['product.product'].search([
            ('default_code', '=', record['OAUARTN'].strip())
        ], limit=1)
        if product and product.id is not False:
            data = {
                'product_id': product.id
            }
            if product.catch_weight_ok is True:
                data.update({
                    'product_cw_uom': product.cw_uom_id.id,
                    'product_cw_uom_qty': product.average_cw_quantity * float(record['OAUMGZTL']),
                })
        else:
            msg = 'product not found: ' + record['OAUARTN'].strip()
            raise Exception(msg)
        return data

    @mapping
    def id(self, record):
        line = self.model.search([
            ('external_id', '=', self.get_external(record)),
        ])        
        if line and line.id is not False:
            return {'id': line.id}
        return {}
