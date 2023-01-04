from odoo.fields import Many2many
from odoo.tools import pycompat


class Many2manyNew(Many2many):

    def create(self, record_values):
        if not record_values:
            return
        model = record_values[0][0]
        comodel = model.env[self.comodel_name]

        # determine relation {id1: ids2}
        rel_ids = {record.id: set() for record, value in record_values}
        recs, vals_list = [], []

        def flush():
            # create lines in batch, and add new links to them
            if vals_list:
                lines = comodel.create(vals_list)
                for rec, line in pycompat.izip(recs, lines):
                    rel_ids[rec.id].add(line.id)
                recs.clear()
                vals_list.clear()

        for record, value in record_values:
            for act in value or []:
                if not isinstance(act, (list, tuple)) or not act:
                    continue
                if act[0] == 0:
                    recs.append(record)
                    vals_list.append(act[2])
                elif act[0] == 1:
                    comodel.browse(act[1]).write(act[2])
                elif act[0] == 2:
                    comodel.browse(act[1]).unlink()
                    rel_ids[record.id].discard(act[1])
                elif act[0] == 3:
                    rel_ids[record.id].discard(act[1])
                elif act[0] == 4:
                    rel_ids[record.id].add(act[1])
                elif act[0] in (5, 6):
                    if recs and recs[-1] == record:
                        flush()
                    rel_ids[record.id].clear()
                    if act[0] == 6:
                        rel_ids[record.id].update(act[2] if act[2] else [])

        flush()

        # add links
        links = [(id1, id2) for id1, ids2 in rel_ids.items() for id2 in ids2]
        if links:
            query = """
                INSERT INTO {rel} ({id1}, {id2}) VALUES {values}
            """.format(
                rel=self.relation, id1=self.column1, id2=self.column2,
                values=", ".join(["%s"] * len(links)),
            )
            model.env.cr.execute(query, tuple(links))


Many2many.create = Many2manyNew.create
