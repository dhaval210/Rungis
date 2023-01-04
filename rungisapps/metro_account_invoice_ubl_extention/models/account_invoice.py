# Copyright 2016-2017 Akretion (http://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from lxml import etree
import logging

from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_round
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _name = 'account.invoice'
    _inherit = ['account.invoice', 'base.ubl']

    xml_ubl = fields.Binary('UBL File')
    
    @api.multi
    def _ubl_add_header(self, parent_node, ns, version='2.1'):
        doc_id = etree.SubElement(parent_node, ns['cbc'] + 'ID')
        doc_id.text = self.number
        issue_date = etree.SubElement(parent_node, ns['cbc'] + 'IssueDate')
        issue_date.text = self.date_invoice.strftime('%Y-%m-%d')
        type_code = etree.SubElement(
            parent_node, ns['cbc'] + 'InvoiceTypeCode')
        if self.type == 'out_invoice':
            type_code.text = '380'
        elif self.type == 'out_refund':
            type_code.text = '381'
        if self.comment:
            note = etree.SubElement(parent_node, ns['cbc'] + 'Note')
            note.text = self.comment
        doc_currency = etree.SubElement(
            parent_node, ns['cbc'] + 'DocumentCurrencyCode')
        doc_currency.text = self.currency_id.name
    
    @api.multi
    def generate_invoice_ubl_xml_etree_extention(self,search_invoice=False, version='2.1'):
        nsmap, ns = self._ubl_get_nsmap_namespace('Invoice-2', version=version)
        xml_root = etree.Element('Invoice', nsmap=nsmap)
        ubl_version = etree.SubElement(
            xml_root, ns['cbc'] + 'UBLVersionID')
        ubl_version.text = version
        
        for invoice in search_invoice:
            inv_root = etree.SubElement(
            xml_root, ns['cac'] + 'Invoice')
            invoice._ubl_add_header(inv_root, ns, version=version)
            invoice._ubl_add_order_reference(inv_root, ns, version=version)
            invoice._ubl_add_contract_document_reference(
                xml_root, ns, version=version)
            invoice._ubl_add_attachments(inv_root, ns, version=version)
            invoice._ubl_add_supplier_party(
                False, invoice.company_id, 'AccountingSupplierParty', inv_root, ns,
                version=version)
            invoice._ubl_add_customer_party(
                invoice.partner_id, False, 'AccountingCustomerParty', inv_root, ns,
                version=version)
            # the field 'partner_shipping_id' is defined in the 'sale' module
            if hasattr(invoice, 'partner_shipping_id') and invoice.partner_shipping_id:
                invoice._ubl_add_delivery(invoice.partner_shipping_id, inv_root, ns)
            # Put paymentmeans block even when invoice is paid ?
            payment_identifier = invoice.get_payment_identifier()
            invoice._ubl_add_payment_means(
                invoice.partner_bank_id, invoice.payment_mode_id, invoice.date_due,
                inv_root, ns, payment_identifier=payment_identifier,
                version=version)
            if invoice.payment_term_id:
                invoice._ubl_add_payment_terms(
                    invoice.payment_term_id, inv_root, ns, version=version)
            invoice._ubl_add_tax_total(inv_root, ns, version=version)
            # invoice._ubl_add_global_discounts(inv_root, ns, version=version)
            invoice._ubl_add_legal_monetary_total(inv_root, ns, version=version)
    
            line_number = 0
            for iline in invoice.invoice_line_ids:
                line_number += 1
                invoice._ubl_add_invoice_line(
                    inv_root, iline, line_number, ns, version=version)
        return xml_root
    
    @api.multi
    def _ubl_add_global_discounts(self, parent_node, ns, version='2.1'):
        cur_name = self.currency_id.name
        prec = self.currency_id.decimal_places
        global_discount_node = etree.SubElement(parent_node, ns['cac'] + 'GlobalDiscounts')
        if self.invoice_global_discount_ids:
            for discount in self.invoice_global_discount_ids:
                global_discount = etree.SubElement(global_discount_node, ns['cac'] + 'Discount')
            # for disc_id in self.invoice_global_discount_ids:
                dicsount_name = etree.SubElement(global_discount, ns['cbc'] + 'Name')
                dicsount_name.text = discount.name
                
                base_price = etree.SubElement(global_discount, ns['cbc'] + 'BasePriceAmount',currencyID=cur_name)
                base_price.text = '%0.*f' % (prec, discount.base)
                # base_price.text = '%0.*f' % (prec,self.amount_untaxed_before_global_discounts)
                
                discount_price = etree.SubElement(global_discount, ns['cbc'] + 'DiscountPriceAmount',currencyID=cur_name)
                discount_price.text = '%0.*f' % (prec, discount.discount_amount)
                # discount_price.text = '%0.*f' % (prec,self.amount_global_discount)

                tax_amount = 100.0
                for tax in discount.tax_ids:
                    tax_amount = tax.amount
                discounted_tax = etree.SubElement(global_discount, ns['cbc'] + 'VATDiscount',currencyID=cur_name)
                discounted_tax.text = '%0.*f' % (prec, discount.discount_amount * (tax_amount / 100))
                
                price_amount = etree.SubElement(global_discount, ns['cbc'] + 'PriceAmount',currencyID=cur_name)
                price_amount.text = '%0.*f' % (prec, discount.base_discounted)
                
                # for disc_id in self.invoice_global_discount_ids:
                percent = etree.SubElement(global_discount, ns['cbc'] + 'DiscountPercent')
                percent.text = '%0.*f' % (prec, discount.discount)

                taxes = etree.SubElement(global_discount, ns["cbc"] + "Tax")
                taxes.text = ", ".join([tax.name for tax in discount.tax_ids])

    @api.multi
    def generates_ubl_xml_string(self, version='2.1'):
        #self.ensure_one()
        # assert self.state in ('open', 'paid')
        # assert self.type in ('out_invoice', 'out_refund')
        logger.debug('Starting to generate UBL XML Invoice file')
        lang = self.get_ubl_lang()
        # The aim of injecting lang in context
        # is to have the content of the XML in the partner's lang
        # but the problem is that the error messages will also be in
        # that lang. But the error messages should almost never
        # happen except the first days of use, so it's probably
        # not worth the additional code to handle the 2 langs
        nsmap, ns = self._ubl_get_nsmap_namespace('Invoice-2', version=version)
        # xml_roots = etree.Element('Invoice', nsmap=nsmap)
        inv_obj = self.env['account.invoice']
        context = dict(self._context or {})
        xml_root = self.with_context(lang=lang).\
            generate_invoice_ubl_xml_etree_extention(search_invoice = inv_obj.browse(context.get('active_ids')),version=version)
        xml_string = etree.tostring(
            xml_root, pretty_print=True, encoding='UTF-8',
            xml_declaration=True)
        #self._ubl_check_xml_schema(xml_string, 'Invoice', version=version)
        logger.debug(
            'Invoice UBL XML file generated for account invoice ID ')
            #'(state %s)', self.id, self.state)
        logger.debug(xml_string.decode('utf-8'))
        return xml_string

    @api.multi
    def get_ubl_filename(self, version="2.1"):
        """This method is designed to be inherited"""
        if len(self) > 1:
            # return "UBL-Invoice-%s.xml" %  datetime.now().strftime("%Y%m%d")
            return 'UBL-Invoice-%s.xml' % version
        if self.number:
            return self._get_custom_ubl_filename()
        return 'UBL-Invoice-%s.xml' % version

    @api.multi
    def get_ubl_version(self):
        version = self._context.get('ubl_version') or '2.1'
        return version

    @api.multi
    def get_ubl_lang(self):
        # Currently this is a workaround and there is probably a better solution
        # FIXME: Might need better method to determine language for file, if multiple partners have different languages only one of them will be used
        for inv in self:
            return inv.partner_id.lang or 'en_US'

    @api.multi
    def embed_ubl_xml_in_pdf(self, pdf_content=None, pdf_file=None):
        self.ensure_one()
        if (
                self.type in ('out_invoice', 'out_refund') and
                self.state in ('open', 'paid')):
            version = self.get_ubl_version()
            ubl_filename = self.get_ubl_filename(version=version)
            xml_string = self.generates_ubl_xml_string(version=version)
            pdf_content = self.embed_xml_in_pdf(
                xml_string, ubl_filename,
                pdf_content=pdf_content, pdf_file=pdf_file)
        return pdf_content

    @api.multi
    def generates_ubl_xml_file_button(self):
        # self.ensure_one()
        # assert self.type in ('out_invoice', 'out_refund')
        # assert self.state in ('open', 'paid')
        version = self.get_ubl_version()
        xml_string = self.generates_ubl_xml_string(version=version)
        filename = self.get_ubl_filename(version=version)
        ctx = {}
        attach = self.env['ir.attachment'].with_context(ctx).create({
            'name': filename,
            'res_id': self.id,
            'res_model': str(self._name),
            'datas': base64.b64encode(xml_string),
            'datas_fname': filename,
            'type': 'binary',
            })
        # get base url
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        # prepare download url
        download_url = '/web/content/' + str(attach.id) + '?download=true'
        # download
        return {
                "type": "ir.actions.act_url",
                "url": str(base_url) + str(download_url),
                "target": "new",
        }
        # action = self.env['ir.actions.act_window'].for_xml_id(
        #      'base', 'action_attachment')
        # action.update({
        #      'res_id': attach.id,
        #      'views': False,
        #      'view_mode': 'form,tree'
        #      })
        # return action
    
        
    @api.multi
    def _ubl_add_order_reference(self, parent_node, ns, version='2.1'):
        self.ensure_one()
        order_ref = etree.SubElement(
            parent_node, ns['cac'] + 'OrderReferences')
        order_ref_name = etree.SubElement(
            order_ref, ns['cac'] + 'OrderNames')
        delivery_ref = etree.SubElement(
            order_ref, ns['cac'] + 'DeliveryReferences')

        # If no origin is given, no references to an order can be done
        if not self.origin:
            return

        for so_name in self.origin.split(" "):
            sale_id = self.env['sale.order'].search([
                ('name','=',so_name),
                ('company_id', '=', self.company_id.id),
            ])
                
            client_order_ref = sale_id.client_order_ref
                
            order = etree.SubElement(order_ref_name, ns["cac"] + "Order")
            order_name = etree.SubElement(
                order, ns['cbc'] + 'Name')
            order_name.text = so_name
            order_date = etree.SubElement(
                order, ns["cbc"] + "Date"
            )
            if sale_id.confirmation_date:
                order_date.text = sale_id.confirmation_date.strftime('%Y-%m-%d')
            if client_order_ref: 
                order_ref_custom = etree.SubElement(
                    order_ref, ns['cac'] + 'CustomerReferences')
                client_order = etree.SubElement(
                        order_ref_custom, ns['cbc'] + 'Reference')
                client_order.text = client_order_ref
            
            if sale_id.company_id.ubl_use_softm_delivery_note:
                delivery_notes = {line.delivery_no for line in sale_id.order_line if line.delivery_no}
                for delivery_no in delivery_notes:
                    delivery_order = etree.SubElement(
                        delivery_ref, ns['cac'] + 'DeliveryOrder')
                    delivery_name = etree.SubElement(
                                delivery_order, ns['cbc'] + 'Name')
                    delivery_date = etree.SubElement(
                                delivery_order, ns['cbc'] + 'Date')
                    delivery_name.text = delivery_no
                    if sale_id.commitment_date:
                        delivery_date.text = sale_id.commitment_date.strftime('%Y-%m-%d')
            else:
                for picking in sale_id.picking_ids.filtered(lambda x: x.state == 'done' and x.location_dest_id.usage == 'customer'):
                    delivery_order = etree.SubElement(
                        delivery_ref, ns['cac'] + 'DeliveryOrder')
                    delivery_name = etree.SubElement(
                                delivery_order, ns['cbc'] + 'Name')
                    delivery_date = etree.SubElement(
                                delivery_order, ns['cbc'] + 'Date')
                    picking_name = picking.name
                    date = picking.scheduled_date
                    
                    delivery_name.text = picking_name
                    delivery_date.text = date.strftime('%Y-%m-%d')

    @api.multi
    def _ubl_add_tax_total(self, xml_root, ns, version='2.1'):
        self.ensure_one()
        cur_name = self.currency_id.name
        tax_total_node = etree.SubElement(xml_root, ns['cac'] + 'TaxTotal')
        tax_amount_node = etree.SubElement(
            tax_total_node, ns['cbc'] + 'TaxAmount', currencyID=cur_name)
        prec = self.currency_id.decimal_places
        tax_amount_node.text = '%0.*f' % (prec, self.amount_tax)
        for tline in self.tax_line_ids:
            # Set undiscounted base price
            base_price = tline.base
            # If global discounts are given search for a tax which matches the name
            # and the undiscounted base price of the global discount record, if found replace base price with discounted price
            if len(self.invoice_global_discount_ids) > 0:
                for disc in self.invoice_global_discount_ids:
                    if tline.name in disc.tax_ids.name and tline.base == disc.base:
                        base_price = disc.base_discounted
                        break
            self._ubl_add_tax_subtotal(
                base_price, tline.amount, tline.tax_id, cur_name,
                tax_total_node, ns, version=version)
        self._ubl_add_global_discounts(xml_root, ns, version=version)

    @api.multi
    def _ubl_add_invoice_line(
            self, parent_node, iline, line_number, ns, version='2.1'):
        cur_name = self.currency_id.name
        line_root = etree.SubElement(
            parent_node, ns['cac'] + 'InvoiceLine')
        dpo = self.env['decimal.precision']
        qty_precision = dpo.precision_get('Product Unit of Measure')
        price_precision = dpo.precision_get('Product Price')
        account_precision = self.currency_id.decimal_places
        line_id = etree.SubElement(line_root, ns['cbc'] + 'ID')
        line_id.text = str(line_number)
        
        order_ref = etree.SubElement(line_root, ns['cbc'] + 'OrderRef')

        sale_id = None
        # Check if invoice line has an origin
        if iline.origin:
            order_ref.text = iline.origin
            sale_id = self.env['sale.order'].search([
                ('name','=',iline.origin),
                ("company_id", "=", iline.company_id.id),
            ])

            if sale_id:
                so_order_date = etree.SubElement(line_root, ns['cbc'] + 'OrderDate')
                so_order_date.text = sale_id.confirmation_date.strftime('%Y-%m-%d')

            orderpos = etree.SubElement(line_root, ns["cbc"] + "OrderPosition")
            if iline.so_pos_no:
                orderpos.text = str(iline.so_pos_no)
        # References to Deliveries can only be added if a reference to an order is given
        if sale_id:
            if sale_id.company_id.ubl_use_softm_delivery_note:
                delivery_ref = etree.SubElement(line_root, ns["cbc"] + "DeliveryRef")
                delivery_ref.text = iline.delivery_no
            else:
                for picking in sale_id.picking_ids.filtered(lambda x: x.state == 'done' and x.location_dest_id.usage == 'customer'):
                    picking_name = picking.name
                    delivery_ref = etree.SubElement(line_root, ns['cbc'] + 'DeliveryRef')
                    delivery_ref.text = picking_name

            so_delivery_date = etree.SubElement(line_root, ns['cbc'] + 'DeliveryDate')
            if sale_id.commitment_date:
                so_delivery_date.text = sale_id.commitment_date.strftime('%Y-%m-%d')
            elif  sale_id.effective_date:
                so_delivery_date.text = sale_id.effective_date.strftime('%Y-%m-%d')
        
        uom_unece_code = False
        # uom_id is not a required field on account.invoice.line
        if iline.uom_id and iline.uom_id.unece_code:
            uom_unece_code = iline.uom_id.unece_code
        if uom_unece_code:
            quantity = etree.SubElement(
                line_root, ns['cbc'] + 'InvoicedQuantity',
                unitCode=uom_unece_code)
        else:
            quantity = etree.SubElement(
                line_root, ns['cbc'] + 'InvoicedQuantity')
        qty = 0
        if iline.product_id._is_cw_product():
            qty = iline.product_cw_uom_qty
        else:
            qty = iline.quantity
        quantity.text = '%0.*f' % (qty_precision, qty)
       
        if iline.uom_id.uom_type == 'bigger' or iline.uom_id.uom_type == 'smaller':
            base_unit_node = etree.SubElement(line_root, ns['cac'] + 'BaseUnit')
            source_unit_node = etree.SubElement(base_unit_node, ns["cac"] + "SourceUnit")
            source_unit = None
            # If product is catch weight product, use CW-UOM as source unit
            if iline.product_id._is_cw_product():
                source_unit = self.env["uom.uom"].search([
                    ('uom_type', '=', 'reference'),
                    ('category_id', '=', iline.product_cw_uom.category_id.id)
                ])
            else:
                source_unit = self.env["uom.uom"].search([
                    ('uom_type', '=', 'reference'),
                    ('category_id', '=', iline.uom_id.category_id.id)
                ])

            source_unit_node.text = source_unit.name

            ratio = etree.SubElement(base_unit_node, ns['cbc'] + 'Ratio')
            rat = 1.0
            # If product is catch weight product use average catch_weight quantity as ratio
            if iline.product_id._is_cw_product():
                uom = iline.product_id.cw_uom_id
                if uom.uom_type != "reference":
                    # Ratio is average_cw_quantity
                    if uom.uom_type == "smaller":
                        rat = uom.factor
                    else:
                        rat = uom.factor_inv
            else:
                if iline.uom_id.uom_type == "smaller":
                    rat = iline.uom_id.factor
                else:
                    rat = iline.uom_id.factor_inv

            ratio.text = '%0.*f' % (6, rat)

            destunit_node = etree.SubElement(base_unit_node, ns["cac"] + "DestUnit")
            if iline.product_id._is_cw_product():
                destunit_node.text = iline.product_cw_uom.name
            else:
                destunit_node.text = iline.uom_id.name
        
        line_amount = etree.SubElement(
            line_root, ns['cbc'] + 'LineExtensionAmount',
            currencyID=cur_name)
        line_amount.text = '%0.*f' % (account_precision, iline.price_subtotal)
        self._ubl_add_invoice_line_tax_total(
            iline, line_root, ns, version=version)

        ctx = {'invoice_line': iline.id}
        self.with_context(ctx)._ubl_add_item(
            iline.name, iline.product_id, line_root, ns, type='sale',
            version=version)
        price_node = etree.SubElement(line_root, ns['cac'] + 'Price')
        price_amount = etree.SubElement(
            price_node, ns['cbc'] + 'PriceAmount', currencyID=cur_name)
        price_unit = 0.0
        # Use price_subtotal/qty to compute price_unit to be sure
        # to get a *tax_excluded* price unit
        if not float_is_zero(qty, precision_digits=qty_precision):
            price_unit = float_round(
                iline.price_subtotal / float(qty),
                precision_digits=price_precision)
        price_amount.text = '%0.*f' % (price_precision, price_unit)
        if uom_unece_code:
            base_qty = etree.SubElement(
                price_node, ns['cbc'] + 'BaseQuantity',
                unitCode=uom_unece_code)
        else:
            base_qty = etree.SubElement(price_node, ns['cbc'] + 'BaseQuantity')
        base_qty.text = '%0.*f' % (qty_precision, qty)
    
    def _ubl_add_invoice_line_tax_total(self, iline, parent_node, ns, version='2.1'):
        cur_name = self.currency_id.name
        prec = self.currency_id.decimal_places
        tax_total_node = etree.SubElement(parent_node, ns['cac'] + 'TaxTotal')
        price = iline.price_unit * (1 - (iline.discount or 0.0) / 100.0)
        quantity = 0
        if iline.product_id._is_cw_product():
            quantity = iline.product_cw_uom_qty
        else:
            quantity = iline.quantity
        res_taxes = iline.invoice_line_tax_ids.compute_all(
            price, quantity=quantity, product=iline.product_id,
            partner=self.partner_id)
        tax_total = float_round(
            res_taxes['total_included'] - res_taxes['total_excluded'],
            precision_digits=prec)
        tax_amount_node = etree.SubElement(
            tax_total_node, ns['cbc'] + 'TaxAmount', currencyID=cur_name)
        tax_amount_node.text = '%0.*f' % (prec, tax_total)
        for res_tax in res_taxes['taxes']:
            tax = self.env['account.tax'].browse(res_tax['id'])
            # we don't have the base amount in res_tax :-(
            self._ubl_add_tax_subtotal(
                False, res_tax['amount'], tax, cur_name, tax_total_node,
                ns, version=version)
        
    @api.multi
    def generate_ubl_xml_string(self, version='2.1'):
        self.ensure_one()
        assert self.state in ('open', 'paid')
        assert self.type in ('out_invoice', 'out_refund')
        logger.debug('Starting to generate UBL XML Invoice file')
        lang = self.get_ubl_lang()
        # The aim of injecting lang in context
        # is to have the content of the XML in the partner's lang
        # but the problem is that the error messages will also be in
        # that lang. But the error messages should almost never
        # happen except the first days of use, so it's probably
        # not worth the additional code to handle the 2 langs
        xml_root = self.with_context(lang=lang).\
            generate_invoice_ubl_xml_etree(version=version)
        xml_string = etree.tostring(
            xml_root, pretty_print=True, encoding='UTF-8',
            xml_declaration=True)
        # self._ubl_check_xml_schema(xml_string, 'Invoice', version=version)
        logger.debug(
            'Invoice UBL XML file generated for account invoice ID %d '
            '(state %s)', self.id, self.state)
        logger.debug(xml_string.decode('utf-8'))
        return xml_string
        
    # Function for custom filenames, use get_ubl_file as fallback function
    @api.multi
    def _get_custom_ubl_filename(self):
        return self.number+".xml"

    # Overwrite filename when clicking on "Generate UBL XML File" button
    @api.multi
    def attach_ubl_xml_file_button(self):
        self.ensure_one()
        # Get attachment
        res = super(AccountInvoice, self).attach_ubl_xml_file_button()
        # Get filename
        filename = self.get_ubl_filename()
        # Overwrite filename of attachment 
        attach = self.env["ir.attachment"].browse([res["res_id"]])
        attach.write({
            "name": filename,
            "datas_fname": filename,
        })
        return res

