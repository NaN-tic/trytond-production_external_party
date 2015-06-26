# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .bom import *
from .production import *


def register():
    Pool.register(
        BOMInput,
        BOMOutput,
        Production,
        Move,
        module='production_external_party', type_='model')
