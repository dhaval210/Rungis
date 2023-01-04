from odoo import api, models, fields
from odoo.addons.queue_job.job import job
from lxml import etree

from odoo.exceptions import ValidationError


class Picking(models.Model):
    _inherit = 'stock.picking'

    async_state = fields.Selection(
        selection=[
            ('progress', 'Confirm in progress'),
            ('done', 'Done'),
        ],
        default=False
    )

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'tree' and 'async_state' in res['fields']:
            type_id = self._context.get('default_picking_type_id', False)
            if type_id is not False:
                p_type = self.env['stock.picking.type'].browse(type_id)
                if p_type.allow_async_validate is False:
                    doc = etree.XML(res['arch'])
                    for node in doc.xpath("//field[@name='async_state']"):
                        doc.remove(node)
                    del res['fields']['async_state']
                    res['arch'] = etree.tostring(doc)
                    if toolbar and res['toolbar'].get('action', False):
                        for action in res['toolbar'].get('action'):
                            if action['xml_id'] == 'metro_validate_pack.validate_packing':
                                res['toolbar']['action'].remove(action)
        return res


    @api.multi
    def action_validate_packing(self):
        failed = False
        failed_packs = []
        for rec in self:
            if rec.check_pick_validation():
                if rec.async_state != 'done':
                    rec.async_state = 'progress'
                rec.with_delay(eta=2).async_validate_packing()
            else:
                failed = True
                failed_packs.append(rec.name)
        if failed:
            failed_packs_string = ', '.join(pack for pack in failed_packs)
            raise ValidationError('Please validate or cancel the remaining'
                                  ' picking before validating the packing of '
                                  + failed_packs_string)
        return True

    @job(default_channel='root.stock_picking')
    @api.multi
    def async_validate_packing(self):
        for record in self:
            wiz = self.env['stock.immediate.transfer'].create({
                'pick_ids': [(4, record.id)]
            })
            wiz.process()
            if record._check_backorder():
                backorder_confirm = self.env['stock.backorder.confirmation'].create(
                    {'pick_ids': [(4, p.id) for p in record]})
                backorder_confirm.process_cancel_backorder()
            record.async_state = 'done'
        return True

    @api.multi
    def button_validate(self):
        if self.check_pick_validation():
            return super(Picking, self).button_validate()
        else:
            raise ValidationError('Please validate or cancel the remaining'
                                  ' picking before validating the packing')

    @api.multi
    def check_pick_validation(self):
        for rec in self:
            if 'pack' in rec.picking_type_id.name.lower():
                pick_ids = rec.search([
                    ('group_id', '=', rec.group_id.id),
                ]).filtered(
                    lambda pick: 'pick' in pick.picking_type_id.name.lower())
                states = pick_ids.mapped('state')
                if states and all(
                        state in ['done', 'cancel'] for state in states):
                    return True
                else:
                    return False
            return True
