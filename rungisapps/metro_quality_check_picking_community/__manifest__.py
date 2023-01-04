# -*- coding: utf-8 -*-
# Part of Nisu Technology See LICENSE file for full copyright and licensing details.
{
    'name': "Metro Quality Check Picking Odoo",
    'version': '1.24',
    'category': 'Warehouse',
    'summary': """Add new Tab Quality Check on Stock Picking""",
    'description': """
	  - This module was last updated on 15 February 2019
	  - Add new tab called Truck Quality Checks in stock.picking form
          - Add products configuration for truck QC in Inventory > Setting
          - Truck QC is a must before transferring stock into warehouse
          - QC results from stock.picking form will be passed on automatically to QC module
          - demo video https://drive.google.com/file/d/1YixhBTXum8Av1V0cKIqAiJumnRpYTyup/view
          - removed error message related to Ambient truck temperature
	  - EMO 520: Create new truck type called Chilled & Frozen (updated 11 January 2019)
  	  - EMO 547: Disable truck level QC on all IN operations except from PO (updated 11 January 2019)
	  - EMO 606: Remove vehicle door seal check from truck level QC (updated 11 January 2019)
	  - EMO 613: Change acceptable temperature for Frozen truck to -30.0 C to -16.0 C (updated 11 January 2019)
      - 25 January 2019: changed value of Truck QC to READ ONLY
      - EMO 795: changed value of chilled truck temperature to 0 - 6 degree cel (updated 2 February 2019)
      - Fixed feedback for READ only fields in Truck QC Check if picking is cancelled (updated 15 February 2019)
      - EMO-895, v1.18, stock_picking init function with_context(prefetch_fields=False) so stock.picking can be extended by other modules
      - EMO-842 : fixed module performance issue,when upgrading module(22aug2019),when installing module it automatically call all 
                compute function.So remove init function from stock_picking
        -RUN-104 :change 'quality' to 'sync_quality_control'
	 """,
    'author': "Nisu Technology,""Cybrosys for METRONOM GmbH",
    'website': "https://nisu.technology",
    'depends': [
        'sync_quality_control',
        'stock',
        'purchase',
        'purchase_stock'],
    'data': [
        # 'wizard/create_quality_wizard_view.xml',
        'views/stock_move_view.xml',
        'views/quality_view.xml',
        # 'views/res_company_view.xml',
        'views/stock_config_settings_views.xml',
    ],
    'application': False,
    'installable': True,
}
