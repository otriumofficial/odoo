# -*- coding: utf-8 -*-

from odoo.addons.account.tests.account_test_classes import AccountingTestCase


class StockMoveInvoice(AccountingTestCase):

    def setUp(self):
        super(StockMoveInvoice, self).setUp()
        self.ProductProduct = self.env['product.product']
        self.SaleOrder = self.env['sale.order']
        self.AccountJournal = self.env['account.journal']

        res_partner_category_0 = self.env['res.partner.category'].create(dict(
            name="Partner",
            color=1
        ))

        res_partner_category_5 = self.env['res.partner.category'].create(dict(
            name="Silver",
            color=3,
            parent_id=res_partner_category_0.id
        ))
        res_partner_18 = self.env['res.partner'].create(dict(
            name="Think Big Systems",
            is_company=True,
            category_id=[(6, 0, [res_partner_category_5.id])],
            city="London",
            email="thinkbig@yourcompany.example.com",
            phone="+1 857 349 3049",
            country_id=self.env.ref('base.uk').id,
            street="89 Lingfield Tower",
            website="http://www.think-big.com"
        ))
        self.partner_18 = res_partner_18
        self.pricelist_id = self.env.ref('product.list0')
        product_category_5 = self.env['product.category'].create(dict(
            parent_id=self.env.ref('product.product_category_1').id,
            name="Physical"
        ))
        product_attribute_1 = self.env['product.attribute'].create(dict(
            name="Memory"
        ))
        product_attribute_value_1 = self.env['product.attribute.value'].create(dict(
            name="16 GB",
            attribute_id=product_attribute_1.id
        ))
        product_product_11 = self.env['product.product'].create(dict(
            name="iPod",
            categ_id=product_category_5.id,
            standard_price=14,
            list_price=16.50,
            type="consu",
            uom_id=self.env.ref('product.product_uom_unit').id,
            uom_po_id=self.env.ref('product.product_uom_unit').id,
            default_code="E-COM12",
            attribute_value_ids=[(6,0,[product_attribute_value_1.id])]
        ))
        self.product_11 = product_product_11
        product_icecream = self.env['product.product'].create(dict(
            default_code="001",
            name="Ice Cream",
            type="product",
            categ_id=self.env.ref('product.product_category_1').id,
            list_price=100.0,
            standard_price=70.0,
            weight=1.0,
            uom_id=self.env.ref('product.product_uom_kgm').id,
            uom_po_id=self.env.ref('product.product_uom_kgm').id,
            property_stock_inventory=self.env.ref('stock.location_inventory').id,
            description="Ice cream can be mass-produced and thus is widely available in developed parts of the world. Ice cream can be purchased in large cartons (vats and squrounds) from supermarkets and grocery stores, in smaller quantities from ice cream shops, convenience stores, and milk bars, and in individual servings from small carts or vans at public events."
        ))
        self.product_icecream = product_icecream
        self.product_uom_kgm = self.env.ref('product.product_uom_kgm')
        product_product_delivery_normal = self.env['product.product'].create(dict(
            default_code="Delivery",
            name="Normal Delivery Charges",
            type="service",
            categ_id=self.env.ref('product.product_category_all').id,
            list_price=10.0,
            sale_ok=False,
            purchase_ok=False
        ))
        normal_delivery_carrier = self.env['delivery.carrier'].create(dict(
            name="Normal Delivery Charges",
            fixed_price=10.0,
            sequence=3,
            delivery_type="fixed",
            product_id=product_product_delivery_normal.id
        ))
        self.normal_delivery = normal_delivery_carrier

    def test_01_delivery_stock_move(self):
        # Test if the stored fields of stock moves are computed with invoice before delivery flow
        # Set a weight on ipod 16GB
        self.product_11.write({
            'weight': 0.25,
        })

        self.sale_prepaid = self.SaleOrder.create({
            'partner_id': self.partner_18.id,
            'partner_invoice_id': self.partner_18.id,
            'partner_shipping_id': self.partner_18.id,
            'pricelist_id': self.pricelist_id.id,
            'order_line': [(0, 0, {
                'name': 'Ice Cream',
                'product_id': self.product_icecream.id,
                'product_uom_qty': 2,
                'product_uom': self.product_uom_kgm.id,
                'price_unit': 750.00,
            })],
            'carrier_id': self.normal_delivery.id
        })

        # I add delivery cost in Sales order
        self.sale_prepaid.get_delivery_price()
        self.sale_prepaid.set_delivery_line()

        # I confirm the SO.
        self.sale_prepaid.action_confirm()
        self.sale_prepaid.action_invoice_create()

        # I check that the invoice was created
        self.assertEqual(len(self.sale_prepaid.invoice_ids), 1, "Invoice not created.")

        # I confirm the invoice

        self.invoice = self.sale_prepaid.invoice_ids
        self.invoice.action_invoice_open()

        # I pay the invoice.
        self.invoice = self.sale_prepaid.invoice_ids
        self.invoice.action_invoice_open()
        self.journal = self.AccountJournal.search([('type', '=', 'cash'), ('company_id', '=', self.sale_prepaid.company_id.id)], limit=1)
        self.invoice.pay_and_reconcile(self.journal, self.invoice.amount_total)

        # Check the SO after paying the invoice
        self.assertNotEqual(self.sale_prepaid.invoice_count, 0, 'order not invoiced')
        self.assertTrue(self.sale_prepaid.invoice_status == 'invoiced', 'order is not invoiced')
        self.assertEqual(len(self.sale_prepaid.picking_ids), 1, 'pickings not generated')

        # Check the stock moves
        moves = self.sale_prepaid.picking_ids.move_lines
        self.assertEqual(moves[0].product_qty, 2, 'wrong product_qty')
        self.assertEqual(moves[0].weight, 2.0, 'wrong move weight')

        # Ship
        self.picking = self.sale_prepaid.picking_ids.action_done()
