# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import logging
import json
# import psycopg2.errors as sql
import psycopg2

from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError, UserError
from odoo.tools.convert import ParseError

_logger = logging.getLogger(__name__)

def list2KeysStr(l):
    keys = ""
    for i in range(0, len(l)):
        keys += l[i]
        if not i == len(l) - 1:
            keys += " \\s "
    return keys


class MetroDashboardStatistics(models.Model):
    _name = "metro.dashboard.statistics"
    _description = "This model holds statistical data, either numbers or complex data types. A statistic can be assigned to a dashboard where a tile is generated from it."

    active = fields.Boolean(
        default=True
    )
    name = fields.Char(
        required=True
    )
    visualisation = fields.Selection([
        ("number", "Show Number"),
        ("bar", "Bar Chart"),
        ("line", "Line Chart"),
        ("pie", "Pie Chart"),
    ], default="number")
    data_source = fields.Selection([
        ("python", "Python Code"),
        ("data", "Use existing dataset(s)")
    ], default="python")
    compute_code = fields.Text(
        "Python Code",
        help="This code will be evaluated. The result variable depends on the type of visualisation."
    )
    dataset_ids = fields.Many2many(
        "metro.dashboard.dataset",
        string="Datasets"
    )
    dataset_count = fields.Integer(
        compute="_get_dataset_count"
    )
    dataset_keys_id = fields.Many2one(
        "metro.dashboard.dataset"
    )
    monetary = fields.Boolean(
        string="Use monetary value",
        default=False
    )
    use_timeframes = fields.Boolean(
        string="Use predefined timeframes",
        help="Predefined timeframes are 'Last 30 days' and 'Last 90 days'. If the predefined timeframes are not used you need to specify them inside the compute_code field.",
        default=False
    )
    cust_timeframe = fields.Char(
        "Custom Timeframe",
        help="This label is shown when a timeframe does not use the standard timeframes (use_timeframes=True)"
    )
    symbol = fields.Char(
        compute="_get_currency_symbol",
        store=True
    )
    suffix = fields.Char()
    # Value for timeframe = Last 30 days
    value = fields.Char(
        string="Value of the computation for the last 30 days.",
        help="The result of the computation for the timeframe 'Last 30 days' will be stored here."
    )
    value_preview = fields.Char(
        string="Value",
        help="This is a preview of your result. If you have the predefined timeframes activated, this will be the preview for the timeframe of 30 days.",
        compute="_get_value_preview"
    )
    # Value for timeframe = Last 90 days
    value90 = fields.Char(
        string="Value of the computation for the last 90 days.",
        help="The result of the computation for the timeframe 'Last 90 days' will be stored here.",
        default=""
    )
    keys = fields.Char(
        help="List of keys used by this statistic",
        store=True
    )
    keys90 = fields.Char(
        help="List of keys used by this statistic with the timeframe = Last 90 days",
        default="",
        store=True
    )
    table_data = fields.Char(
        help="The data of the table which gets parsed with the table variable."
    )
    table_data90 = fields.Char(
        string="Table data for the last 90 days",
        help="The data which gets displayed in the table for the timeframe 'Last 90 days'."
    )
    tile_ids = fields.One2many(
        "metro.dashboard.tile",
        "statistic_id"
    )
    tile_count = fields.Integer(
        string="Number of tiles referenced to this challenge",
        compute="_get_tile_count",
        store=True
    )
    empty = fields.Boolean(
        compute="_get_empty",
        store=True
    )
    empty90 = fields.Boolean(
        compute="_get_empty",
        store=True
    )
    dependencies = fields.Char(
        string="All dependencies",
        help="The modules which need to be installed to compute this Statistic"
    )
    uninstalled_dependencies = fields.Char(
        help="Please install those dependencies before you can use this Statistic"
    )
    dependency_count = fields.Integer(
        string = "# Dependencies",
        help="The number of dependencies this statistic has.",
        compute="_compute_dependency_count"
    )

    @api.model
    def create(self, vals):
        res = super(MetroDashboardStatistics, self).create(vals)

        # Error handling
        self.validate_form(res)

        if res.data_source == "python" and vals["compute_code"]:
            try:
                res.execute_code(False)
            except Exception as e:
                _logger.warn(e)
                return res
        elif res.data_source == "data" and vals["dataset_ids"]:
            res._extract_from_dataset()
            res.table_data = "[]"

        return res

    @api.multi
    def write(self, vals):
        res = super(MetroDashboardStatistics, self).write(vals)
        
        self.validate_form(self)

        # Computing value
        if ("compute_code" in vals or "data_source" in vals\
            or "use_timeframes" in vals or "visualisation" in vals)\
            and self.data_source == "python":
            try:
                self.execute_code(False)
            except Exception as e:
                _logger.warn(e)
                return res
        elif ("dataset_ids" in vals or "data_source" in vals or "dataset_keys_id" in vals)\
             and self.data_source == "data":
            self._extract_from_dataset()
            if not self.table_data:
                self.table_data = "[]"
        return res
    
    @api.one
    def validate_form(self, obj):
        # Throw an error when the data source is python but no code is provided
        if obj.data_source == "python" and not obj.compute_code:
            err = "Please insert code and provide a result variable inside it."
            raise UserError(err)
        # Throw an error when the data source is data but not dataset is provided
        elif obj.data_source == "data" and not obj.dataset_ids:
            err = "Please add at least one dataset to the statistic."
            raise UserError(err)
        # Throw an error when datasets are selected as data source but the visualisation
        # is number (datasets can only be displayed with charts)
        elif obj.data_source == "data" and obj.visualisation == "number":
            err = "You can't choose a dataset as data source and choose the visualisation number.\n"
            err += "Please choose another type of visualisation. Any kind of Chart will work with datasets."
            raise UserError(err)
        elif obj.visualisation == False:
            err = "Please choose a type of visualisation."
            raise UserError(err)

    @api.depends("tile_ids")
    def _get_tile_count(self):
        for r in self:
            r.tile_count = len(r.tile_ids)

    @api.depends("dataset_ids")
    def _get_dataset_count(self):
        for r in self:
            r.dataset_count = len(r.dataset_ids)

    @api.one
    @api.depends("dataset_keys_id", "value", "value90")
    def _get_keys(self):
        if self.value:
            val = json.loads(self.value or "{}")
            val90 = json.loads(self.value90 or "{}")
            self.keys = ""
            self.keys90 = ""
            if self.data_source == "data":
                if not self.visualisation == "number" and self.dataset_keys_id:
                    self.keys = self.dataset_keys_id.keys
                elif not self.visualisation == "number" and not self.dataset_keys_id:
                    self.keys = self.dataset_ids[0].keys
            else:
                keys = []
                keys90 = []
                if not self.visualisation == "number" and type(val) == dict:
                    keys = list(val.keys())
                    if self.use_timeframes:
                        keys90 = list(val90.keys())
                elif not self.visualisation == "number" and type(val) == list:
                    if len(val) >= 2:
                        keys = list(val[1].keys())
                    if self.use_timeframes:
                        if len(val90) >= 2:
                            keys90 = list(val90[1].keys())
                self.keys = list2KeysStr(keys)
                self.keys90 = list2KeysStr(keys90)

    @api.multi
    def _get_value_preview(self):
        for r in self:
            if r.value:
                r.value_preview = r.value[:150]
                if len(r.value) >= 150:
                    r.value_preview += "..."

    @api.one
    def update_value(self):
        if self.data_source == "python":
            self.execute_code(False)
        elif self.data_source == "data":
            self._extract_from_dataset()

    @api.model
    def update_all(self):
        objs = self.search([])
        for obj in objs:
            obj.update_value()

    @api.model
    def action_update(self):
        ids = self.env.context["active_ids"]
        records = self.browse(ids)
        for record in records:
            record.update_value()

    @api.one
    def _extract_from_dataset(self):
        datasets = []
        if self.dataset_count > 0:
            # Suffix gets set to the chosen dataset id
            # Better: Every dataset has its own suffix
            # if self.dataset_keys_id:
            #     self.suffix = self.dataset_keys_id.suffix
            for dataset in self.dataset_ids:
                datasets.append(dataset.name)
                data = {}
                for line in dataset.line_ids:
                    data[line.name] = line.value
                datasets.append(data)
            self.suffix = self._get_suffix_from_dataset(self.dataset_ids)
            self.value = json.dumps(datasets)
            self._get_keys()

    @api.one
    def execute_code(self, days_90 = False):
        self.check_dependencies()
        if self.uninstalled_dependencies:
            _logger.warn("Please install the following dependencies before calculting %s: %s", self.name, self.uninstalled_dependencies)
            self.value = ""
            self.value90 = ""
            self.keys = ""
            return
        if self.compute_code == False:
            err = "Please provide code if you want to calculate the value of your statistic with python code."
            err += "\nIf you want to use a dataset instead please choose the \"Use an existing dataset\" option in the \"Data Source\" field."
            raise UserError(err)
        last_day = datetime.now().date() + timedelta(days=1)
        first_day = last_day - timedelta(days=31)
        if days_90:
            first_day = first_day - timedelta(days=60)
        ctx = {
            "val": self.val,
            "env": self.env,
            "datetime": datetime,
            "timedelta": timedelta,
            "type": type,
            "sorted": sorted,
            "variable": self.env["metro.dashboard.variable"],
            "log": _logger.info,
            "load": json.loads,
            "parse": json.dumps,
            "list2KeysStr": list2KeysStr,
            "first_day": str(first_day),
            "last_day": str(last_day),
        }
        code = self.compute_code.strip()
        safe_eval(code, ctx, mode="exec", nocopy=True)
        
        res_var = ctx.get("result")
        if res_var == None:
            raise ValidationError("You need to provide a result variable.")
        result = None
        table = []
        try:
            if self.visualisation == "number":
                # If the number is an integer don't format the number so that is has 2 decimal places
                if int(res_var) == float(res_var):
                    result = int(res_var)
                # If it's a float value round it to two decimal places
                else:
                    result = float("{0:.2f}".format(float(res_var)))
            else:
                if type(res_var) != type({}) and type(res_var) != type([]):
                    raise TypeError
                result = json.dumps(res_var)
        except (ValueError, TypeError):
            err = "You have provided the wrong format for the result variable with the given type of visualisation.\n"
            if self.visualisation == "number":
                err += "A numerical value is required as type. But you've provided: " + str(type(res_var))
            else:
                err += "A dictionary is required as type. But you've provided: " + str(type(res_var))
            err += ".\nPlease look at the modules documentation for more information."
            raise ValidationError(err)
        except Exception as e:
            err = "An unkown error occured: " + str(e)
            raise ValidationError(err)

        if ctx.get("table"):
            table = json.dumps(ctx.get("table"))

        if ctx.get("keys"):
            keys = ctx.get("keys")
            if type(keys) == type([]):
                keys = list2KeysStr(keys)
            if days_90:
                self.keys90 = keys
            else:
                self.keys = keys

        if days_90:
            self.value90 = result
            self.table_data90 = table
        else:
            self.value = result
            self.table_data = table
        self._get_currency_symbol()

        if days_90 == False:
            if self.use_timeframes:
                self.execute_code(True)

            if not ctx.get("keys"):
                self._get_keys()
    
    @api.one
    def val(self):
        if self.visualisation == "number":
            return float(self.value)
        else:
            return json.loads(self.value)

    @api.multi
    def _get_currency_symbol(self):
        for r in self:
            r.symbol = self.env.user.company_id.currency_id.symbol

    @api.depends("value", "value90")
    def _get_empty(self):
        for r in self:
            if r.visualisation == "number":
                r.empty = False
                r.empty90 = False
                return
            res = json.loads(r.value or "{}")
            res90 = json.loads(r.value90 or "{}")

            if type(res) == type([]):
                r.empty = False
            else:
                r.empty = self._check_dict_empty(res)
            if type(res90) == type([]):
                r.empty90 = False
            else:
                r.empty90 = self._check_dict_empty(res90)

    def _check_dict_empty(self, d):
        if type(d) != type({}):
            return True
        if len(d) == 0:
            return True

        empty = True
        for key in d:
            if d[key] != 0:
                empty = False
        
        return empty

    def _get_suffix_from_dataset(self, dataset_ids):
        suffixes = {}
        for dataset in dataset_ids:
            suffixes[dataset.name] = dataset.suffix
        return json.dumps(suffixes)

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
