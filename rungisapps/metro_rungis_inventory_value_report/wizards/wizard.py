from odoo import models, fields, api
import json
import io
from odoo.tools import date_utils
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


def sumOfList(list, size):
    if (size == 0):
        return 0
    else:
        return list[size - 1] + sumOfList(list, size - 1)


class InventoryReportWizard(models.TransientModel):
    _name = 'stock.report.wizard'

    warehouse_ids = fields.Many2many('stock.warehouse', string="Warehouses", required=True)
    categ_id = fields.Many2one('product.category', string="Category", required=True)
    product_id = fields.Many2many('product.product', string="Product")
    date_from = fields.Date(string="Start Date", default=fields.Date.context_today)
    date_to = fields.Date(string="End Date", default=fields.Date.context_today)
    is_all_warehouse = fields.Boolean(string="All Warehouses", default=True)

    @api.onchange('categ_id')
    def _onchange_categ_id(self):
        if self.categ_id:
            return {'domain': {'product_id': [('categ_id', '=', self.categ_id.id)]}}

    def print_pdf(self):
        if self.is_all_warehouse:
            warehouse_ids = self.env['stock.warehouse'].search([]).ids
        else:
            warehouse_ids = self.warehouse_ids.ids
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'date_from': self.date_from,
                'date_to': self.date_to,
                'product_id': self.product_id.ids,
                'categ_id': self.categ_id.id,
                'warehouse_ids': warehouse_ids,
            },
        }
        return self.env.ref('metro_rungis_inventory_value_report.action_financial_stock_report_pdf').report_action(self, data=data)

    def print_xlsx(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'product_id': self.product_id.ids,
            'categ_id': self.categ_id.id,
            'warehouse_ids': self.warehouse_ids.ids,
            }

        }
        return {
            'type': 'ir_actions_xlsx_download',
            'data': {'model': 'stock.report.wizard',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Financial Stock Report',
                     }
        }

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Report')

        bold = workbook.add_format({'bold': True, 'font_size': '10px', 'border': 1})
        date = workbook.add_format({'bold': True, 'font_size': '10px'})
        date_to = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '10px'})
        head = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '20px', 'border': 1})
        txt = workbook.add_format({'font_size': '10px', 'border': 1})
        type = workbook.add_format({'bold': True, 'font_size': '10px', 'border': 1})
        sheet.merge_range('C2:R3', 'FINANCIAL STOCK REPORT', head)
        sheet.write('C5', "FROM", date)
        sheet.write('C6', "TO", date)
        sheet.write('D5', data['form']['date_from'], date)
        sheet.write('D6', data['form']['date_to'], date)
        sheet.write('F5', "CATEGORY", date)
        sheet.write('G5', self.env['product.category'].browse(int(data['form']['categ_id'])).name, date)

        sheet.write('C7', 'PRODUCT', bold)
        sheet.write('D7', 'ARTICLE NO', bold)
        sheet.write('E7', 'CW/NON CW', bold)
        sheet.write('F7', 'CW UoM', bold)
        sheet.write('G7', 'QUANTITY AVAILABLE', bold)
        sheet.write('H7', 'CW QUANTITY AVAILABLE', bold)
        sheet.write('I7', 'STOCK WEIGHT', bold)
        sheet.write('J7', 'COST', bold)
        sheet.write('K7', 'LAST PURCHASE PRICE', bold)
        sheet.write('L7', 'STOCK AMOUNT(LPP)', bold)
        sheet.write('M7', 'STOCK AMOUNT(COST)', bold)
        sheet.write('N7', 'LANDED COST', bold)
        sheet.write('O7', 'LATER INCOME', bold)
        sheet.write('P7', 'FINAL STOCK VALUE(LPP)', bold)
        warehouse_ids = data['form']['warehouse_ids']
        categ_id = data['form']['categ_id']

        values = []

        if data['form']['product_id']:
            product_ids = self.env['product.product'].search([('id', 'in', data['form']['product_id']),
                                                              ('categ_id', '=', categ_id)])
        else:
            product_ids = self.env['product.product'].search([('categ_id', '=', categ_id)])
        main = []
        main_total = {}
        total_vals = {}
        wh_totals = {}
        tot_sum_qty_available = 0.0
        tot_sum_cw_qty_available = 0.0
        tot_sum_cost = 0.0
        tot_sum_stock_weight = 0.0
        tot_sum_last_purchase_price = 0.0
        tot_sum_stock_amount = 0.0
        tot_sum_stock_amount_cost = 0.0
        tot_sum_landed_cost = 0.0
        tot_sum_later_income = 0.0
        tot_sum_final_stock_value = 0.0
        for warehouse in warehouse_ids:
            warehouse_id = self.env['stock.warehouse'].browse(warehouse)
            sum_qty_available = 0.0
            sum_cw_qty_available = 0.0
            sum_cost = 0.0
            sum_stock_weight = 0.0
            sum_last_purchase_price = 0.0
            sum_stock_amount = 0.0
            sum_stock_amount_cost = 0.0
            sum_landed_cost = 0.0
            sum_later_income = 0.0
            sum_final_stock_value = 0.0
            main.append(
                warehouse_id.name
            )
            main_total.update({
                warehouse_id.name: 0.0
            })

            for product in product_ids:

                # landed_cost_ids = self.env['stock.picking'].search([('date_done', '>=', data['form']['date_from']),
                #                                                     ('date_done', '<=', data['form']['date_to'])])
                #
                # if landed_cost_ids:
                #     landed_cost_product_ids = landed_cost_ids.mapped('move_ids_without_package').mapped('product_id')
                #     landed_cost_line_ids = landed_cost_ids.mapped('partner_id') \
                #         .mapped('landed_cost_line_ids').mapped('percentage')
                #     landed_cost_sum = sumOfList(landed_cost_line_ids, len(landed_cost_line_ids))
                #
                #     later_income_line_ids = landed_cost_ids.mapped('partner_id') \
                #         .mapped('later_income_line_ids').mapped('percentage')
                #     later_income_sum = sumOfList(later_income_line_ids, len(later_income_line_ids))
                product_id = self.env['product.product'].with_context(warehouse=warehouse).browse(product.id)

                if product_id.seller_ids:
                    landed_cost_line_ids = product_id.seller_ids[0].mapped('name').mapped(
                        'landed_cost_line_ids').mapped('percentage')
                    landed_cost_sum = sumOfList(landed_cost_line_ids, len(landed_cost_line_ids))
                    later_income_line_ids = product_id.seller_ids[0].mapped('name').mapped(
                        'later_income_line_ids').mapped('percentage')
                    later_income_sum = sumOfList(later_income_line_ids, len(later_income_line_ids))
                    # if product_id in landed_cost_product_ids:
                    sum_qty_available = sum_qty_available + product_id.qty_available
                    sum_cw_qty_available = sum_cw_qty_available + product_id.cw_qty_available
                    sum_stock_weight = sum_stock_weight + product_id.weight * product_id.qty_available
                    sum_cost = sum_cost + product_id.standard_price
                    sum_last_purchase_price = sum_last_purchase_price + product_id.last_purchase_price


                    if product_id.catch_weight_ok:
                        sum_stock_amount = sum_stock_amount + product_id.cw_qty_available * product_id.last_purchase_price
                        sum_stock_amount_cost = sum_stock_amount_cost + product_id.cw_qty_available * product_id.standard_price
                        sum_landed_cost = sum_landed_cost + (
                                    product_id.last_purchase_price * product_id.cw_qty_available * landed_cost_sum) / 100
                        sum_later_income = sum_later_income + (
                                    product_id.last_purchase_price * product_id.cw_qty_available * later_income_sum) / 100
                        sum_final_stock_value = sum_final_stock_value + (
                                product_id.cw_qty_available * product_id.last_purchase_price) \
                                                + (
                                                        product_id.last_purchase_price * product_id.cw_qty_available * landed_cost_sum / 100) + \
                                                (
                                                        product_id.last_purchase_price * product_id.cw_qty_available * later_income_sum / 100)

                    else:
                        sum_stock_amount = sum_stock_amount + product_id.qty_available * product_id.last_purchase_price
                        sum_stock_amount_cost = sum_stock_amount_cost + product_id.qty_available * product_id.standard_price
                        sum_landed_cost = sum_landed_cost + (
                                    product_id.last_purchase_price * product_id.qty_available * landed_cost_sum) / 100
                        sum_later_income = sum_later_income + (
                                    product_id.last_purchase_price * product_id.cw_qty_available * later_income_sum) / 100
                        sum_final_stock_value = sum_final_stock_value + (
                                product_id.qty_available * product_id.last_purchase_price) \
                                                + (
                                                        product_id.last_purchase_price * product_id.qty_available * landed_cost_sum / 100) + \
                                                (
                                                        product_id.last_purchase_price * product_id.qty_available * later_income_sum / 100)


                    values.append({
                        'catch_weight': 'Catch Weight Product' if product_id.catch_weight_ok else 'Non Catch Weight Product',
                        'catch_weight_uom': product_id.cw_uom_id.name if product_id.catch_weight_ok else None,
                        'product_id': product_id.name,
                        'ref': product_id.default_code,
                        'warehouse': warehouse_id.name,
                        'virtual_available': product_id.virtual_available,
                        'qty_available': product_id.qty_available,
                        'cw_qty_available': product_id.cw_qty_available,
                        'qty_available_mh': product_id.qty_available_mh,
                        'uom_name': product_id.uom_name,
                        'cw_uom_name': product_id.cw_uom_name,
                        'stock_weight': product_id.weight * product_id.qty_available,
                        'weight_uom_id': product_id.weight_uom_id.name,
                        'standard_price': product_id.standard_price,
                        'purchase_price_base': product_id.purchase_price_base,
                        'last_purchase_price': product_id.last_purchase_price,

                    })
                    if product_id.catch_weight_ok:
                        values[-1].update({
                            'stock_amount': product_id.cw_qty_available * product_id.last_purchase_price,
                            'stock_amount_cost': product_id.cw_qty_available * product_id.standard_price,
                            'landed_cost': (
                                                       product_id.last_purchase_price * product_id.cw_qty_available * landed_cost_sum) / 100,
                            'later_income': (
                                                        product_id.last_purchase_price * product_id.cw_qty_available * later_income_sum) / 100,
                            'final_stock_value_lpp': (product_id.cw_qty_available * product_id.last_purchase_price) +
                                                     (
                                                                 product_id.last_purchase_price * product_id.cw_qty_available * landed_cost_sum) / 100 +
                                                     (
                                                                 product_id.last_purchase_price * product_id.cw_qty_available * later_income_sum) / 100,
                        })
                    else:
                        values[-1].update({
                            'stock_amount': product_id.qty_available * product_id.last_purchase_price,
                            'stock_amount_cost': product_id.qty_available * product_id.standard_price,
                            'landed_cost': (
                                                       product_id.last_purchase_price * product_id.qty_available * landed_cost_sum) / 100,
                            'later_income': (
                                                        product_id.last_purchase_price * product_id.qty_available * later_income_sum) / 100,
                            'final_stock_value_lpp': (product_id.qty_available * product_id.last_purchase_price) +
                                                     (
                                                                 product_id.last_purchase_price * product_id.qty_available * landed_cost_sum) / 100 +
                                                     (
                                                                 product_id.last_purchase_price * product_id.qty_available * later_income_sum) / 100,
                        })
                    main_total[warehouse_id.name] = sum_qty_available
                    total_vals.update({
                        warehouse_id.name: {
                            'sum_qty_available': sum_qty_available,
                            'sum_cw_qty_available': sum_cw_qty_available,
                            'sum_stock_weight': sum_stock_weight,
                            'sum_cost': sum_cost,
                            'sum_last_purchase_price': sum_last_purchase_price,
                            'sum_stock_amount': sum_stock_amount,
                            'sum_stock_amount_cost': sum_stock_amount_cost,
                            'sum_landed_cost': sum_landed_cost,
                            'sum_later_income': sum_later_income,
                            'sum_final_stock_value': sum_final_stock_value,
                        }
                    })
            tot_sum_qty_available = tot_sum_qty_available + sum_qty_available
            tot_sum_cw_qty_available = tot_sum_cw_qty_available + sum_cw_qty_available
            tot_sum_stock_weight = tot_sum_stock_weight + sum_stock_weight
            tot_sum_cost = tot_sum_cost + sum_cost
            tot_sum_last_purchase_price = tot_sum_last_purchase_price + sum_last_purchase_price
            tot_sum_stock_amount = tot_sum_stock_amount + sum_stock_amount
            tot_sum_stock_amount_cost = tot_sum_stock_amount_cost + sum_stock_amount_cost
            tot_sum_landed_cost = tot_sum_landed_cost + sum_landed_cost
            tot_sum_later_income = tot_sum_later_income + sum_later_income
            tot_sum_final_stock_value = tot_sum_final_stock_value + sum_final_stock_value
        wh_totals.update({
            'tot_sum_qty_available': tot_sum_qty_available,
            'tot_sum_cw_qty_available': tot_sum_cw_qty_available,
            'tot_sum_stock_weight': tot_sum_stock_weight,
            'tot_sum_cost': tot_sum_cost,
            'tot_sum_last_purchase_price': tot_sum_last_purchase_price,
            'tot_sum_stock_amount': tot_sum_stock_amount,
            'tot_sum_stock_amount_cost': tot_sum_stock_amount_cost,
            'tot_sum_landed_cost': tot_sum_landed_cost,
            'tot_sum_later_income': tot_sum_later_income,
            'tot_sum_final_stock_value': tot_sum_final_stock_value
        })

        vals = {
            'wh_totals': wh_totals,
            'main': main,
            'main_total': main_total,
            'total_vals': total_vals,
            'values': values,
            'date_from': data['form']['date_from'],
            'date_to': data['form']['date_to'],
            'data': data,
            'date_today': fields.Datetime.now(),
            'categ_id': self.env['product.category'].browse(int(data['form']['categ_id'])).name
        }
        if len(data['form']['product_id']) == 1:
            vals.update({
                'product_id': self.env['product.product'].browse(int(data['form']['product_id'][0])).name
            })

        row_num = 7
        col_num = 2
        for warehouse in vals['main']:
            row_num += 1
            sheet.merge_range(row_num, col_num, row_num, col_num + 13, warehouse, date)
            for data in vals['values']:
                if data['warehouse'] == warehouse:
                    row_num += 1
                    sheet.write(row_num, col_num, data['product_id'], txt)
                    sheet.write(row_num, col_num+1, data['ref'], txt)
                    sheet.write(row_num, col_num+2, data['catch_weight'], txt)
                    sheet.write(row_num, col_num+3, data['catch_weight_uom'], txt)
                    sheet.write(row_num, col_num+4, str(data['qty_available']) + ' ' + data['uom_name'], txt)
                    sheet.write(row_num, col_num+5, str(data['cw_qty_available']) + ' ' + data['cw_uom_name'], txt)
                    sheet.write(row_num, col_num+6, str(round(data['stock_weight'])) + ' ' + data['weight_uom_id'], txt)
                    sheet.write(row_num, col_num+7, data['standard_price'], txt)
                    sheet.write(row_num, col_num+8, data['last_purchase_price'], txt)
                    sheet.write(row_num, col_num+9, data['stock_amount'], txt)
                    sheet.write(row_num, col_num+10, data['stock_amount_cost'], txt)
                    sheet.write(row_num, col_num+11, data['landed_cost'], txt)
                    sheet.write(row_num, col_num+12, data['later_income'], txt)
                    sheet.write(row_num, col_num+13, data['final_stock_value_lpp'], txt)

            if total_vals:
                row_num += 1
                sheet.merge_range(row_num, col_num, row_num, col_num+3, "Total", bold)
                sheet.write(row_num, col_num+4, vals['total_vals'][warehouse]['sum_qty_available'], bold)
                sheet.write(row_num, col_num+5, vals['total_vals'][warehouse]['sum_cw_qty_available'], bold)
                sheet.write(row_num, col_num+6, round(vals['total_vals'][warehouse]['sum_stock_weight']), bold)
                sheet.write(row_num, col_num+7, vals['total_vals'][warehouse]['sum_cost'], bold)
                sheet.write(row_num, col_num+8, vals['total_vals'][warehouse]['sum_last_purchase_price'], bold)
                sheet.write(row_num, col_num+9, vals['total_vals'][warehouse]['sum_stock_amount'], bold)
                sheet.write(row_num, col_num+10, vals['total_vals'][warehouse]['sum_stock_amount_cost'], bold)
                sheet.write(row_num, col_num+11, vals['total_vals'][warehouse]['sum_landed_cost'], bold)
                sheet.write(row_num, col_num+12, vals['total_vals'][warehouse]['sum_later_income'], bold)
                sheet.write(row_num, col_num+13, vals['total_vals'][warehouse]['sum_final_stock_value'], bold)
        row_num += 2
        sheet.merge_range(row_num, col_num, row_num, col_num + 3, "Total", bold)
        sheet.write(row_num, col_num + 4, wh_totals['tot_sum_qty_available'], bold)
        sheet.write(row_num, col_num + 5, wh_totals['tot_sum_cw_qty_available'], bold)
        sheet.write(row_num, col_num + 6, round(wh_totals['tot_sum_stock_weight']), bold)
        sheet.write(row_num, col_num + 7, round(wh_totals['tot_sum_cost']), bold)
        sheet.write(row_num, col_num + 8, round(wh_totals['tot_sum_last_purchase_price']), bold)
        sheet.write(row_num, col_num + 9, round(wh_totals['tot_sum_stock_amount']), bold)
        sheet.write(row_num, col_num + 10, round(wh_totals['tot_sum_stock_amount_cost']), bold)
        sheet.write(row_num, col_num + 11, round(wh_totals['tot_sum_landed_cost']), bold)
        sheet.write(row_num, col_num + 12, round(wh_totals['tot_sum_later_income']), bold)
        sheet.write(row_num, col_num + 13, round(wh_totals['tot_sum_final_stock_value']), bold)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()


