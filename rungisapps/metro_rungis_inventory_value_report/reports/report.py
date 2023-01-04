from odoo import models, fields, api
import datetime
import operator as py_operator


def sumOfList(list, size):
   if (size == 0):
     return 0
   else:
     return list[size - 1] + sumOfList(list, size - 1)

OPERATORS = {
    '<': py_operator.lt,
    '>': py_operator.gt,
    '<=': py_operator.le,
    '>=': py_operator.ge,
    '=': py_operator.eq,
    '!=': py_operator.ne
}


class FinancialStockReport(models.AbstractModel):
    _name = 'report.metro_rungis_inventory_value_report.report_stock_value'

    @api.multi
    def _get_report_values(self, docids, data):
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
            main_total.update({
                warehouse_id.name : 0.0
            })

            for product in product_ids:

                # landed_cost_ids = self.env['stock.picking'].search([('date_done', '>=', data['form']['date_from']),
                #                                             ('date_done', '<=', data['form']['date_to'])])

            # if landed_cost_ids:
            #     landed_cost_product_ids = landed_cost_ids.mapped('move_ids_without_package').mapped('product_id')
            #     landed_cost_line_ids = landed_cost_ids.mapped('partner_id')\
            #         .mapped('landed_cost_line_ids').mapped('percentage')
            #     landed_cost_sum = sumOfList(landed_cost_line_ids, len(landed_cost_line_ids))
            #     landed_cost_product_ids = product


                # later_income_line_ids = landed_cost_ids.mapped('partner_id') \
                #     .mapped('later_income_line_ids').mapped('percentage')
                # later_income_sum = sumOfList(later_income_line_ids, len(later_income_line_ids))
                product_id = self.env['product.product'].with_context(warehouse=warehouse).browse(product.id)
                if product_id.qty_available > 0 or product_id.cw_qty_available > 0:
                    if warehouse_id.name not in main:
                        main.append(
                            warehouse_id.name
                        )
                if product_id.seller_ids:

                    landed_cost_line_ids = product_id.seller_ids[0].mapped('name').mapped('landed_cost_line_ids').mapped('percentage')
                    landed_cost_sum = sumOfList(landed_cost_line_ids, len(landed_cost_line_ids))
                    later_income_line_ids = product_id.seller_ids[0].mapped('name').mapped('later_income_line_ids').mapped('percentage')
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
                        sum_landed_cost = sum_landed_cost + (product_id.last_purchase_price * product_id.cw_qty_available * landed_cost_sum)/100
                        sum_later_income = sum_later_income + (product_id.last_purchase_price * product_id.cw_qty_available * later_income_sum)/100
                        sum_final_stock_value = sum_final_stock_value + (
                                product_id.cw_qty_available * product_id.last_purchase_price) \
                                            + (
                                                        product_id.last_purchase_price * product_id.cw_qty_available * landed_cost_sum / 100) + \
                                            (
                                                        product_id.last_purchase_price * product_id.cw_qty_available * later_income_sum / 100)

                    else:

                        sum_stock_amount = sum_stock_amount + product_id.qty_available * product_id.last_purchase_price
                        sum_stock_amount_cost = sum_stock_amount_cost + product_id.qty_available * product_id.standard_price
                        sum_landed_cost = sum_landed_cost + (product_id.last_purchase_price * product_id.qty_available * landed_cost_sum)/100
                        sum_later_income = sum_later_income + (product_id.last_purchase_price * product_id.cw_qty_available * later_income_sum)/100
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
                    main_total[warehouse_id.name] = sum_cw_qty_available

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
                            'sum_final_stock_value':  sum_final_stock_value,
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

        return vals
