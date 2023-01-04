from odoo.tests.common import TransactionCase


class TestGenerateDialoglistXml(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Dialog = self.env['tspbv.dialog']
        self.Input = self.env['tspbv.input']
        self.GrammarRule = self.env['tspbv.grammar.rule']
        self.Input = self.env['tspbv.input']
        self.Link = self.env['tspbv.link']
        self.Output = self.env['tspbv.output']
        self.Recognition = self.env['tspbv.recognition']
        self.Scan = self.env['tspbv.scan']

    def test_dialog_name(self):
        dialog = self.Dialog.create({
            'id_dialog': 'my_dialog'
        })
        self.assertEqual(dialog.display_name, 'my_dialog')
        dialog.write({
            'id_dialog': 'my_dialog_changed'
        })
        self.assertNotEqual(dialog.display_name, 'my_dialog_changed')
        dialog._compute_display_name()
        self.assertEqual(dialog.display_name, 'my_dialog_changed')

    def test_grammer_rule_name(self):
        grammar_rule_rec = self.GrammarRule.create({
            'rule_name': 'my_rule'
        })
        self.assertEqual(grammar_rule_rec.display_name, 'my_rule')
        grammar_rule_rec.write({
            'rule_name': 'my_rule_changed'
        })
        self.assertNotEqual(grammar_rule_rec.display_name, 'my_rule_changed')
        grammar_rule_rec._compute_display_name()
        self.assertEqual(grammar_rule_rec.display_name, 'my_rule_changed')

    def test_link_name(self):
        link = self.Link.create({
            'rel': 'my_rel'
        })
        self.assertEqual(link.display_name, 'my_rel')
        link.write({
            'rel': 'my_rel_changed'
        })
        self.assertNotEqual(link.display_name, 'my_rel_changed')
        link._compute_display_name()
        self.assertEqual(link.display_name, 'my_rel_changed')

    def test_output_name(self):
        output = self.Output.create({
            'lydia_output': 'my_output'
        })
        self.assertEqual(output.display_name, 'my_output')
        output.write({
            'lydia_output': 'my_output_changed'
        })
        self.assertNotEqual(output.display_name, 'my_output_changed')
        output._compute_display_name()
        self.assertEqual(output.display_name, 'my_output_changed')

    def test_recognition_name(self):
        recognition = self.Recognition.create({
            'rel': 'my_rel'
        })
        self.assertEqual(recognition.display_name, 'my_rel')
        recognition.write({
            'rel': 'my_rel_changed'
        })
        self.assertNotEqual(recognition.display_name, 'my_rel_changed')
        recognition._compute_display_name()
        self.assertEqual(recognition.display_name, 'my_rel_changed')

    def test_scan_name(self):
        scan = self.Scan.create({
            'rel': 'my_rel'
        })
        self.assertEqual(scan.display_name, 'my_rel')
        scan.write({
            'rel': 'my_rel_changed'
        })
        self.assertNotEqual(scan.display_name, 'my_rel_changed')
        scan._compute_display_name()
        self.assertEqual(scan.display_name, 'my_rel_changed')
