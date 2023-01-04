import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from odoo.tests.common import TransactionCase


class TestGenerateDialoglistXml(TransactionCase):

    def setUp(self):
        super().setUp()
        self.simplexml = self.env.ref('tspbv_connector.dialoglist_1')
        self.complexxml = self.env.ref('tspbv_connector.dialoglist_2')
        self.workflow = self.env.ref('tspbv_connector.workflow_1')
        self.DialoglistModel = self.env['tspbv.dialoglist']

        root = ET.Element('voicedialog')
        root.set('schemaVersion', "2")
        root.set('xsi:schemaLocation', "http://www.topsystem.de/xmlns/LydiaRESTInterface ../LydiaRESTInterface.xsd")
        root.set('xmlns:xsi', "http://www.w3.org/2001/XMLSchema-instance")
        root.set('xmlns', "http://www.topsystem.de/xmlns/LydiaRESTInterface")
        dialoglist = ET.SubElement(root, 'dialoglist', {"start": "startOrder"})
        dialog = ET.SubElement(dialoglist, 'dialog', {"id": "startOrder"})
        output = ET.SubElement(dialog, 'output')
        message = ET.SubElement(output, 'message')
        message.text = "Order §spell{123456}, 6 positions, 1 pallet"
        copilot = ET.SubElement(output, 'copilot')
        copilot.text = "order: 123456, positions: 6, pallets: 1"
        xml_input = ET.SubElement(
            dialog,
            'input',
            {"grammarrules": "start order"}
        )
        recognition = ET.SubElement(xml_input, 'recognition', {"rel": "pos1"})
        recognition.text = "start order"
        links = ET.SubElement(dialog, 'links')
        link = ET.SubElement(
            links,
            'link',
            {
                "href": "http://.../Demo_Pos1.xml",
                "method": "post",
                "rel": "pos1"
            }
        )
        rough_string = ET.tostring(root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        self.expected_simple_xml = reparsed.toprettyxml(indent="\t")

        root = ET.Element('voicedialog')
        root.set('schemaVersion', "2")
        root.set(
            'xsi:schemaLocation',
            "http://www.topsystem.de/xmlns/LydiaRESTInterface " +
            "../LydiaRESTInterface.xsd"
        )
        root.set('xmlns:xsi', "http://www.w3.org/2001/XMLSchema-instance")
        root.set('xmlns', "http://www.topsystem.de/xmlns/LydiaRESTInterface")
        dialoglist = ET.SubElement(root, 'dialoglist', {"start": "aisle"})
        dialog = ET.SubElement(dialoglist, 'dialog', {"id": "aisle"})
        output = ET.SubElement(dialog, 'output')
        message = ET.SubElement(output, 'message')
        message.text = "Aisle 1"
        xml_input = ET.SubElement(dialog, 'input', {"grammarrules": "okay"})
        recognition = ET.SubElement(
            xml_input,
            'recognition',
            {"rel": "aisleok"}
        )
        recognition.text = "okay"
        links = ET.SubElement(dialog, 'links')
        link = ET.SubElement(
            links,
            'link',
            {
                "href": "#location",
                "rel": "aisleok"
            }
        )
        dialog_2 = ET.SubElement(dialoglist, 'dialog', {"id": "location"})
        output_2 = ET.SubElement(dialog_2, 'output')
        message_2 = ET.SubElement(output_2, 'message')
        message_2.text = "Rack 5 shelf 11"
        xml_input_2 = ET.SubElement(
            dialog_2,
            'input',
            {"grammarrules": "checkdigit"}
        )
        recognition_2 = ET.SubElement(
            xml_input_2,
            'recognition',
            {"rel": "checkdigitok"}
        )
        recognition_2.text = "(62) okay"
        scan_2 = ET.SubElement(
            xml_input_2,
            'scan',
            {"rel": "checkdigitok", "onMatch": "$0==62"}
        )
        scan_2.text = ".*"
        links_2 = ET.SubElement(dialog_2, 'links')
        link_2 = ET.SubElement(
            links_2,
            'link',
            {
                "href": "#amount",
                "rel": "checkdigitok"
            }
        )
        link_3 = ET.SubElement(
            links_2,
            'link',
            {
                "rel": "checkdigitnotok"
            }
        )
        dialog_3 = ET.SubElement(
            link_3,
            'dialog',
            {"id": "checkDigitNotOkDialog"}
        )
        output_3 = ET.SubElement(dialog_3, 'output')
        message_3 = ET.SubElement(output_3, 'message')
        message_3.text = "checkdigit not ok"
        xml_input_3 = ET.SubElement(dialog_3, 'input')
        links_4 = ET.SubElement(dialog_3, 'links')
        link_4 = ET.SubElement(
            links_4,
            'link',
            {
                "href": "#location",
                "rel": "*"
            }
        )

        dialog_4 = ET.SubElement(dialoglist, 'dialog', {"id": "amount"})
        output_4 = ET.SubElement(dialog_4, 'output')
        message_4 = ET.SubElement(output_4, 'message')
        message_4.text = "Take 2"
        xml_input_4 = ET.SubElement(
            dialog_4,
            'input',
            {"grammarrules": "pickamount"}
        )
        recognition_5 = ET.SubElement(
            xml_input_4,
            'recognition',
            {"rel": "confirmSubAmount", "onMatch": "checkSubAmount($1, 2)"}
        )
        recognition_6 = ET.SubElement(
            xml_input_4,
            'recognition',
            {"rel": "amountCorrect"}
        )
        recognition_4 = ET.SubElement(
            xml_input_4,
            'scan',
            {"rel": "overAmountNotOk", "onMatch": "2 > $1"}
        )
        recognition_4.text = "([0-9]{1,3}) okay"
        recognition_5.text = "([0-9]{1,3}) okay"
        recognition_6.text = "([0-9]{1,3}) okay"
        links_5 = ET.SubElement(dialog_4, 'links')
        link_5 = ET.SubElement(
            links_5,
            'link',
            {
                "href": "#overamountnotallowed",
                "rel": "overAmountNotOk"
            }
        )
        link_6 = ET.SubElement(
            links_5,
            'link',
            {
                "href": "#confirmsubamount",
                "rel": "confirmSubAmount"
            }
        )
        link_7 = ET.SubElement(
            links_5,
            'link',
            {
                "href": "http://.../Demo_FinishOrder.xml",
                "rel": "amountCorrect"
            }
        )
        dialog_5 = ET.SubElement(
            dialoglist,
            'dialog',
            {"id": "overamountnotallowed"}
        )
        output_5 = ET.SubElement(dialog_5, 'output')
        message_5 = ET.SubElement(output_5, 'message')
        message_5.text = "Overamount not allowed"
        xml_input_5 = ET.SubElement(dialog_5, 'input')
        links_6 = ET.SubElement(dialog_5, 'links')
        link_8 = ET.SubElement(
            links_6,
            'link',
            {
                "href": "#amount",
                "rel": "*"
            }
        )

        dialog_6 = ET.SubElement(
            dialoglist,
            'dialog',
            {"id": "confirmsubamount"}
        )
        output_6 = ET.SubElement(dialog_6, 'output')
        message_6 = ET.SubElement(output_6, 'message')
        message_6.text = "Confirm ${amount}[1]"
        xml_input_6 = ET.SubElement(
            dialog_6,
            'input',
            {"grammarrules": "pickamount,cancel"}
        )
        recognition_7 = ET.SubElement(
            xml_input_6,
            'recognition',
            {"rel": "cancel"}
        )
        recognition_8 = ET.SubElement(
            xml_input_6,
            'recognition',
            {"rel": "confirm", "onMatch": "$1==${amount}[1]"}
        )
        recognition_7.text = "cancel"
        recognition_8.text = "([0-9]{1,3}) okay"
        links_7 = ET.SubElement(dialog_6, 'links')
        link_9 = ET.SubElement(
            links_7,
            'link',
            {
                "href": "#amount",
                "rel": "cancel"
            }
        )
        link_10 = ET.SubElement(
            links_7,
            'link',
            {
                "href": "http://.../Demo_FinishOrder.xml",
                "rel": "confirm"
            }
        )
        rough_string = ET.tostring(root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        self.expected_complex_xml = reparsed.toprettyxml(indent="\t")

        root = ET.Element('voicedialog')
        root.set('schemaVersion', "2")
        root.set('xsi:schemaLocation', "http://www.topsystem.de/xmlns/LydiaRESTInterface ../LydiaRESTInterface.xsd")
        root.set('xmlns:xsi', "http://www.w3.org/2001/XMLSchema-instance")
        root.set('xmlns', "http://www.topsystem.de/xmlns/LydiaRESTInterface")
        initialization = ET.SubElement(root, 'initialization')
        grammars = ET.SubElement(initialization, 'grammars')
        grammarrule_1 = ET.SubElement(grammars, 'grammarrule', {"name": "start order"})
        grammarrule_2 = ET.SubElement(grammars, 'grammarrule', {"name": "abort order"})
        grammarrule_3 = ET.SubElement(grammars, 'grammarrule', {"name": "confirmabortorder"})
        grammarrule_4 = ET.SubElement(grammars, 'grammarrule', {"name": "locationok"})
        grammarrule_4.text = "okay"
        digits_1 = ET.SubElement(grammarrule_4, 'digits', {"min": "1", "max": "2"})

        dialoglist = ET.SubElement(root, 'dialoglist', {"start": "startDialog"})
        dialog = ET.SubElement(dialoglist, 'dialog', {"id": "startDialog"})
        output = ET.SubElement(dialog, 'output')
        xml_input = ET.SubElement(dialog, 'input')
        links = ET.SubElement(dialog, 'links')
        url = self.env["ir.config_parameter"].sudo().get_param('web.base.url')
        link = ET.SubElement(
            links,
            'link',
            {
                "href": (
                    url +
                    "/tspbv/dialoglist?dialoglist_code=session&record_id=1"
                ),
                "rel": "*"
            }
        )
        rough_string = ET.tostring(root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        self.expected_init_xml = reparsed.toprettyxml(indent="\t")

    def test_simplexml_convertion(self):
        xml = self.simplexml.generate_dialoglist_xml(1)
        self.assertEqual(xml, self.expected_simple_xml)

    def test_complexxml_convertion(self):
        xml = self.complexxml.generate_dialoglist_xml(1)
        self.assertEqual(xml, self.expected_complex_xml)

    def test_initxml_convertion(self):
        xml = self.workflow.generate_init_xml(1)
        self.assertEqual(xml, self.expected_init_xml)
