{
    'name': 'Metro Rungis Views',
    'version': '12.0.1.0.54',
    'summary': ' RUN-541,RUN-358, RUN-709, RUN-662, RUN-731, RUN-845, RUN-846, RUN-858, RUN-907, RUN-934, RUN-933, RUN-936, RUN-888, RUN-877, RUN_1025, RUN-1036, RUN-603, RUN-1056, RUN-1009, RUN-1038, RUN-1071, RUN-1080, RUN-1123, RUN-1242,RUN-1244,1297,RUN-1312, RUN-1321',
    'description': """
                    RUN-541:https://jira.metrosystems.net/browse/RUN-541
                    RUN-358:https://jira.metrosystems.net/browse/RUN-358
                    RUN-709:https://jira.metrosystems.net/browse/RUN-709
                    RUN-662:https://jira.metrosystems.net/browse/RUN-662
                    RUN-731:https://jira.metrosystems.net/browse/RUN-731
                    RUN-845:https://jira.metrosystems.net/browse/RUN-845
                    RUN-846:https://jira.metrosystems.net/browse/RUN-846
                    RUN-858:https://jira.metrosystems.net/browse/RUN-858
                    RUN-907:https://jira.metrosystems.net/browse/RUN-907
                    RUN-934:https://jira.metrosystems.net/browse/RUN-934
                    RUN-933:https://jira.metrosystems.net/browse/RUN-933
                    RUN-936:https://jira.metrosystems.net/browse/RUN-936
                    RUN-936:https://jira.metrosystems.net/browse/RUN-888
                    RUN-877:https://jira.metrosystems.net/browse/RUN-877
                    RUN-1025:https://jira.metrosystems.net/browse/RUN-1025
                    RUN-1026:https://jira.metrosystems.net/browse/RUN-1026
                    RUN-1036:https://jira.metrosystems.net/browse/RUN-1036
                    RUN-603:https://jira.metrosystems.net/browse/RUN-603
                    RUN-1056:https://jira.metrosystems.net/browse/RUN-1056
                    RUN-1009:https://jira.metrosystems.net/browse/RUN-1009
                    RUN-1038:https://jira.metrosystems.net/browse/RUN-1038
                    RUN-1071:https://jira.metrosystems.net/browse/RUN-1071
                    RUN-1080:https://jira.metrosystems.net/browse/RUN-1080
                    RUN-1123:https://jira.metrosystems.net/browse/RUN-1123
                    RUN-1123:https://jira.metrosystems.net/browse/RUN-1160
                    RUN-1244:https://jira.metrosystems.net/browse/RUN-1244
                    RUN-1242:https://jira.metrosystems.net/browse/RUN-1242
                    RUN-1297:https://jira.metrosystems.net/browse/RUN-1297
                    RUN-1312:https://jira.metrosystems.net/browse/RUN-1312
                    RUN-1321:https://jira.metrosystems.net/browse/RUN-1321
                    """,
    'author': ' Cybrosys for METRONOM GmbH',
    'category': 'warehouse',
    'depends': [
        'base_address_extended',
        'metro_partner_exporter',
        'stock',
        'stock_landed_costs',
        'product_multi_category',
        'metro_studio_customizations',
        'product_fao_fishing',
        'stock_no_negative',
        'metro_putaway_strategy',
        'tis_cw_average_qty',
        'mrp',
        'sale',
        'product_expiry',
        'product_logistics_uom',
        'metro_split_picking',
        'product_dimension',
        'metro_buying_potential',
        'metro_auto_set_transporter',
        'partner_fax',
        'metro_min_amount_so',
        'base_global_discount',
        'metro_purchase_schedule',
        'purchase_discount',
        'purchase_triple_discount',
        'metro_lefo',
        'account_payment_partner',
        'purchase',
        'product_brand',
        'metro_softm_fields',
        'tis_catch_weight',
        'metro_db2_connector',
        'metro_rungis_product_margin'
    ],
    "data": [
        'views/stock_production_lot.xml',
        'views/product.xml',
        'views/res_partner.xml',
        'views/sale_order.xml',
        'views/stock_picking.xml',
        'views/stock_picking_type.xml',
        'views/stock_move_view.xml',
        'views/stock_move_line_view.xml',
        'views/account_invoice_view.xml',
        'views/purchase_order_view.xml',
        'data/po_follower_channel_parameter.xml',
        'security/security.xml',
        'security/ir.model.access.csv'

    ],
    'license': 'LGPL-3',
    'installable': True,
}
