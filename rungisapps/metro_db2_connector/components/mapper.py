from odoo.addons.component.core import AbstractComponent
import datetime


class DB2ImportMapper(AbstractComponent):
    _name = 'db2.import.mapper'
    _inherit = ['base.db2.connector', 'base.import.mapper']
    _usage = 'import.mapper'


class DB2ExportMapper(AbstractComponent):
    _name = 'db2.export.mapper'
    _inherit = ['base.db2.connector', 'base.export.mapper']
    _usage = 'export.mapper'


def normalize_datetime(field):
    """Change a invalid date which comes from DB2, if
    no real date is set to null for correct import to
    OpenERP"""

    def modifier(self, record, to_attr):
        if record[field] == '0000-00-00 00:00:00':
            return None
        modified_date = datetime.datetime.strptime(record[field], "%d.%m.%Y").strftime("%Y-%m-%d")
        return modified_date
    return modifier


class DB2ImportMapChild(AbstractComponent):
    """ :py:class:`MapChild` for the Imports """

    _inherit = 'base.map.child.import'
    _usage = 'import.map.child'

    def format_items(self, items_values):
        """ Format the values of the items mapped from the child Mappers.

        It can be overridden for instance to add the Odoo
        relationships commands ``(6, 0, [IDs])``, ...

        As instance, it can be modified to handle update of existing
        items: check if an 'id' has been defined by
        :py:meth:`get_item_values` then use the ``(1, ID, {values}``)
        command

        :param items_values: list of values for the items to create
        :type items_values: list

        """
        items = []
        for values in items_values:
            if 'id' in values:
                items += [(1, values['id'], values)]
            else:
                items += [(0, 0, values)]
        return items
        # return [(0, 0, values) for values in items_values]