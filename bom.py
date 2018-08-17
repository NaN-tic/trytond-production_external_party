# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta

__all__ = ['BOMInput', 'BOMOutput']



class BOMInput(metaclass=PoolMeta):
    __name__ = 'production.bom.input'
    party_stock = fields.Boolean('Party Stock',
        help='Use stock owned by party instead of company stock.')
    # TODO: add any domain or check to foce product has 'may_belong_to_party'
    # checked?

    @fields.depends('product')
    def on_change_product(self):
        super(BOMInput, self).on_change_product()
        if self.product and self.product.may_belong_to_party:
            self.party_stock = True


class BOMOutput(metaclass=PoolMeta):
    __name__ = 'production.bom.output'
    party_stock = fields.Boolean('Party Stock',
        help='Produce stock owned by party instead of by company.')

    @fields.depends('product')
    def on_change_product(self):
        super(BOMOutput, self).on_change_product()
        if self.product and self.product.may_belong_to_party:
            self.party_stock = True
