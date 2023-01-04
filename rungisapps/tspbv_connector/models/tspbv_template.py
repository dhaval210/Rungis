# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import copy
import datetime
import dateutil.relativedelta as relativedelta
import logging
import functools
from werkzeug import urls
from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError
from odoo.tools import pycompat
_logger = logging.getLogger(__name__)

try:
    # We use a jinja2 sandboxed environment to render mako templates.
    # Note that the rendering does not cover all the mako syntax, in particular
    # arbitrary Python statements are not accepted, and not all expressions are
    # allowed: only "public" attributes (not starting with '_') of objects may
    # be accessed.
    # This is done on purpose: it prevents incidental or malicious execution of
    # Python code that may break the security of the server.
    from jinja2.sandbox import SandboxedEnvironment
    mako_template_env = SandboxedEnvironment(
        block_start_string='~[',
        block_end_string=']~',
        variable_start_string="$[",
        variable_end_string="]",
        trim_blocks=True,               # do not output newline after blocks
        autoescape=True,                # XML/HTML automatic escaping
    )
    mako_template_env.globals.update({
        'str': str,
        'quote': urls.url_quote,
        'urlencode': urls.url_encode,
        'datetime': datetime,
        'len': len,
        'abs': abs,
        'min': min,
        'max': max,
        'sum': sum,
        'filter': filter,
        'reduce': functools.reduce,
        'map': map,
        'round': round,

        # dateutil.relativedelta is an old-style class and cannot be directly
        # instanciated wihtin a jinja2 expression, so a lambda "proxy" is
        # is needed, apparently.
        'relativedelta': lambda *a, **kw : relativedelta.relativedelta(*a, **kw),
    })
    mako_safe_template_env = copy.copy(mako_template_env)
    mako_safe_template_env.autoescape = False
except ImportError:
    _logger.warning("jinja2 not available, templating features will not work!")


class TspbvTemplate(models.Model):
    "Templates for sending email"
    _name = "tspbv.template"
    _description = 'TSPBV Templates'
    _order = 'name'


    @api.model
    def _render_template(self, template_txt, model, res_ids, post_process=False):
        """ Render the given template text, replace mako expressions ``$[expr]``
        with the result of evaluating these expressions with an evaluation
        context containing:

         - ``object``: record of the document record this mail is related to

        :param str template_txt: the template text to render
        :param str model: model name of the document record this mail is related to.
        :param int res_ids: list of ids of document records those mails are related to.
        """
        multi_mode = True
        if isinstance(res_ids, pycompat.integer_types):
            multi_mode = False
            res_ids = [res_ids]

        results = dict.fromkeys(res_ids, u"")

        # try to load the template
        try:
            mako_env = mako_safe_template_env if self.env.context.get('safe') else mako_template_env
            template = mako_env.from_string(tools.ustr(template_txt))
        except Exception:
            _logger.info("Failed to load template %r", template_txt, exc_info=True)
            return multi_mode and results or results[res_ids[0]]

        # prepare template variables
        records = self.env[model].browse(it for it in res_ids if it)  # filter to avoid browsing [None]
        res_to_rec = dict.fromkeys(res_ids, None)
        for record in records:
            res_to_rec[record.id] = record
        variables = {}
        for res_id, record in res_to_rec.items():
            variables['object'] = record
            try:
                render_result = template.render(variables)
            except Exception:
                _logger.info("Failed to render template %r using values %r" % (template, variables), exc_info=True)
                raise UserError(_("Failed to render template %r using values %r")% (template, variables))
            if render_result == u"False":
                render_result = u""
            results[res_id] = render_result

        if post_process:
            for res_id, result in results.items():
                results[res_id] = self.render_post_process(result)
        return multi_mode and results or results[res_ids[0]]