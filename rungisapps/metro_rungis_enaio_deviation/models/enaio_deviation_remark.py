from odoo import api, fields, models

class EnaioDeviationRemark(models.Model):
    _name = 'enaio.deviation.remark'
    _description = 'Enaio Deviation Remark'
    _inherit = 'mail.thread'

    name = fields.Char("Deviation Code")
    remark = fields.Text("Deviation Description")

    _sql_constraints = [('name_unique', 'unique(name)', 'Deviation Code must be unique!')]

    @api.multi
    def name_get(self):
        res=[]
        for name in self:
            res.append((name.id,'%s'% (name.remark)))
        return res

class StockMoveLine(models.Model):
    _inherit='stock.move.line'

    enaio_remark_id = fields.Many2one('enaio.deviation.remark', "Enaio Deviation Remark")

class SaleOrderLine(models.Model):
    _inherit='sale.order.line'

    enaio_remark_id = fields.Many2one('enaio.deviation.remark', "Enaio Deviation Remark")
