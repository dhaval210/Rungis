
from odoo import models, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_round, file_open
from lxml import etree
from io import BytesIO
from tempfile import NamedTemporaryFile
import mimetypes
import logging
logger = logging.getLogger(__name__)

try:
    from PyPDF2 import PdfFileWriter, PdfFileReader
    from PyPDF2.generic import NameObject
except ImportError:
    logger.debug('Cannot import PyPDF2')


class BaseUbl(models.AbstractModel):
    _inherit = 'base.ubl'
   
    @api.model
    def _ubl_add_item(
            self, name, product, parent_node, ns, type='purchase',
            seller=False, version='2.1'):
        """Beware that product may be False (in particular on invoices)"""
        assert type in ('sale', 'purchase'), 'Wrong type param'
        assert name, 'name is a required arg'
        item = etree.SubElement(parent_node, ns['cac'] + 'Item')
        product_name = False
        seller_code = False
        if product:
            if type == 'purchase':
                if seller:
                    sellers = product._select_seller(
                        partner_id=seller, quantity=0.0, date=None,
                        uom_id=False)
                    if sellers:
                        product_name = sellers[0].product_name
                        seller_code = sellers[0].product_code
            if not seller_code:
                seller_code = product.default_code
            if not product_name:
                variant = ", ".join(
                    [v.name for v in product.attribute_value_ids])
                product_name = variant and "%s (%s)" % (product.name, variant)\
                    or product.name
        description = etree.SubElement(item, ns['cbc'] + 'Description')
        description.text = name
        name_node = etree.SubElement(item, ns['cbc'] + 'Name')
        name_node.text = product_name or name.split('\n')[0]
        if product.attribute_line_ids:
            for attributes in product.attribute_line_ids:     
                if "Zertifizierung" in attributes.attribute_id.name:
                    if ":" in attributes.attribute_id.name :
                        certif_type = attributes.attribute_id.name.split(':')[1].strip().lower()
                    else:
                        certif_type = "unkown"    
                    certif = etree.SubElement(item, ns['cac'] + 'Certificates')
                    for attr in attributes.value_ids:
                        attribute_name = attr.name
                        attribute = etree.SubElement(certif, ns['cbc'] + 'Certificate' , type=certif_type,)
                        attribute.text = attribute_name
                    
        if seller_code:
            seller_identification = etree.SubElement(
                item, ns['cac'] + 'SellersItemIdentification')
            seller_identification_id = etree.SubElement(
                seller_identification, ns['cbc'] + 'ID')
            seller_identification_id.text = seller_code
        if product:
            if product.barcode:
                std_identification = etree.SubElement(
                    item, ns['cac'] + 'StandardItemIdentification')
                std_identification_id = etree.SubElement(
                    std_identification, ns['cbc'] + 'ID',
                    schemeAgencyID='6', schemeID='GTIN')
                std_identification_id.text = product.barcode
            # I'm not 100% sure, but it seems that ClassifiedTaxCategory
            # contains the taxes of the product without taking into
            # account the fiscal position
            # FIXME: Maybe tax for wrong company was found here which caused the message that taxes need ubl stuff set
            if type == 'sale':
                taxes = product.taxes_id
            else:
                taxes = product.supplier_taxes_id
            if taxes:
                for tax in taxes.filtered(
                        lambda t: t.company_id == self.env.user.company_id):
                    self._ubl_add_tax_category(
                        tax, item, ns, node_name='ClassifiedTaxCategory',
                        version=version)


            # Code added by Abhay for RUN 965, modified by Niklas
            self._ubl_add_product_attribute(product, item, ns)
            # Abhay Code ends here

            item_property = etree.SubElement(
                item, ns['cac'] + 'AdditionalItemProperty')
            for attribute_value in product.attribute_value_ids:
                property_name = etree.SubElement(
                    item_property, ns['cbc'] + 'Name')
                property_name.text = attribute_value.attribute_id.name
                property_value = etree.SubElement(
                    item_property, ns['cbc'] + 'Value')
                property_value.text = attribute_value.name
    
    @api.model
    def _ubl_add_product_attribute(self, product, parent_node, ns):
        product_attribute_xml =  etree.SubElement(parent_node, ns['cac'] + 'ProductAttributes')
        for attribute_line in product.attribute_line_ids:
            if attribute_line.print_on_invoice:
                product_attr = etree.SubElement(product_attribute_xml, ns["cac"] + "Attribute")
                attr_name = etree.SubElement(product_attr, ns["cbc"] + "Name")
                attr_name.text = attribute_line.attribute_id.name
                attr_val = etree.SubElement(product_attr, ns["cbc"] + "Value")
                attr_val.text = attribute_line.value_ids[0].name

            elif attribute_line.lot_extension and self._context and self._context.get('invoice_line'):
                invoice_line = self.env['account.invoice.line'].browse(self._context['invoice_line'])
                attribute_id = attribute_line.attribute_id

                if invoice_line.sale_line_ids.filtered(lambda x: x.product_id.id == product.id):
                    lot_product_id =  invoice_line.sale_line_ids.filtered(lambda x: x.product_id.id == product.id)

                    if lot_product_id and lot_product_id.lot_name and lot_product_id.lot_name.lot_attribute_line_ids:
                        lot_attribute_line_ids =  lot_product_id.lot_name.lot_attribute_line_ids.filtered(lambda x: x.attribute_id.id == attribute_id.id)
                        if lot_attribute_line_ids:
                            for lot_attribute_line_id in lot_attribute_line_ids:
                                product_attr = etree.SubElement(product_attribute_xml, ns["cac"] + "Attribute")
                                attr_name = etree.SubElement(product_attr, ns["cbc"] + "Name")
                                attr_name.text = lot_attribute_line_id.attribute_id.name
                                attr_val = etree.SubElement(product_attr, ns["cbc"] + "Value")
                                attr_val.text = lot_attribute_line_id.value_ids[0].name if lot_attribute_line_id.value_ids else "None"

    @api.model
    def _ubl_add_party(
            self, partner, company, node_name, parent_node, ns, version='2.1'):
        commercial_partner = partner.commercial_partner_id
        party = etree.SubElement(parent_node, ns['cac'] + node_name)
        if commercial_partner.website:
            website = etree.SubElement(party, ns['cbc'] + 'WebsiteURI')
            website.text = commercial_partner.website
        self._ubl_add_party_identification(
            commercial_partner, party, ns, version=version)
        
        party_identification = etree.SubElement(party, ns['cac'] + 'PartyIdentification')
        if commercial_partner.id_numbers.category_id.code =='gln_id_number':
            identification = etree.SubElement(party_identification, ns['cbc'] + 'ID', schemeID='GLN',
                    schemeAgencyID='9')
            identification.text = commercial_partner.id_numbers[0].name
       
        metro_bio_certificate = etree.SubElement(party, ns['cac'] + 'BioCertificate')
        if company and company.metro_bio_certificate:
            metro_bio_certificate.text = company.metro_bio_certificate

        party_name = etree.SubElement(party, ns['cac'] + 'PartyName')
        name = etree.SubElement(party_name, ns['cbc'] + 'Name')
        name.text = commercial_partner.name
        if partner.lang:
            self._ubl_add_language(partner.lang, party, ns, version=version)
        self._ubl_add_address(
            commercial_partner, 'PostalAddress', party, ns, version=version)
        self._ubl_add_party_tax_scheme(
            commercial_partner, party, ns, version=version)
        if company:
            self._ubl_add_party_legal_entity(
                commercial_partner, party, ns, version='2.1')
        self._ubl_add_contact(partner, party, ns, version=version)
        
    @api.model
    def _ubl_add_address(
            self, partner, node_name, parent_node, ns, version='2.1'):
        address = etree.SubElement(parent_node, ns['cac'] + node_name)
        if partner.street:
            streetname = etree.SubElement(
                address, ns['cbc'] + 'StreetName')
            streetname.text = partner.street
        if partner.street2:
            addstreetname = etree.SubElement(
                address, ns['cbc'] + 'AdditionalStreetName')
            addstreetname.text = partner.street2
        if hasattr(partner, 'street3') and partner.street3:
            blockname = etree.SubElement(
                address, ns['cbc'] + 'BlockName')
            blockname.text = partner.street3
        if partner.city:
            city = etree.SubElement(address, ns['cbc'] + 'CityName')
        city.text = partner.city
        if partner.zip:
            zip = etree.SubElement(address, ns['cbc'] + 'PostalZone')
            zip.text = partner.zip
        if partner.state_id:
            state = etree.SubElement(
                address, ns['cbc'] + 'CountrySubentity')
            state.text = partner.state_id.name
            state_code = etree.SubElement(
                address, ns['cbc'] + 'CountrySubentityCode')
            state_code.text = partner.state_id.code
        if partner.country_id:
            self._ubl_add_country(
                partner.country_id, address, ns, version=version)
        else:
            logger.warning('UBL: missing country on partner %s', partner.name)
    