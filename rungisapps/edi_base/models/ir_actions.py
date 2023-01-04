# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class IrActionsServer(models.Model):

    _inherit = 'ir.actions.server'

    @api.model
    def _get_eval_context(self, action=None):
        """
        """

        eval_context = super(IrActionsServer, self)._get_eval_context(action=action)

        if not action:
            return eval_context

        integration = self.env['edi.integration'].search([
            ('integration_server_action_id', '=', action.id)
        ])
        if not integration:
            return eval_context

        self_with_context = self.with_context(
            active_model='edi.integration',
            active_id=integration.id
        )
        return super(IrActionsServer, self_with_context)._get_eval_context(action=action)
