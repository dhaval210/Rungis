from odoo import api, fields, models
import xml.etree as etree
import xml.etree.ElementTree as ET
import logging

_logger = logging.getLogger(__name__)

attribute_map = {'dialog': 'dialog_ids', 'output': 'lydia_output_id', 'input': 'lydia_input_id',
                 'message': 'lydia_output',
                 'copilot': 'lydia_copilot', 'grammarrules': 'grammar_rules',
                 'recognition': 'lydia_recognition_ids', 'scan': 'lydia_scan_ids', 'links': 'lydia_link_ids',
                 'id': 'id_dialog', 'onMatch': 'on_match', 'grammars': 'grammar_rule_ids',
                 'constraint': 'constraint_id', 'name': 'rule_name', 'script': 'script_code'}

dict_order = {'dialog': ['output', 'input', 'links'], 'initialization': ['script', 'grammars']}
orig_node_struct = {'dialoglist': {'dialog': {'output': [('message', 'lydia_output'), ('copilot', 'lydia_copilot')],
                                              'input': [('recognition', 'pattern'), ('scan', 'pattern')],
                                              'links': 'dialog_dict'}}}

orig_init_node_struct = {'initialization': {'script': '', 'grammars': {'constraint': ''}}}

excluded_field_depend = {'decimalsmin': (
    'type', 'float'), 'decimalsmax': ('type', 'float')}

excluded_fields = ['create_date', 'write_date', 'display_name', '__last_update', 'create_uid', 'write_uid',
                   'id', 'model_id', 'content', 'dialoglist_ids', 'idle_template', 'first_dialog_id',
                   'dialoglist_id', 'default_code', 'dialog_id', 'input_id', 'name', 'sub_dialog_id',
                   'grammar_rule_ids', 'type', 'js_script_ids']

excluded_values = {'method': 'get', 'terminate': False}

subelemnt_dict = {'links': 'link', 'grammars': 'grammarrule'}

keep_if_empty = {'input', 'output', 'message'}

attribute_value_map = {'constraint': 'type'}


def CDATA(text=None):
    element = ET.Element('![CDATA[')
    element.text = text
    return element


ET._original_serialize_xml = ET._serialize_xml


def _serialize_xml(write, elem, qnames, namespaces, short_empty_elements, **kwargs):
    if elem.tag == '![CDATA[':
        write("\n<{}{}]]>\n".format(elem.tag, elem.text))
        if elem.tail:
            write(_escape_cdata(elem.tail))
    else:
        return ET._original_serialize_xml(write, elem, qnames, namespaces, short_empty_elements, **kwargs)


ET._serialize_xml = ET._serialize['xml'] = _serialize_xml


class XmlGenerator(models.Model):
    _name = 'xml.generator'
    _description = 'Generate XML from dialogue list'

    def get_field_type(self, object, field):
        model = object._name
        ir_model_obj = self.env['ir.model.fields']
        ir_model_field = ir_model_obj.search(
            [('model', '=', model), ('name', '=', field)])
        field_type = ir_model_field.ttype
        return field_type

    @api.model
    def map_field(self, attribute, inverse=False):
        if inverse:
            for key, value in attribute_map.items():
                if value == attribute:
                    return key
        if attribute in attribute_map:
            return attribute_map[attribute]
        return attribute

    @api.model
    def check_exists(self, sub_key, content=None):
        if type(content) is list:
            for item in content:
                if type(item) is tuple:
                    if item[0] == sub_key:
                        return True
                else:
                    if item == sub_key:
                        return True
        elif type(content) is dict:
            if sub_key in content:
                return True

    @api.model
    def add_header_nodes(self):
        root = ET.Element('voicedialog')
        root.set('schemaVersion', "2")
        root.set('xsi:schemaLocation',
                 "http://www.topsystem.de/xmlns/LydiaRESTInterface ../LydiaRESTInterface.xsd")
        root.set('xmlns:xsi', "http://www.w3.org/2001/XMLSchema-instance")
        root.set('xmlns', "http://www.topsystem.de/xmlns/LydiaRESTInterface")
        return root

    @api.model
    def keep_if_empty(self, dict, parent_element, root_element):
        if root_element in keep_if_empty:
            subelement = ET.SubElement(parent_element, root_element)
            parent_element = subelement
            for key in dict:
                if key in keep_if_empty:
                    if type(dict[key]) is dict:
                        subelement = ET.SubElement(parent_element, key)
                        parent_element = subelement
                        self.keep_if_empty(dict[key], parent_element)
                    elif type(dict[key]) is list:
                        for item in dict[key]:
                            if item[0] in keep_if_empty:
                                ET.SubElement(parent_element, item[0])

    @api.model
    def exclude_dependent(self, field, object):
        if field in excluded_field_depend:
            if getattr(object, excluded_field_depend[field][0]) != excluded_field_depend[field][1]:
                return True
            else:
                return False
        else:
            return False

    @api.model
    def generate_nodes(self, object, node_struct=orig_node_struct, parent_element=None, root=None, root_element=None,
                       no_header=False):
        if root == None:
            if not no_header:
                root = self.add_header_nodes()
                parent_element = ET.SubElement(root, root_element)
            else:
                root = ET.Element(root_element)
                parent_element = root
        else:
            if root_element in subelemnt_dict:
                subelement = ET.SubElement(
                    parent_element, subelemnt_dict[root_element])
                parent_element = subelement
            elif root_element in attribute_value_map:
                value = getattr(object, attribute_value_map[root_element])
                subelement = ET.SubElement(parent_element, value)
                parent_element = subelement
            else:
                subelement = ET.SubElement(parent_element, root_element)
                parent_element = subelement
        fields = object._fields
        for field in fields:
            if not self.exclude_dependent(field, object):
                key = self.map_field(field, inverse=True)
                if (not self.check_exists(key, node_struct[root_element])) and field not in excluded_fields:
                    attribute = str(getattr(object, field))
                    if attribute and attribute != 'False' and attribute != excluded_values.get(field):
                        parent_element.set(key, attribute)
        if type(node_struct[root_element]) is dict:
            if root_element in dict_order:
                elements = dict_order[root_element]
            else:
                elements = node_struct[root_element]
            for subkey in elements:
                field_name = self.map_field(subkey)
                field_value = getattr(object, field_name)
                if field_value:
                    if type(field_value) is str:
                        if subkey == 'script':
                            cdata = CDATA(field_value)
                            subelement = ET.SubElement(parent_element, subkey)
                            temp_parent = parent_element
                            parent_element = subelement
                            parent_element.append(cdata)
                            parent_element = temp_parent
                    else:
                        if subkey in subelemnt_dict:
                            subelement = ET.SubElement(parent_element, subkey)
                            parent_element = subelement
                        for record in field_value:
                            self.generate_nodes(object=record, node_struct=node_struct[root_element],
                                                parent_element=parent_element, root=root, root_element=subkey)
                else:
                    self.keep_if_empty(
                        node_struct[root_element][subkey], parent_element, subkey)
        if object._name == 'tspbv.grammar.rule':
            value = str(getattr(object, 'content'))
            if value and value != 'False':
                if len(parent_element):
                    parent_element[len(parent_element) - 1].tail = value
                else:
                    parent_element.text = value

        elif node_struct[root_element] == 'dialog_dict':
            field_value = getattr(object, 'sub_dialog_id')
            if field_value:
                for record in field_value:
                    self.generate_nodes(object=record, node_struct=orig_node_struct['dialoglist'],
                                        parent_element=parent_element, root=root, root_element='dialog')

        elif type(node_struct[root_element]) is list:
            for element in node_struct[root_element]:
                if type(element) is tuple:
                    field_name = self.map_field(element[0])
                    field_type = self.get_field_type(object, field_name)
                    if field_type in ['many2one', 'one2many']:
                        field_name = self.map_field(element[0])
                        field_value = getattr(object, field_name)
                        if field_value:
                            for record in field_value:
                                subelement = ET.SubElement(
                                    parent_element, element[0])
                                subelement.text = getattr(record, element[1])
                                fields = getattr(field_value, '_fields')
                                for field in fields:
                                    if field not in excluded_fields and field != element[1]:
                                        value = getattr(record, field)
                                        if value and value != 'False' and value != excluded_values.get(field):
                                            attribute = self.map_field(
                                                field, inverse=True)
                                            if attribute:
                                                subelement.set(
                                                    attribute, str(value))
                        elif element[0] in keep_if_empty:
                            ET.SubElement(parent_element, element[0])
                    else:
                        value = getattr(object, element[1])
                        if value and value != False:
                            subelement = ET.SubElement(
                                parent_element, element[0])
                            subelement.text = getattr(object, element[1])
                        elif element[0] in keep_if_empty:
                            ET.SubElement(parent_element, element[0])

        return root

    @api.model
    def generate_xml_doc(self, dialog_list_id, no_header=False):
        return self.generate_nodes(dialog_list_id, node_struct=orig_node_struct, parent_element=None, root=None,
                                   root_element='dialoglist', no_header=no_header)

    @api.model
    def generate_init_doc(self, workflow_id):
        return self.generate_nodes(workflow_id, node_struct=orig_init_node_struct, parent_element=None, root=None,
                                   root_element='initialization')
