{
    'name': 'Print Barcodes from HHT',
    'version': '12.0.1.0.0',
    'summary': 'RUN-883',
    'description': """
        RUN-883: https://jira.metrosystems.net/browse/RUN-883,
    """,
    'author': ' Thore Baden, Hucke Media GmbH & Co. KG',
    'category': 'Metro',
    'depends': [
        'metro_barcode_print_community',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
}
