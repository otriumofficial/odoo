# -*- coding: utf-8 -*-

from odoo.addons.account.tests.account_test_classes import AccountingTestCase
from odoo.exceptions import ValidationError

import time


class TestAccountInvoiceRounding(AccountingTestCase):

    def setUp(self):
        super(TestAccountInvoiceRounding, self).setUp()
        self.account_receivable = self.env['account.account'].search(
            [('user_type_id', '=', self.env.ref('account.data_account_type_receivable').id)], limit=1)
        self.account_revenue = self.env['account.account'].search(
            [('user_type_id', '=', self.env.ref('account.data_account_type_revenue').id)], limit=1)
        self.fixed_tax = self.env['account.tax'].create({
            'name': 'Test Tax',
            'amount': 0.0,
            'amount_type': 'fixed',
        })

    def create_cash_rounding(self, rounding, method, strategy):
        return self.env['account.cash.rounding'].create({
            'name': 'rounding ' + method,
            'rounding': rounding,
            'account_id': self.account_receivable.id,
            'strategy': strategy,
            'rounding_method': method,
        })

    def create_invoice(self, amount, cash_rounding_id, tax_amount=None):
        """ Returns an open invoice """
        res_partner_category_0 = self.env['res.partner.category'].create(dict(
            name="Partner",
            color=1,
        ))
        res_partner_category_7 = self.env['res.partner.category'].create(dict(
            name="IT Services",
            color=5,
            parent_id=res_partner_category_0.id
        ))
        res_partner_category_9 = self.env['res.partner.category'].create(dict(
            name="Components Buyer",
            color=6
        ))
        res_partner_2 = self.env['res.partner'].create(dict(
            name="Agrolait",
            category_id=[(6, 0, [res_partner_category_7.id, res_partner_category_9.id])],
            is_company=True,
            city="Wavre",
            zip="1300",
            country_id=self.env.ref('base.be').id,
            street="69 rue de Namur",
            email="agrolait@yourcompany.example.com",
            phone="+32 10 588 558",
            website="http://www.agrolait.com",
            property_payment_term_id=self.env.ref('account.account_payment_term_net').id
        ))
        invoice_id = self.env['account.invoice'].create({
            'partner_id': res_partner_2.id,
            'reference_type': 'none',
            'currency_id': self.env.ref('base.USD').id,
            'name': 'invoice test rounding',
            'account_id': self.account_receivable.id,
            'type': 'out_invoice',
            'date_invoice': time.strftime('%Y') + '-06-26',
        })
        if tax_amount:
            self.fixed_tax.amount = tax_amount

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

        # self.product_4 = self.env.ref('product.product_product_4')
        product_product_4 = self.env['product.product'].create(dict(
            name="iPad Retina Display",
            categ_id=product_category_5.id,
            standard_price=500.0,
            list_price=750.0,
            type="consu",
            uom_id=self.env.ref('product.product_uom_unit').id,
            uom_po_id=self.env.ref('product.product_uom_unit').id,
            description_sale="7.9‑inch (diagonal) LED-backlit, 128Gb&#xA;Dual-core A5 with quad-core graphics&#xA;FaceTime HD Camera, 1.2 MP Photos",
            default_code="E-COM01",
            attribute_value_ids=[(6, 0, [product_attribute_value_1.id, product_attribute_value_3.id])]
        ))

        self.env['account.invoice.line'].create({
            'product_id': product_product_4.id,
            'quantity': 1,
            'price_unit': amount,
            'invoice_id': invoice_id.id,
            'name': 'something',
            'account_id': self.account_revenue.id,
            'invoice_line_tax_ids': [(6, 0, [self.fixed_tax.id])] if tax_amount else None
        })
        # Create the tax_line_ids
        invoice_id._onchange_invoice_line_ids()

        # We need to set the cash_rounding_id after the _onchange_invoice_line_ids
        # to avoid a ValidationError from _check_cash_rounding because the onchange
        # are not well triggered in the tests.
        try:
            invoice_id.cash_rounding_id = cash_rounding_id
        except ValidationError:
            pass

        invoice_id._onchange_cash_rounding()
        invoice_id.action_invoice_open()
        return invoice_id

    def _check_invoice_rounding(self, inv, exp_lines_values, exp_tax_values=None):
        inv_lines = inv.invoice_line_ids
        self.assertEquals(len(inv_lines), len(exp_lines_values))
        for i in range(0, len(exp_lines_values)):
            self.assertEquals(inv_lines[i].price_unit, exp_lines_values[i])

        if exp_tax_values:
            tax_lines = inv.tax_line_ids
            self.assertEquals(len(tax_lines), len(exp_tax_values))
            for i in range(0, len(exp_tax_values)):
                self.assertEquals(tax_lines[i].amount_total, exp_tax_values[i])

    def test_rounding_add_invoice_line(self):
        self._check_invoice_rounding(
            self.create_invoice(100.2, self.create_cash_rounding(0.5, 'UP', 'add_invoice_line')),
            [100.2, 0.3]
        )
        self._check_invoice_rounding(
            self.create_invoice(100.9, self.create_cash_rounding(1.0, 'DOWN', 'add_invoice_line')),
            [100.9, -0.9]
        )
        self._check_invoice_rounding(
            self.create_invoice(100.5, self.create_cash_rounding(1.0, 'HALF-UP', 'add_invoice_line')),
            [100.5, 0.5]
        )

    def test_rounding_biggest_tax(self):
        self._check_invoice_rounding(
            self.create_invoice(100.2, self.create_cash_rounding(0.5, 'UP', 'biggest_tax'), 1.0),
            [100.2], [1.3]
        )
        self._check_invoice_rounding(
            self.create_invoice(100.9, self.create_cash_rounding(1.0, 'DOWN', 'biggest_tax'), 2.0),
            [100.9], [1.1]
        )
        self._check_invoice_rounding(
            self.create_invoice(100.5, self.create_cash_rounding(1.0, 'HALF-UP', 'biggest_tax'), 1.0),
            [100.5], [1.5]
        )
