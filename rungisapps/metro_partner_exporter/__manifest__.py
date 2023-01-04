{
    'name': 'SAP Partner Exporter',
    'version': '12.0.1.1.2',
    'summary': 'SAP Partner Exporter',
    'category': 'custom',
    'author': 'Hucke Media GmbH & Co KG',
    'website': 'https://www.hucke-media.de',
    'license': 'LGPL-3',
    'depends': [
        'connector',
        'partner_fax',
        'base_iban',
        'base_address_extended'
    ],
    'data': [
        'views/res_partner.xml',
        'views/csv_export.xml',
        'views/csv_backend.xml',
        'data/data.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
