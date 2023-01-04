from odoo import api, fields, models
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import logging
_logger = logging.getLogger(__name__)


class Workflow(models.Model):
    _name = 'tspbv.workflow'
    _description = 'Workflow'


    name = fields.Char('Name')
    dialoglist_ids = fields.Many2many('tspbv.dialoglist', 'workflow_dialoglist_rel', 'workflow_id', 'dialoglist_id', 'Dialog Lists',
                                         help="Dialog List included in the workflow")
    grammar_rule_ids = fields.One2many('tspbv.grammar.rule',compute='_get_grammar_rules')
    js_script_ids = fields.Many2many('tspbv.script', 'workflow_script_rel', 'workflow_id', 'script_id','Related Scripts')
    script_code = fields.Text(compute='get_script_code',string='Script Code')
    first_dialog_id = fields.Many2one('tspbv.dialoglist','First Dialog List')



    @api.multi
    def get_script_code(self):
        for record in self:
            if record.js_script_ids:
                code = ''
                for script in record.js_script_ids:
                    code += script.code
                record.script_code = code


    @api.multi
    def _get_grammar_rules(self):
        for record in self:
            grammar_rule_ids = []
            for dialoglist in record.dialoglist_ids:
                for dialog in dialoglist.dialog_ids:
                    grammar_rule_ids += dialog.lydia_input_id.grammar_rule_ids.ids
            record.grammar_rule_ids = [(6, 0, grammar_rule_ids)]


    @api.multi
    def generate_init_xml(self, record_id):
        for record in self:
            init_xml = self.env['xml.generator'].generate_init_doc(record)
            if record.first_dialog_id:
                first_dialog = record.first_dialog_id
                dialog_xml = self.env['xml.generator'].generate_xml_doc(first_dialog, no_header=True)
                init_xml.append(dialog_xml)
            rough_string = ET.tostring(init_xml, 'utf-8')
            reparsed = minidom.parseString(rough_string)
            xml = reparsed.toprettyxml(indent="\t")
            if record_id and record.first_dialog_id.model_id:
                formatted_xml = self.first_dialog_id.convert_to_html(xml, record.first_dialog_id.model_id.model, int(record_id))
                return formatted_xml
            return xml
