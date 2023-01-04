# -*- coding: utf-8 -*-
import logging
import json
from datetime import datetime, timedelta

from odoo import models, api, fields
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError


_logger = logging.getLogger(__name__)

class Variable(models.Model):
    _name = "metro.dashboard.variable"
    _description = "Variables for the Tiles which hold often used values."
    _sql_constraints = [
        ("name_unique", "unique(name)", "This variable name is already used"),
    ]

    active = fields.Boolean(
        default=True
    )
    name = fields.Char(
        string="Variable Name",
        help="This will be the variable name you call when using the variable.",
        required=True
    )
    compute_code = fields.Text("Python Code", help="Result will be calculated here", required=True)
    var_type = fields.Selection([
        ("bool", "Boolean"),
        ("int", "Integer"),
        ("float", "Float"),
        ("dict", "Dictionary"),
        ("list", "List/Array"),
        ("string", "String"),
    ], string="Type", help="Type of the result the variable will hold", default="float")
    # The current value will be parsed in the right type later
    value = fields.Char(
        string="Current Value",
        readonly=True,
        store=True
    )
    # A preview for the value, if the value contains more than x characters the string will be shortened
    value_preview = fields.Char(
        string="Current Value",
        readonly=True,
        compute="_get_value_preview"
    )
    dependencies = fields.Char(
        string="All dependencies",
        help="The modules which need to be installed to compute this Statistic"
    )
    uninstalled_dependencies = fields.Char(
        help="Please install those dependencies before using the Variable."
    )
    dependency_count = fields.Integer(
        string="# Dependencies",
        help="The number of dependencies this variable has.",
        compute="_compute_dependency_count"
    )

    # Replace whitespaces (except trailing and leading) with underscores
    # Calculate the current value directly when created
    @api.model
    def create(self, vals):
        if "name" in vals:
            vals["name"] = vals["name"].strip().replace(" ", "_")
        res = super(Variable, self).create(vals)
        if "compute_code" in vals:
            res.execute_code()
        return res
    
    # Recalculate the value when either the var_type or compute_code changes
    # In the name of the variable it will replace the whitespaces with an underscore
    # and remove the trailing and leading whitespaces
    @api.multi
    def write(self, vals):
        # Remove tailing/leading whitespaces and replace rest of the whitespaces with underscores
        if "name" in vals:
            vals["name"] = vals["name"].strip().replace(" ", "_")
        res = super(Variable, self).write(vals)
        # Recalculate the current value with the new type (and maybe code)
        if "var_type" in vals:
            self.execute_code()
        # Recalculate the current value with the new code
        elif "compute_code" in vals:
            self.execute_code()
        return res

    @api.one
    def execute_code(self):
        self.check_dependencies()
        if self.uninstalled_dependencies:
            _logger.warn("Please install the following dependencies before calculting %s: %s", self.name, self.uninstalled_dependencies)
            self.value = ""
            return
        # Variables which are available inside the compute_code code
        ctx = {
            "val": self.val,
            "env": self.env,
            "datetime": datetime,
            "timedelta": timedelta,
            "type": type,
            "load": json.loads,
            "parse": json.dumps,
            "log": _logger.info
        }
        # Get the code and remove trailing/leading whitespaces
        code = self.compute_code.strip()
        # Evaluate the code with the given context
        try:
            safe_eval(code, ctx, mode="exec", nocopy=True)
        except ValueError:
            _logger.warn("Dependency for Variable " + self.name + " is missing.")
            self.active = False
            self.value = ""
            return
        except Exception as e:
            raise e
        # Get the result
        result = ctx.get("result")
        if result == None:
            raise ValidationError("You need to provide a result variable with the given type.")
        # If the result is present and it's one of the specified types
        # Save the result with the type
        try:
            if result and self.var_type == "float":
                self.value = float(result)
            elif result and self.var_type == "int":
                self.value = int(result)
            elif result != None and self.var_type == "bool":
                self.value = bool(result)
            elif result and self.var_type == "string":
                self.value = result
            # If only result is given (and it's a list or dict)
            # set the value to the json of the result
            elif result:
                self.value = json.dumps(result)
            # If there was in error, log it
            else:
                _logger.error("No result is given for the variable " + self.name)
        except (ValueError, TypeError) as e:
            err = "You need to provide the result variable with the given type.\n"
            err += "Type " + str(type(result)) + " should be " + self.var_type + "."
            raise ValidationError(err)
        except Exception as e:
            raise ValidationError("An unkown error occured: " + str(e))

    # The function val() returns the value in the correct format
    # The arguments are required when the variable changes the type
    # This function gets executed before those values are written to a database
    def val(self, data=None, new_type=None):
        # Variable for holding the type
        t = None
        if new_type:
            t = new_type
        else:
            t = self.var_type
        # Variable for holding the value
        val = None
        if data:
            val = data
        else:
            val = self.value
        # Try to convert the current value to the given type
        # If no value is given return either 0 or an empty list/dict
        try:
            if t == "float":
                if not val:
                    return 0.0
                return float(val)
            elif t == "int":
                if not val:
                    return 0
                return int(float(val))
            elif t == "bool":
                if not val:
                    return False
                return bool(val)
            elif t == "dict":
                if not val:
                    return {}
                return json.loads(val)
            elif t == "list":
                if not val:
                    return []
                return json.loads(val)
            # Datatype must be string
            else:
                if not val:
                    return ""
                return val
        # If it was not possible to convert the value to the type
        # log an error
        except Exception:
            _logger.error("Failed to convert the value (type: %s) '%s' into the type '%s'", type(self.value), self.value, self.var_type)

    @api.model
    def _cron_update(self):
        # Get all variables and recalculate the value
        variables = self.env["metro.dashboard.variable"].search([
            ("active", "=", True)
        ])
        for var in variables:
            var.execute_code()

    @api.model
    def action_update(self):
        ids = self.env.context["active_ids"]
        records = self.browse(ids)
        for record in records:
            record.execute_code()
        
    @api.multi
    def _get_value_preview(self):
        for r in self:
            r.value_preview = r.value[:150]
            if len(r.value) >= 150:
                r.value_preview += "..."

    @api.multi
    def _compute_dependency_count(self):
        for r in self:
            if r.dependencies:
                r.dependency_count = len(r.dependencies.split(","))
            else:
                r.dependency_count = 0
            
    @api.multi
    def check_dependencies(self):
        for r in self:
            if r.dependencies:
                r.uninstalled_dependencies = ""
                dependencies = r.dependencies.split(",")
                for i in range(len(dependencies)):
                    dependency = dependencies[i]
                    module = self.env["ir.module.module"].search([("name", "=", dependency)])
                    if module.state != "installed":
                        r.uninstalled_dependencies += dependency + ","
                # Remove trailing comma and set to inactive if dependencies are not installed
                if r.uninstalled_dependencies:
                    r.uninstalled_dependencies = r.uninstalled_dependencies[:-1]
                    r.active = False
                else:
                    r.active = True
            else:
                r.active = True
