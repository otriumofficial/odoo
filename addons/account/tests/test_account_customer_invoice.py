from odoo.addons.account.tests.account_test_users import AccountTestUsers
import datetime


class TestAccountCustomerInvoice(AccountTestUsers):

    def test_customer_invoice(self):
        # I will create bank detail with using manager access rights
        # because account manager can only create bank details.
        self.res_partner_bank_0 = self.env['res.partner.bank'].sudo(self.account_manager.id).create(dict(
            acc_type='bank',
            company_id=self.main_company.id,
            partner_id=self.main_partner.id,
            acc_number='123456789',
            bank_id=self.main_bank.id,
        ))

        # Test with that user which have rights to make Invoicing and payment and who is accountant.
        # Create a customer invoice
        self.account_invoice_obj = self.env['account.invoice']
        account_payment_term_advance = self.env['account.payment.term'].create(dict(
            name="30% Advance End of Following Month",
            note="Payment terms: 30% Advance End of Following Month",
            line_ids=[
                (5, 0),
                (0, 0, {'value': 'percent', 'value_amount': 30.0, 'sequence': 400, 'days': 0, 'option': 'day_after_invoice_date'}),
                (0, 0, {'value': 'balance', 'value_amount': 0.0, 'sequence': 500, 'days': 0, 'option': 'last_day_following_month'})
            ]
        ))
        self.payment_term = account_payment_term_advance
        self.journalrec = self.env['account.journal'].search([('type', '=', 'sale')])[0]
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
        self.partner3 = res_partner_3
        account_user_type = self.env.ref('account.data_account_type_receivable')
        self.ova = self.env['account.account'].search([('user_type_id', '=', self.env.ref('account.data_account_type_current_assets').id)], limit=1)

        #only adviser can create an account
        self.account_rec1_id = self.account_model.sudo(self.account_manager.id).create(dict(
            code="cust_acc",
            name="customer account",
            user_type_id=account_user_type.id,
            reconcile=True,
        ))

        product_category_5 = self.env['product.category'].create(dict(
            parent_id=self.env.ref('product.product_category_1').id,
            name="Physical"
        ))
        product_product_5 = self.env['product.product'].create(dict(
            name="Custom Computer (kit)",
            categ_id=product_category_5.id,
            standard_price=600.0,
            list_price=147.0,
            type="consu",
            uom_id=self.env.ref('product.product_uom_unit').id,
            uom_po_id=self.env.ref('product.product_uom_unit').id,
            description="Custom computer shipped in kit.",
            default_code="E-COM06"
        ))

        invoice_line_data = [
            (0, 0,
                {
                    'product_id': product_product_5.id,
                    'quantity': 10.0,
                    'account_id': self.env['account.account'].search([('user_type_id', '=', self.env.ref('account.data_account_type_revenue').id)], limit=1).id,
                    'name': 'product test 5',
                    'price_unit': 100.00,
                }
             )
        ]

        self.account_invoice_customer0 = self.account_invoice_obj.sudo(self.account_user.id).create(dict(
            name="Test Customer Invoice",
            reference_type="none",
            payment_term_id=self.payment_term.id,
            journal_id=self.journalrec.id,
            partner_id=self.partner3.id,
            account_id=self.account_rec1_id.id,
            invoice_line_ids=invoice_line_data
        ))

        # I manually assign tax on invoice
        invoice_tax_line = {
            'name': 'Test Tax for Customer Invoice',
            'manual': 1,
            'amount': 9050,
            'account_id': self.ova.id,
            'invoice_id': self.account_invoice_customer0.id,
        }
        tax = self.env['account.invoice.tax'].create(invoice_tax_line)
        assert tax, "Tax has not been assigned correctly"

        total_before_confirm = self.partner3.total_invoiced

        # I check that Initially customer invoice is in the "Draft" state
        self.assertEquals(self.account_invoice_customer0.state, 'draft')

        # I check that there is no move attached to the invoice
        self.assertEquals(len(self.account_invoice_customer0.move_id), 0)

        # I validate invoice by creating on
        self.account_invoice_customer0.action_invoice_open()

        # I check that the invoice state is "Open"
        self.assertEquals(self.account_invoice_customer0.state, 'open')

        # I check that now there is a move attached to the invoice
        assert self.account_invoice_customer0.move_id, "Move not created for open invoice"

        # I totally pay the Invoice
        self.account_invoice_customer0.pay_and_reconcile(self.env['account.journal'].search([('type', '=', 'bank')], limit=1), 10050.0)

        # I verify that invoice is now in Paid state
        assert (self.account_invoice_customer0.state == 'paid'), "Invoice is not in Paid state"

        total_after_confirm = self.partner3.total_invoiced
        self.assertEquals(total_after_confirm - total_before_confirm, self.account_invoice_customer0.amount_untaxed_signed)

        # I created a credit note Using Add Credit Note Button
        invoice_refund_obj = self.env['account.invoice.refund']
        self.account_invoice_refund_0 = invoice_refund_obj.create(dict(
            description='Credit Note for China Export',
            date=datetime.date.today(),
            filter_refund='refund'
        ))

        # I clicked on Add Credit Note button.
        self.account_invoice_refund_0.invoice_refund()

    def test_customer_invoice_tax(self):

        self.env.user.company_id.tax_calculation_rounding_method = 'round_globally'

        account_payment_term_advance = self.env['account.payment.term'].create(dict(
            name="30% Advance End of Following Month",
            note="Payment terms: 30% Advance End of Following Month",
            line_ids=[
                (5, 0),
                (0, 0, {'value': 'percent', 'value_amount': 30.0, 'sequence': 400, 'days': 0, 'option': 'day_after_invoice_date'}),
                (0, 0, {'value': 'balance', 'value_amount': 0.0, 'sequence': 500, 'days': 0, 'option': 'last_day_following_month'})
            ]
        ))
        payment_term = account_payment_term_advance
        journalrec = self.env['account.journal'].search([('type', '=', 'sale')])[0]
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
        partner3 = res_partner_3
        account_id = self.env['account.account'].search([('user_type_id', '=', self.env.ref('account.data_account_type_revenue').id)], limit=1).id

        tax = self.env['account.tax'].create({
            'name': 'Tax 15.0',
            'amount': 15.0,
            'amount_type': 'percent',
            'type_tax_use': 'sale',
        })

        product_category_3 = self.env['product.category'].create(dict(
            parent_id=self.env.ref('product.product_category_1').id,
            name="Services"
        ))
        product_product_1 = self.env['product.product'].create(dict(
            name="GAP Analysis Service",
            categ_id=product_category_3.id,
            standard_price=20.5,
            list_price=30.75,
            type="service",
            uom_id=self.env.ref('product.product_uom_hour').id,
            uom_po_id=self.env.ref('product.product_uom_hour').id,
            description="Example of products to invoice based on delivery.",
            invoice_policy="delivery"
        ))
        product_product_2 = self.env['product.product'].create(dict(
            name="Support Service",
            categ_id=product_category_3.id,
            standard_price=25.5,
            list_price=38.25,
            type="service",
            uom_id=self.env.ref('product.product_uom_hour').id,
            uom_po_id=self.env.ref('product.product_uom_hour').id,
            description="Example of product to invoice based on delivery.",
            invoice_policy="delivery"
        ))
        product_category_5 = self.env['product.category'].create(dict(
            parent_id=self.env.ref('product.product_category_1').id,
            name="Physical"
        ))
        product_product_3 = self.env['product.product'].create(dict(
            name="Computer SC234",
            categ_id=product_category_5.id,
            standard_price=450.0,
            list_price=300.0,
            type="consu",
            uom_id=self.env.ref('product.product_uom_unit').id,
            uom_po_id=self.env.ref('product.product_uom_unit').id,
            description_sale="""17" LCD Monitor&#xA;Processor AMD 8-Core""",
            default_code="PCSC234",
            invoice_policy="delivery"
        ))

        invoice_line_data = [
            (0, 0,
                {
                    'product_id': product_product_1.id,
                    'quantity': 40.0,
                    'account_id': account_id,
                    'name': 'product test 1',
                    'discount' : 10.00,
                    'price_unit': 2.27,
                    'invoice_line_tax_ids': [(6, 0, [tax.id])],
                }
             ),
              (0, 0,
                {
                    'product_id': product_product_2.id,
                    'quantity': 21.0,
                    'account_id': self.env['account.account'].search([('user_type_id', '=', self.env.ref('account.data_account_type_revenue').id)], limit=1).id,
                    'name': 'product test 2',
                    'discount' : 10.00,
                    'price_unit': 2.77,
                    'invoice_line_tax_ids': [(6, 0, [tax.id])],
                }
             ),
             (0, 0,
                {
                    'product_id': product_product_3.id,
                    'quantity': 21.0,
                    'account_id': self.env['account.account'].search([('user_type_id', '=', self.env.ref('account.data_account_type_revenue').id)], limit=1).id,
                    'name': 'product test 3',
                    'discount' : 10.00,
                    'price_unit': 2.77,
                    'invoice_line_tax_ids': [(6, 0, [tax.id])],
                }
             )
        ]

        invoice = self.env['account.invoice'].create(dict(
            name="Test Customer Invoice",
            reference_type="none",
            payment_term_id=payment_term.id,
            journal_id=journalrec.id,
            partner_id=partner3.id,
            invoice_line_ids=invoice_line_data
        ))

        self.assertEquals(invoice.amount_untaxed, sum([x.base for x in invoice.tax_line_ids]))

    def test_customer_invoice_tax_refund(self):
        company = self.env.user.company_id
        tax_account = self.env['account.account'].create({
            'name': 'TAX',
            'code': 'TAX',
            'user_type_id': self.env.ref('account.data_account_type_current_assets').id,
            'company_id': company.id,
        })

        tax_refund_account = self.env['account.account'].create({
            'name': 'TAX_REFUND',
            'code': 'TAX_R',
            'user_type_id': self.env.ref('account.data_account_type_current_assets').id,
            'company_id': company.id,
        })

        journalrec = self.env['account.journal'].search([('type', '=', 'sale')])[0]
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
        partner3 = res_partner_3
        account_id = self.env['account.account'].search([('user_type_id', '=', self.env.ref('account.data_account_type_revenue').id)], limit=1).id

        tax = self.env['account.tax'].create({
            'name': 'Tax 15.0',
            'amount': 15.0,
            'amount_type': 'percent',
            'type_tax_use': 'sale',
            'account_id': tax_account.id,
            'refund_account_id': tax_refund_account.id
        })

        product_category_3 = self.env['product.category'].create(dict(
            parent_id=self.env.ref('product.product_category_1').id,
            name="Services"
        ))
        product_product_1 = self.env['product.product'].create(dict(
            name="GAP Analysis Service",
            categ_id=product_category_3.id,
            standard_price=20.5,
            list_price=30.75,
            type="service",
            uom_id=self.env.ref('product.product_uom_hour').id,
            uom_po_id=self.env.ref('product.product_uom_hour').id,
            description="Example of products to invoice based on delivery.",
            invoice_policy="delivery"
        ))

        invoice_line_data = [
            (0, 0,
                {
                    'product_id': product_product_1.id,
                    'quantity': 40.0,
                    'account_id': account_id,
                    'name': 'product test 1',
                    'discount': 10.00,
                    'price_unit': 2.27,
                    'invoice_line_tax_ids': [(6, 0, [tax.id])],
                }
             )]

        invoice = self.env['account.invoice'].create(dict(
            name="Test Customer Invoice",
            reference_type="none",
            journal_id=journalrec.id,
            partner_id=partner3.id,
            invoice_line_ids=invoice_line_data
        ))

        invoice.action_invoice_open()

        refund = invoice.refund()
        self.assertEqual(invoice.tax_line_ids.mapped('account_id'), tax_account)
        self.assertEqual(refund.tax_line_ids.mapped('account_id'), tax_refund_account)
