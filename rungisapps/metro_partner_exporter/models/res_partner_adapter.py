from odoo.addons.component.core import Component
import logging

_logger = logging.getLogger(__name__)


class ResPartnerAdapter(Component):
    _name = 'csv.res.partner.adapter'
    _inherit = 'csv.adapter'
    _apply_on = ['res.partner']
    _file_name = 'sap_partner_export'
    _file_header = ['COMPANY REF', 'REF', 'NAME',  'TYPE', 'TITLE','INDUSTRY NAME' 'ACTIVE', 'VAT', 'CURRENCY', 'PURCHASE CURRENCY',
                    'PAYMENT TERM', 'VENDOR PAYMENT TERM', 'DUE INVOICES REMINDER', 'CREDIT LIMIT', 'LANGUAGE', 'STREET',
                    'HOUSE NUMBER', 'ZIP', 'CITY', 'COUNTRY', 'STATE', 'MOBILE', 'FAX', 'EMAIL', 'WEBSITE', 'BANK BIC',
                    'BANK ACC NUMBER', 'IBAN', 'NOTE']
