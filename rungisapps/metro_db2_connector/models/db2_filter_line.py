from odoo import api, fields, models


class FilterLine(models.Model):
    _name = 'db2.filter.line'
    _description = 'Filter Line'

    attributes = fields.Selection(
        selection=[
            ('OAUKGRP', 'customer group'),
            ('OAUKDNR', 'softm customer reference'),
            ('OAUAUFN', 'softm order number'),
            ('OAUARTN', 'product code'),
            ('OAUALP', 'run up point'),
        ], help="""
            customer group: OAUKGRP
            softm customer reference :OAUKDNR
            softm order number: OAUAUFN
            product code: OAUARTN
            run up point: OAUALP
        """,
        required=True
    )
    condition = fields.Selection(
        selection=[
            ('=', '='),
            ('!=', '!='),
        ],
        required=True
    ) 
    value = fields.Char(required=True)
    backend_id = fields.Many2one(comodel_name='db2.backend')
