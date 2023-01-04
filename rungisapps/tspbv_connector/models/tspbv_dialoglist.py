from odoo import api, fields, models
from odoo.exceptions import ValidationError
import logging
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
_logger = logging.getLogger(__name__)


class DialogList(models.Model):
    _name = 'tspbv.dialoglist'
    _description = 'Dialoglist'

    model_id = fields.Many2one('ir.model', string='Model')
    name = fields.Char(string='Template Name')
    default_code = fields.Char(string='Template Code')
    start = fields.Char(string='Start')
    dialog_ids = fields.One2many(
        comodel_name='tspbv.dialog',
        inverse_name='dialoglist_id',
        string='Dialog'
    )

    _sql_constraints = [('default_code_unique', 'unique(default_code)',
                        'There can only be one code for an dialoglist template')]

    def convert_to_html(self, text_to_convert, model_name, id):
        """
        this function use the render_template of mail.template replacing template with an html field
        :return:
        """
        Template = self.env['tspbv.template']
        record = self.env[model_name].search([('id', '=', id)], limit=1)
        if not record:
            raise ValidationError('No record matching ID: '+str(id)+' exists for Model '+ model_name)
        text_record = Template._render_template(text_to_convert, model_name, id)
        return text_record

    @api.multi
    def generate_dialoglist_xml(self, record_id):
        for record in self:
            xml = self.env['xml.generator'].generate_xml_doc(record)
            rough_string = ET.tostring(xml, 'utf-8')
            reparsed = minidom.parseString(rough_string)
            xml = reparsed.toprettyxml(indent="\t")
            if record_id and self.model_id:
                formatted_xml = self.convert_to_html(xml,record.model_id.model,int(record_id))
                return formatted_xml
            else:
                return xml