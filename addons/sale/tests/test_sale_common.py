# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from collections import OrderedDict
from odoo.addons.account.tests.account_test_classes import AccountingTestCase


class TestSale(AccountingTestCase):
    def setUp(self):
        super(TestSale, self).setUp()
        # some users
        group_manager = self.env.ref('sales_team.group_sale_manager')
        group_user = self.env.ref('sales_team.group_sale_salesman')
        self.manager = self.env['res.users'].create({
            'name': 'Andrew Manager',
            'login': 'manager',
            'email': 'a.m@example.com',
            'signature': '--\nAndreww',
            'notification_type': 'email',
            'groups_id': [(6, 0, [group_manager.id])]
        })
        self.user = self.env['res.users'].create({
            'name': 'Mark User',
            'login': 'user',
            'email': 'm.u@example.com',
            'signature': '--\nMark',
            'notification_type': 'email',
            'groups_id': [(6, 0, [group_user.id])]
        })
        # create quotation with differend kinds of products (all possible combinations)
        product_category_4 = self.env['product.category'].create(dict(
            parent_id=self.env.ref('product.product_category_1').id,
            name="Software"
        ))
        product_order_01 = self.env['product.product'].create(dict(
            name="Zed+ Antivirus",
            categ_id=product_category_4.id,
            standard_price=235.0,
            list_price=280.0,
            type="consu",
            uom_id=self.env.ref('product.product_uom_unit').id,
            uom_po_id=self.env.ref('product.product_uom_unit').id,
            default_code="PROD_ORDER"
        ))
        product_category_5 = self.env['product.category'].create(dict(
            parent_id=self.env.ref('product.product_category_1').id,
            name="Physical"
        ))
        service_delivery = self.env['product.product'].create(dict(
            name="Cost-plus Contract",
            categ_id=product_category_5.id,
            standard_price=200.0,
            list_price=180.0,
            type="service",
            uom_id=self.env.ref('product.product_uom_unit').id,
            uom_po_id=self.env.ref('product.product_uom_unit').id,
            default_code="SERV_DEL"
        ))
        product_category_3 = self.env['product.category'].create(dict(
            parent_id=self.env.ref('product.product_category_1').id,
            name="Services"
        ))
        service_order_01 = self.env['product.product'].create(dict(
            name="Prepaid Consulting",
            categ_id=product_category_3.id,
            standard_price=40,
            list_price=90,
            type="service",
            uom_id=self.env.ref('product.product_uom_hour').id,
            uom_po_id=self.env.ref('product.product_uom_hour').id,
            description="Example of product to invoice on order.",
            default_code="SERV_ORDER"
        ))
        product_delivery_01 = self.env['product.product'].create(dict(
            name="Switch, 24 ports",
            categ_id=product_category_5.id,
            standard_price=55.0,
            list_price=70.0,
            type="consu",
            uom_id=self.env.ref('product.product_uom_unit').id,
            uom_po_id=self.env.ref('product.product_uom_unit').id,
            default_code="PROD_DEL"
        ))
        self.products = OrderedDict([
            ('prod_order', product_order_01),
            ('serv_del', service_delivery),
            ('serv_order', service_order_01),
            ('prod_del', product_delivery_01),
        ])
        res_partner_category_13 = self.env['res.partner.category'].create(dict(
            name="Distributor",
            color=9
        ))
        res_partner_category_12 = self.env['res.partner.category'].create(dict(
            name="Office Supplies",
            color=8
        ))
        res_partner_1 = self.env['res.partner'].create(dict(
            name="ASUSTeK",
            category_id=[(6, 0, [res_partner_category_13.id, res_partner_category_12.id])],
            supplier=True,
            customer=False,
            is_company=True,
            city="Taipei",
            zip="106",
            country_id=self.env.ref('base.tw').id,
            street="1 Hong Kong street",
            email="asusteK@yourcompany.example.com",
            phone="(+886) (02) 4162 2023",
            website="http://www.asustek.com"
        ))
        self.partner = res_partner_1
