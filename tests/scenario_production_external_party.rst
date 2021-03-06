==================================
Production External Party Scenario
==================================

=============
General Setup
=============

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from proteus import config, Model, Wizard
    >>> from trytond.tests.tools import activate_modules
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> today = datetime.date.today()
    >>> yesterday = today - relativedelta(days=1)
    >>> tomorrow = today + relativedelta(days=1)

Create database::

    >>> config = config.set_trytond()
    >>> config.pool.test = True

Install production_external_party Module::

    >>> config = activate_modules('production_external_party')

Create company::

    >>> _ = create_company()
    >>> company = get_company()

Create parties::

    >>> Party = Model.get('party.party')
    >>> supplier = Party(name='Supplier')
    >>> supplier.save()
    >>> customer = Party(name='Customer')
    >>> customer.save()

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> ProductTemplate = Model.get('product.template')
    >>> Product = Model.get('product.product')
    >>> product = Product()
    >>> template = ProductTemplate()
    >>> template.producible = True
    >>> template.name = 'product'
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.list_price = Decimal(30)
    >>> template.cost_price = Decimal(20)
    >>> template.save()
    >>> product, = template.products

Create Components::

    >>> template1 = ProductTemplate()
    >>> template1.name = 'component 1'
    >>> template1.default_uom = unit
    >>> template1.type = 'goods'
    >>> template1.list_price = Decimal(5)
    >>> template1.cost_price = Decimal(1)
    >>> template1.save()
    >>> component1, = template1.products

    >>> meter, = ProductUom.find([('name', '=', 'Meter')])
    >>> template2 = ProductTemplate()
    >>> template2.name = 'component 2'
    >>> template2.default_uom = meter
    >>> template2.type = 'goods'
    >>> template2.list_price = Decimal(7)
    >>> template2.cost_price = Decimal(5)
    >>> template2.may_belong_to_party = True
    >>> template2.save()
    >>> component2, = template2.products

Create Bills of Material::

    >>> BOM = Model.get('production.bom')
    >>> BOMInput = Model.get('production.bom.input')
    >>> BOMOutput = Model.get('production.bom.output')
    >>> bom_party_stock = BOM(name='product')
    >>> input1 = BOMInput()
    >>> bom_party_stock.inputs.append(input1)
    >>> input1.product = component1
    >>> input1.quantity = 5
    >>> input2 = BOMInput()
    >>> bom_party_stock.inputs.append(input2)
    >>> input2.product = component2
    >>> input2.quantity = 2
    >>> input2.uom = meter
    >>> output = BOMOutput()
    >>> bom_party_stock.outputs.append(output)
    >>> output.product = product
    >>> output.quantity = 1
    >>> bom_party_stock.save()

    >>> for input in bom_party_stock.inputs:
    ...     if input.product == component1:
    ...         input.party_stock == False
    ...     elif input.product == component2:
    ...         input.party_stock == True
    True
    True
    >>> output, = bom_party_stock.outputs
    >>> output.party_stock == False
    True

    >>> output.party_stock = True
    >>> output.save()
    >>> bom_party_stock.reload()

    >>> bom_company_stock = BOM(BOM.copy([bom_party_stock.id], config.context)[0])
    >>> for input in bom_company_stock.inputs:
    ...     if input.product == component2:
    ...         input.party_stock = False
    >>> output, = bom_company_stock.outputs
    >>> output.party_stock = False
    >>> bom_company_stock.save()

    >>> ProductBom = Model.get('product.product-production.bom')
    >>> product.boms.append(ProductBom(bom=bom_company_stock))
    >>> product.boms.append(ProductBom(bom=bom_party_stock))
    >>> product.save()

Create an Inventory::

    >>> Inventory = Model.get('stock.inventory')
    >>> Location = Model.get('stock.location')
    >>> storage, = Location.find([
    ...         ('code', '=', 'STO'),
    ...         ])
    >>> inventory = Inventory()
    >>> inventory.date = yesterday
    >>> inventory.location = storage
    >>> inventory_line1 = inventory.lines.new()
    >>> inventory_line1.product = component1
    >>> inventory_line1.quantity = 20
    >>> inventory_line2 = inventory.lines.new()
    >>> inventory_line2.product = component2
    >>> inventory_line2.quantity = 4
    >>> inventory_line3 = inventory.lines.new()
    >>> inventory_line3.product = component2
    >>> inventory_line3.party = customer
    >>> inventory_line3.quantity = 2
    >>> inventory_line3 = inventory.lines.new()
    >>> inventory_line3.product = component2
    >>> inventory_line3.party = supplier
    >>> inventory_line3.quantity = 2
    >>> inventory.save()
    >>> Inventory.confirm([inventory.id], config.context)
    >>> inventory.state
    'done'

Check available quantities by product::

    >>> lcontext = config.context
    >>> config._context.update({'locations': [storage.id],
    ...             'stock_date_end': today})
    >>> component1 = Product(component1.id, config._context)
    >>> component1.quantity
    20.0
    >>> component2 = Product(component2.id, config._context)
    >>> component2.quantity
    8.0

Check available quantities of component 2 by party::

    >>> with config.set_context({'products': [component2.id]}):
    ...     customer.reload()
    ...     customer.quantity
    ...     supplier.reload()
    ...     supplier.quantity
    2.0
    2.0

Make a production using BoM with company stock::

    >>> Production = Model.get('production')
    >>> production = Production()
    >>> production.product = product
    >>> production.bom = bom_company_stock
    >>> production.stock_owner = customer
    >>> production.quantity = 1
    >>> sorted([(i.quantity, i.party_used) for i in production.inputs])
    [(2.0, None), (5.0, None)]
    >>> output, = production.outputs
    >>> output.quantity
    1.0
    >>> output.party_used
    >>> production.save()
    >>> production.click('wait')
    >>> production.click('assign_try')
    True
    >>> production.click('run')
    >>> production.click('done')

Check available quantities by product::

    >>> with config.set_context({'locations': [storage.id],
    ...             'stock_date_end': today}):
    ...     component1.reload()
    ...     component1.quantity
    ...     component2.reload()
    ...     component2.quantity
    15.0
    6.0
    >>> config._context.update({'locations': [storage.id],
    ...             'stock_date_end': today})
    >>> product = Product(product.id, config._context)
    >>> product.quantity
    1.0

Check available quantities by party::

    >>> with config.set_context({'products': [component2.id],
    ...             'stock_date_end': today}):
    ...     customer.reload()
    ...     customer.quantity
    ...     supplier.reload()
    ...     supplier.quantity
    2.0
    2.0

    >>> with config.set_context({'products': [product.id],
    ...             'stock_date_end': today}):
    ...     customer.reload()
    ...     customer.quantity
    2.0

Make a production using BoM with party stock::

    >>> Production = Model.get('production')
    >>> production = Production()
    >>> production.product = product
    >>> production.bom = bom_party_stock
    >>> production.stock_owner = customer
    >>> production.quantity = 1
    >>> production.save()
    >>> sorted([(i.quantity, i.party_used.rec_name if i.party_used else None) for i in production.inputs])
    [(2.0, 'Customer'), (5.0, None)]
    >>> output, = production.outputs
    >>> output.quantity
    1.0
    >>> output.party_used.rec_name
    'Customer'
    >>> production.click('wait')
    >>> production.reload()
    >>> production.click('assign_try')
    True
    >>> production.click('run')
    >>> production.click('done')

Check available quantities by product::

    >>> with config.set_context({'locations': [storage.id],
    ...             'stock_date_end': today}):
    ...     component1.reload()
    ...     component1.quantity
    ...     component2.reload()
    ...     component2.quantity
    ...     product.reload()
    ...     product.quantity
    10.0
    4.0
    2.0

Check available quantities by party::

    >>> with config.set_context({'products': [component2.id],
    ...             'stock_date_end': today}):
    ...     customer.reload()
    ...     customer.quantity
    ...     supplier.reload()
    ...     supplier.quantity
    1.0
    2.0

    >>> with config.set_context({'products': [product.id],
    ...             'stock_date_end': today}):
    ...     customer.reload()
    ...     customer.quantity
    1.0

Try to make another production with BoM using customer stock::

    >>> production = Production()
    >>> production.product = product
    >>> production.stock_owner = customer
    >>> production.bom = bom_party_stock
    >>> production.quantity = 1
    >>> production.save()
    >>> sorted([(i.quantity, i.party_used.rec_name if i.party_used else None)
    ...         for i in production.inputs])
    [(2.0, 'Customer'), (5.0, None)]
    >>> output, = production.outputs
    >>> output.quantity
    1.0
    >>> output.party_used.rec_name
    'Customer'
    >>> production.click('wait')
    >>> production.click('assign_try')
    False

Try to use stock from different party to move than production's stock owner::

    >>> production.click('draft')
    >>> for input in production.inputs:
    ...     if input.product == component2:
    ...         input.party_used = supplier
    >>> production.save()
    >>> production.stock_owner.rec_name
    'Customer'
    >>> sorted([(i.quantity, i.party_used.rec_name if i.party_used else None)
    ...         for i in production.inputs])
    [(2.0, 'Supplier'), (5.0, None)]
    >>> production.click('wait')
    >>> try:
    ...     production.click('assign_try')
    ... except Exception as e:
    ...     e.__class__.__name__
    'UserError'

Remove party from production inputs to use company's stock and produce::

    >>> production.click('draft')
    >>> for input in production.inputs:
    ...     if input.product == component2:
    ...         input.party_used = None
    >>> production.save()
    >>> production.click('wait')
    >>> production.click('assign_try')
    True
    >>> production.click('run')
    >>> production.click('done')

Check available quantities by product::

    >>> with config.set_context({'locations': [storage.id],
    ...             'stock_date_end': tomorrow}):
    ...     component1.reload()
    ...     component1.quantity
    ...     component2.reload()
    ...     component2.quantity
    ...     product.reload()
    ...     product.quantity
    5.0
    2.0
    3.0

Check available quantities by party::

    >>> with config.set_context({'products': [component2.id],
    ...             'stock_date_end': tomorrow}):
    ...     customer.reload()
    ...     customer.quantity
    ...     supplier.reload()
    ...     supplier.quantity
    2.0
    2.0

    >>> with config.set_context({'products': [product.id],
    ...             'stock_date_end': tomorrow}):
    ...     customer.reload()
    ...     customer.quantity
    2.0

Make another production with BoM using supplier stock::

    >>> production = Production()
    >>> production.product = product
    >>> production.stock_owner = customer
    >>> production.bom = bom_party_stock
    >>> production.quantity = 1
    >>> sorted([(i.quantity, i.party_used.rec_name if i.party_used else None)
    ...         for i in production.inputs])
    [(2.0, 'Customer'), (5.0, None)]
    >>> output, = production.outputs
    >>> output.quantity
    1.0
    >>> output.party_used.rec_name
    'Customer'
    >>> production.stock_owner = supplier
    >>> sorted([(i.quantity, i.party_used.rec_name if i.party_used else None)
    ...         for i in production.inputs])
    [(2.0, 'Supplier'), (5.0, None)]
    >>> output, = production.outputs
    >>> output.party_used.rec_name
    'Supplier'
    >>> production.click('wait')
    >>> production.click('assign_try')
    True
    >>> production.click('run')
    >>> production.click('done')

Check available quantities by product::

    >>> with config.set_context({'locations': [storage.id],
    ...             'stock_date_end': today}):
    ...     component1.reload()
    ...     component1.quantity
    ...     component2.reload()
    ...     component2.quantity
    ...     product.reload()
    ...     product.quantity
    0.0
    0.0
    4.0

Check available quantities by party::

    >>> with config.set_context({'products': [component2.id],
    ...             'stock_date_end': today}):
    ...     customer.reload()
    ...     customer.quantity
    ...     supplier.reload()
    ...     supplier.quantity
    2.0
    1.0

    >>> with config.set_context({'products': [product.id],
    ...             'stock_date_end': today}):
    ...     customer.reload()
    ...     customer.quantity
    ...     supplier.reload()
    ...     supplier.quantity
    2.0
    1.0
