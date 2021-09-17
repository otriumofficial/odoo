# -*- coding: utf-8 -*-

from odoo.tests import common
from odoo.tools import float_compare


@common.at_install(False)
@common.post_install(True)
class TestDeliveryCost(common.TransactionCase):

    def setUp(self):
        super(TestDeliveryCost, self).setUp()
        self.SaleOrder = self.env['sale.order']
        self.SaleOrderLine = self.env['sale.order.line']
        self.AccountAccount = self.env['account.account']
        self.SaleConfigSetting = self.env['res.config.settings']
        self.Product = self.env['product.product']

        res_partner_category_0 = self.env['res.partner.category'].create(dict(
            name="Partner",
            color=1
        ))

        res_partner_category_5 = self.env['res.partner.category'].create(dict(
            name="Silver",
            color=3,
            parent_id=res_partner_category_0.id
        ))

        # self.partner_18 = self.env.ref('base.res_partner_18')
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

        self.pricelist = self.env.ref('product.list0')

        product_category_5 = self.env['product.category'].create(dict(
            parent_id=self.env.ref("product.product_category_1").id,
            name="Physical"
        ))

        product_attribute_1 = self.env['product.attribute'].create(dict(
            name="Memory"
        ))

        product_attribute_2 = self.env['product.attribute'].create(dict(
            name="Color"
        ))

        product_attribute_value_1 = self.env['product.attribute.value'].create(dict(
            name="16 GB",
            attribute_id=product_attribute_1.id
        ))

        product_attribute_value_3 = self.env['product.attribute.value'].create(dict(
            name="White",
            attribute_id=product_attribute_2.id
        ))

        self.product_uom_unit = self.env.ref('product.product_uom_unit')

        # self.product_4 = self.env.ref('product.product_product_4')
        self.product_4 = self.env['product.product'].create(dict(
            name="iPad Retina Display",
            categ_id=product_category_5.id,
            standard_price=500.0,
            list_price=750.0,
            type="consu",
            uom_id=self.product_uom_unit.id,
            uom_po_id=self.product_uom_unit.id,
            description_sale="7.9‑inch (diagonal) LED-backlit, 128Gb&#xA;Dual-core A5 with quad-core graphics&#xA;FaceTime HD Camera, 1.2 MP Photos",
            default_code="E-COM01",
            attribute_value_ids=[(6, 0, [product_attribute_value_1.id, product_attribute_value_3.id])]
        ))

        product_product_delivery_normal = self.env['product.product'].create(dict(
            name="Normal Delivery Charges",
            default_code="Delivery",
            type="service",
            categ_id=self.env.ref('product.product_category_all').id,
            sale_ok=False,
            purchase_ok=False,
            list_price=10.0
        ))

        # self.normal_delivery = self.env.ref('delivery.normal_delivery_carrier')
        self.normal_delivery = self.env['delivery.carrier'].create(dict(
            name="Normal Delivery Charges",
            fixed_price=10.0,
            sequence=3,
            delivery_type="fixed",
            product_id=product_product_delivery_normal.id
        ))

        res_partner_category_12 = self.env['res.partner.category'].create(dict(
            name="Office Supplies",
            color=8
        ))

        res_partner_category_13 = self.env['res.partner.category'].create(dict(
            name="Distributor",
            color=9
        ))

        # self.partner_4 = self.env.ref('base.res_partner_4')
        self.partner_4 = self.env['res.partner'].create(dict(
            name="Delta PC",
            category_id=[(6, 0, [res_partner_category_13.id, res_partner_category_12.id])],
            customer=False,
            supplier=True,
            is_company=True,
            city="Fremont",
            zip="94538",
            country_id=self.env.ref('base.us').id,
            state_id=self.env['res.country.state'].search([('code', 'ilike', 'ca')], limit=1).id,
            street="3661 Station Street",
            email="deltapc@yourcompany.example.com",
            phone="+1 510 340 2385",
            website="http://www.distribpc.com/"
        ))

        res_partner_category_8 = self.env['res.partner.category'].create(dict(
            name="Consultancy Services",
            color=5
        ))

        res_partner_category_14 = self.env['res.partner.category'].create(dict(
            name="Manufacturer",
            color=10
        ))

        res_partner_3 = self.env['res.partner'].create(dict(
            name="China Export",
            supplier=True,
            category_id=[(6, 0, [res_partner_category_8.id, res_partner_category_14.id])],
            is_company=True,
            city="Shanghai",
            zip="200000",
            country_id=self.env.ref('base.cn').id,
            street="52 Chop Suey street",
            email="chinaexport@yourcompany.example.com",
            phone="+86 21 6484 5671",
            website="http://www.chinaexport.com/"
        ))

        # self.partner_address_13 = self.env.ref('base.res_partner_address_13')
        self.partner_address_13 = self.env['res.partner'].create(dict(
            name="John M. Brown",
            parent_id=res_partner_3.id,
            function="Director",
            email="john.brown@epic.example.com"
        ))

        self.product_uom_hour = self.env.ref('product.product_uom_hour')
        self.account_data = self.env.ref('account.data_account_type_revenue')
        self.account_tag_operating = self.env.ref('account.account_tag_operating')

        product_category_3 = self.env['product.category'].create(dict(
            parent_id=self.env.ref('product.product_category_1').id,
            name="Services"
        ))

        # self.product_2 = self.env.ref('product.product_product_2')
        self.product_2 = self.env['product.product'].create(dict(
            name="Support Services",
            categ_id=product_category_3.id,
            standard_price=25.5,
            list_price=38.25,
            type="service",
            uom_id=self.env.ref('product.product_uom_hour').id,
            uom_po_id=self.env.ref('product.product_uom_hour').id,
            description="Example of product to invoice based on delivery."
        ))

        self.product_category = self.env.ref('product.product_category_all')
        self.free_delivery = self.env.ref('delivery.free_delivery_carrier')
        # as the tests hereunder assume all the prices in USD, we must ensure
        # that the company actually uses USD
        self.env.cr.execute(
            "UPDATE res_company SET currency_id = %s WHERE id = %s",
            [self.env.ref('base.USD').id, self.env.user.company_id.id])
        # FIXME: this is failing due to product.pricelist constraint
        # self.pricelist.currency_id = self.env.ref('base.USD').id

    def test_00_delivery_cost(self):
        # In order to test Carrier Cost
        # Create sales order with Normal Delivery Charges

        self.sale_normal_delivery_charges = self.SaleOrder.create({
            'partner_id': self.partner_18.id,
            'partner_invoice_id': self.partner_18.id,
            'partner_shipping_id': self.partner_18.id,
            'pricelist_id': self.pricelist.id,
            'order_line': [(0, 0, {
                'name': 'PC Assamble + 2GB RAM',
                'product_id': self.product_4.id,
                'product_uom_qty': 1,
                'product_uom': self.product_uom_unit.id,
                'price_unit': 750.00,
            })],
            'carrier_id': self.normal_delivery.id
        })
        # I add delivery cost in Sales order

        self.a_sale = self.AccountAccount.create({
            'code': 'X2020',
            'name': 'Product Sales - (test)',
            'user_type_id': self.account_data.id,
            'tag_ids': [(6, 0, {
                self.account_tag_operating.id
            })]
        })

        self.product_consultant = self.Product.create({
            'sale_ok': True,
            'list_price': 75.0,
            'standard_price': 30.0,
            'uom_id': self.product_uom_hour.id,
            'uom_po_id': self.product_uom_hour.id,
            'name': 'Service',
            'categ_id': self.product_category.id,
            'type': 'service'
        })

        # I add delivery cost in Sales order
        self.sale_normal_delivery_charges.get_delivery_price()
        self.sale_normal_delivery_charges.set_delivery_line()

        # I check sales order after added delivery cost

        line = self.SaleOrderLine.search([('order_id', '=', self.sale_normal_delivery_charges.id),
            ('product_id', '=', self.sale_normal_delivery_charges.carrier_id.product_id.id)])
        self.assertEqual(len(line), 1, "Delivery cost is not Added")

        self.assertEqual(float_compare(line.price_subtotal, 10.0, precision_digits=2), 0,
            "Delivery cost is not correspond.")

        # I confirm the sales order

        self.sale_normal_delivery_charges.action_confirm()

        # Create one more sales order with Free Delivery Charges

        self.delivery_sale_order_cost = self.SaleOrder.create({
            'partner_id': self.partner_4.id,
            'partner_invoice_id': self.partner_address_13.id,
            'partner_shipping_id': self.partner_address_13.id,
            'pricelist_id': self.pricelist.id,
            'order_line': [(0, 0, {
                'name': 'Service on demand',
                'product_id': self.product_consultant.id,
                'product_uom_qty': 24,
                'product_uom': self.product_uom_hour.id,
                'price_unit': 75.00,
            }), (0, 0, {
                'name': 'On Site Assistance',
                'product_id': self.product_2.id,
                'product_uom_qty': 30,
                'product_uom': self.product_uom_hour.id,
                'price_unit': 38.25,
            })],
            'carrier_id': self.free_delivery.id
        })

        # I add free delivery cost in Sales order
        self.delivery_sale_order_cost.get_delivery_price()
        self.delivery_sale_order_cost.set_delivery_line()

        # I check sales order after adding delivery cost
        line = self.SaleOrderLine.search([('order_id', '=', self.delivery_sale_order_cost.id),
            ('product_id', '=', self.delivery_sale_order_cost.carrier_id.product_id.id)])

        self.assertEqual(len(line), 1, "Delivery cost is not Added")
        self.assertEqual(float_compare(line.price_subtotal, 0, precision_digits=2), 0,
            "Delivery cost is not correspond.")

        # I set default delivery policy

        self.default_delivery_policy = self.SaleConfigSetting.create({})

        self.default_delivery_policy.execute()
