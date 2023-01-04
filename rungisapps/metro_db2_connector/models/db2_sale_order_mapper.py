import logging

from re import search as re_search
from datetime import datetime, timedelta

from odoo import _
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.queue_job.exception import FailedJobError
from ..components.mapper import normalize_datetime


class SaleOrderImportMapper(Component):
    
    _name = 'db2.sale.order.mapper'
    _inherit = 'db2.import.mapper'
    _apply_on = 'db2.sale.order'

    direct = [
        ('OAUAUFN', 'external_id'),
        ('OAUAUFN', 'db2_order_id'),
        ('OAUAUFN', 'client_order_ref'),
        ('OAUALP', 'run_up_point'),
        (normalize_datetime('OAUDTLT'), 'commitment_date'),
    ]

    children = [
        ('child', 'db2_order_line_ids', 'db2.sale.order.line'),
    ]

    def finalize(self, map_record, values):
        values.setdefault('order_line', [])
        values.update({
            'partner_shipping_id': values[ 'partner_id'],
        })
        partner = self.env['res.partner'].browse(values['partner_id'])
        if partner and partner.property_payment_term_id:
            values.update({
                'payment_term_id': partner.property_payment_term_id.id,
            })        
        if partner and partner.customer_global_discount_ids and len(partner.customer_global_discount_ids.ids):
            values.update({
                'global_discount_ids': [[6, 0, partner.customer_global_discount_ids.ids]],
            })          
        return values


    @mapping
    def name(self, record):
        return {'name': 'SO' + record['OAUAUFN']}


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
    def partner_id(self, record):
        partner_id = 1
        partner = self.env['res.partner'].search(
            [
                ('ref', '=', record['OAUKDNR'].strip()),
                ('customer', '=', True),
            ], limit=1
        )
        if partner and partner.id is not False:
            partner_id = partner.id
        else:
            msg = 'partner not found: ' + record['OAUKDNR'].strip()
            raise Exception(msg)
        return {'partner_id': partner_id}

    @mapping
    def partner_invoice_id(self, record):
        partner_invoice_id = 1
        partner = self.env['res.partner'].search(
            [
                ('ref', '=', record['OAUKDRG'].strip()),
                ('customer', '=', True),
            ], limit=1
        )
        if partner and partner.id is not False:
            partner_invoice_id = partner.id
        else:
            msg = 'invoice partner not found: ' + record['OAUKDRG'].strip()
            raise Exception(msg)
        return {'partner_invoice_id': partner_invoice_id}

    @mapping
    def sales_team(self, record):
        team = self.options.team_id
        if team:
            return {'team_id': team.id}

    @mapping
    def analytic_account_id(self, record):
        analytic_account_id = self.options.account_analytic_id
        if analytic_account_id:
            return {'analytic_account_id': analytic_account_id.id}

    @mapping
    def fiscal_position(self, record):
        fiscal_position = self.options.fiscal_position_id
        if fiscal_position:
            return {'fiscal_position_id': fiscal_position.id}

    @mapping
    def warehouse_id(self, record):
        warehouse = self.backend_record.default_warehouse_id.id
        if warehouse:
            return {'warehouse_id': warehouse}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def tour_id(self, record):
        tour_id = False
        tour = self.env['transporter.route'].search(
            [
                ('name', '=', record['OAUTRNR'].strip()),
            ], limit=1
        )
        if tour and tour.id is not False:
            tour_id = tour.id
        else:
            msg = 'tour not found: ' + record['OAUTRNR'].strip()
            raise Exception(msg)                     
        return {'tour_id': tour_id}

    @mapping
    def user_id(self, record):
        user_id = False
        user = self.env['res.users'].search(
            [
                ('login', '=', record['OAUEMVK'].strip()),
            ], limit=1
        )
        if user and user.id is not False:
            user_id = user.id
        return {'user_id': user_id}
