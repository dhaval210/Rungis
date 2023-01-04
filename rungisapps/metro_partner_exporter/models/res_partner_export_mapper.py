from odoo.addons.component.core import Component
import logging
_logger = logging.getLogger(__name__)
from odoo.addons.connector.components.mapper import mapping


class ResPartnerExportMapper(Component):
    _name = 'csv.res.partner.export.mapper'
    _inherit = 'csv.export.mapper'
    _apply_on = ['res.partner']
    _usage = 'export.mapper'


    @mapping
    def mappings(self, record):
        iban = ''
        acc_number = ''
        bic = ''
        if record.bank_ids :
            if record.bank_ids[0].acc_type == 'iban':
                iban = record.bank_ids and record.bank_ids[0].acc_number
            else:
                acc_number = record.bank_ids and record.bank_ids[0].acc_number
            bic = record.bank_ids[0].bank_id and record.bank_ids[0].bank_id.bic or ''
        return {'COMPANY': record.parent_id.name or '',
                'REF': record.ref or '',
                'NAME': record.name or '',
                'VAT': record.vat or '',
                'CURRENCY': record.currency_id.name or '',
                'PURCHASE CURRENCY': record.property_purchase_currency_id.name or '',
                'PAYMENT TERM': record.property_payment_term_id.name or '',
                'VENDOR PAYMENT TERM': record.property_supplier_payment_term_id.name or '',
                'DUE INVOICES REMINDER': record.due_invoices_reminder,
                'NOTE': record.comment or '',
                'CREDIT LIMIT': record.credit_limit or '',
                'LANGUAGE': record.lang or '',
                'STREET': record.street or '',
                'STREET2': record.street2 or '',
                'HOUSE NUMBER': record.street_number or '',
                'ZIP': record.zip or '',
                'CITY': record.city or '',
                'STATE': record.state_id.code or '',
                'COUNTRY': record.country_id.code or '',
                'MOBILE': record.mobile or '',
                'EMAIL': record.email or '',
                'WEBSITE': record.website or '',
                'TITLE': record.title and record.title.name or '',
                'TYPE': record.company_type or '',
                'BANK BIC': bic,
                'BANK ACC NUMBER': acc_number,
                'IBAN': iban,
                'ACTIVE': record.active,
              }


