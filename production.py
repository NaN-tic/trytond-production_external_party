# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval
from trytond.transaction import Transaction

__all__ = ['Production', 'Move']
__metaclass__ = PoolMeta


class Production:
    __name__ = 'production'
    stock_owner = fields.Many2One('party.party', 'Stock Owner', states={
            'readonly': ~Eval('state').in_(['request', 'draft']),
            }, depends=['state'],
        help="The party whose stock can be used in this production instead of "
        "company's stock.")

    @fields.depends('stock_owner')
    def on_change_product(self):
        return super(Production, self).on_change_product()

    @fields.depends('stock_owner')
    def on_change_bom(self):
        return super(Production, self).on_change_bom()

    @fields.depends('stock_owner')
    def on_change_uom(self):
        return super(Production, self).on_change_uom()

    @fields.depends('stock_owner')
    def on_change_quantity(self):
        return super(Production, self).on_change_quantity()

    @fields.depends('stock_owner', methods=['bom'])
    def on_change_stock_owner(self):
        return self.explode_bom()

    @fields.depends('origin', 'stock_owner')
    def on_change_origin(self):
        pool = Pool()
        try:
            Sale = pool.get('sale.sale')
            SaleLine = pool.get('sale.line')
        except KeyError:
            Sale = None
            SaleLine = None
        try:
            res = super(Production, self).on_change_origin()
        except AttributeError:
            res = {}
        if hasattr(self, 'origin') and Sale:
            new_stock_owner = None
            if isinstance(self.origin, Sale):
                new_stock_owner = self.origin.party
            elif isinstance(self.origin, SaleLine):
                new_stock_owner = self.origin.sale.party
            if new_stock_owner != self.stock_owner:
                self.stock_owner = new_stock_owner
                if new_stock_owner:
                    res['stock_owner'] = new_stock_owner.id
                    res['stock_owner.rec_name'] = new_stock_owner.rec_name
                else:
                    res['stock_owner'] = None

                res.update(self.explode_bom())
        return res

    def _explode_move_values(self, from_location, to_location, company,
            bom_io, quantity):
        values = super(Production, self)._explode_move_values(from_location,
            to_location, company, bom_io, quantity)
        if bom_io.party_stock and self.stock_owner:
            values['party_used'] = self.stock_owner.id
            values['party_used.rec_name'] = self.stock_owner.rec_name
        return values

    def set_moves(self):
        # TODO: it will be better provide bom_input/output to _move()
        super(Production, self).set_moves()
        if not self.stock_owner or not self.bom:
            return

        todo_input_products = [i.product for i in self.bom.inputs
            if i.party_stock]
        if todo_input_products:
            for input_ in self.inputs:
                if input_.product in todo_input_products:
                    input_.party_used = self.stock_owner

        todo_output_products = [i.product for i in self.bom.outputs
            if i.party_stock]
        if todo_output_products:
            for output_ in self.outputs:
                if output_.product in todo_output_products:
                    output_.party_used = self.stock_owner


class Move:
    __name__ = 'stock.move'

    def get_party_to_check(self, name):
        with Transaction().set_context(_check_access=False):
            if self.production_input:
                return (self.production_input.stock_owner.id
                    if self.production_input.stock_owner else None)
            if self.production_output:
                return (self.production_output.stock_owner.id
                    if self.produciton_output.stock_owner else None)
        return super(Move, self).get_party_to_check(name)

    @classmethod
    def location_types_to_check_party(cls):
        res = super(Move, cls).location_types_to_check_party()
        if 'production' not in res:
            res.append('production')
        return res
