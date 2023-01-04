# -*- coding: utf-8 -*-
{
    'name': 'Split picking',
    'summary': 'Split a picking into multiple picking.',
    'summary': "RUN-1022, RUN-1136",
    'description': """
                    RUN-1022 : Split of PICKs for large orders (capacity separation)
                    RUN-1136 : Splitted PICKs remain in same batch
                    """,
    'version': '12.0.1.0.3',
    'category': 'Inventory',
    'author': "Wipro Technologies - Abhay Singh Rathore",
    'website': 'https://wipro.com/',
    'depends': ['base', 'stock', 'sale','metro_rungis_batch_autoassign'],
    'data': ['views/views.xml'],
}
