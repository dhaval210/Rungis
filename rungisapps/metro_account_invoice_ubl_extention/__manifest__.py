{
    'name': 'Account Invoice UBL Extention',
    'version': '12.0.1.8.25',
    'category': 'Accounting & Finance',
    'license': 'AGPL-3',
    'summary': 'Customization of Generate UBL XML For RUNGIS,RUN-965,RUN-1194',
    'description': '''
        Customization of Generate UBL XML For RUNGIS,
        https://jira.metrosystems.net/browse/RUN-965
        https://jira.metrosystems.net/browse/RUN-1194
    ''',
    'author': 'Hucke Media GmbH & Co. KG/IFE GmbH',
    'depends': [
        'account_e-invoice_generate',
        'account_payment_partner',
        'base_ubl_payment',
        'account_invoice_ubl',
        'account_tax_unece',
        'account_global_discount',
        'partner_identification_gln',
        "tis_catch_weight",
        "metro_softm_fields",
        "metro_rungis_invoice_report",
        "metro_lot_attributes"
    ],
    'data': [
        "views/res_config_settings.xml",

        'data/ubl_invoice_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'post_init_hook': 'set_xml_format_in_pdf_invoice_to_ubl',
    'uninstall_hook': 'remove_ubl_xml_format_in_pdf_invoice',
}
