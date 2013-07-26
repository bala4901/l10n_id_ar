# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from osv import fields, osv
from tools.translate import _

class wizard_multi_charts_accounts(osv.osv_memory):

    _name='wizard.multi.charts.accounts'
    _inherit = 'wizard.multi.charts.accounts'

    _columns = {
        'currency_use_ids': fields.many2many(string='Currency', obj='res.currency', rel='l10n_curency_wizard_rel', id1='wizard_id', id2='currency_id', required=True),
        'bank_account_ids': fields.one2many(obj='account.set_bank_account', fields_id='wizard_id', string='Set Bank Account'),
        'cash_account_ids': fields.one2many(obj='account.set_cash_account', fields_id='wizard_id', string='Set Cash Account'),
    }

    def default_get(self, cr, uid, fields, context=None):
        res = super(wizard_multi_charts_accounts, self).default_get(cr, uid, fields, context=context)
        tax_templ_obj = self.pool.get('account.tax.template')

        if 'bank_accounts_id' in fields:
            res.update({'bank_accounts_id': [{'acc_name': _('Cash'), 'account_type': 'cash'},{'acc_name': _('Bank'), 'account_type': 'bank'}]})
        if 'company_id' in fields:
            res.update({'company_id': self.pool.get('res.users').browse(cr, uid, [uid], context=context)[0].company_id.id})
        if 'currency_id' in fields:
            company_id = res.get('company_id') or False
            if company_id:
                company_obj = self.pool.get('res.company')
                country_id = company_obj.browse(cr, uid, company_id, context=context).country_id.id
                currency_id = company_obj.on_change_country(cr, uid, company_id, country_id, context=context)['value']['currency_id']
                res.update({'currency_id': currency_id})

        ids = self.pool.get('account.chart.template').search(cr, uid, [('visible', '=', True),('name', '=', 'Basic Indonesian Chart of Account')], context=context)
        if ids:
            if 'chart_template_id' in fields:
                res.update({'only_one_chart_template': len(ids) == 1, 'chart_template_id': ids[0]})
            if 'sale_tax' in fields:
                sale_tax_ids = tax_templ_obj.search(cr, uid, [("chart_template_id"
                                              , "=", ids[0]), ('type_tax_use', 'in', ('sale','all'))], order="sequence")
                res.update({'sale_tax': sale_tax_ids and sale_tax_ids[0] or False})
            if 'purchase_tax' in fields:
                purchase_tax_ids = tax_templ_obj.search(cr, uid, [("chart_template_id"
                                          , "=", ids[0]), ('type_tax_use', 'in', ('purchase','all'))], order="sequence")
                res.update({'purchase_tax': purchase_tax_ids and purchase_tax_ids[0] or False})
        res.update({
            'purchase_tax_rate': 10.0,
            'sale_tax_rate': 10.0,
        })
        return res

    def _load_template(self, cr, uid, template_id, company_id, code_digits=None, obj_wizard=None, account_ref=None, taxes_ref=None, tax_code_ref=None, context=None):
        '''
        This function generates all the objects from the templates

        :param template_id: id of the chart template to load
        :param company_id: id of the company the wizard is running for
        :param code_digits: integer that depicts the number of digits the accounts code should have in the COA
        :param obj_wizard: the current wizard for generating the COA from the templates
        :param acc_ref: Mapping between ids of account templates and real accounts created from them
        :param taxes_ref: Mapping between ids of tax templates and real taxes created from them
        :param tax_code_ref: Mapping between ids of tax code templates and real tax codes created from them
        :returns: return a tuple with a dictionary containing
            * the mapping between the account template ids and the ids of the real accounts that have been generated
              from them, as first item,
            * a similar dictionary for mapping the tax templates and taxes, as second item,
            * a last identical containing the mapping of tax code templates and tax codes
        :rtype: tuple(dict, dict, dict)
        '''
        if account_ref is None:
            account_ref = {}
        if taxes_ref is None:
            taxes_ref = {}
        if tax_code_ref is None:
            tax_code_ref = {}
        template = self.pool.get('account.chart.template').browse(cr, uid, template_id, context=context)
        obj_tax_code_template = self.pool.get('account.tax.code.template')
        obj_acc_tax = self.pool.get('account.tax')
        obj_tax_temp = self.pool.get('account.tax.template')
        obj_acc_template = self.pool.get('account.account.template')
        obj_fiscal_position_template = self.pool.get('account.fiscal.position.template')

        # create all the tax code.
        tax_code_ref.update(obj_tax_code_template.generate_tax_code(cr, uid, template.tax_code_root_id.id, company_id, context=context))

        # Generate taxes from templates.
        tax_templates = [x for x in template.tax_template_ids]
        generated_tax_res = obj_tax_temp._generate_tax(cr, uid, tax_templates, tax_code_ref, company_id, context=context)
        taxes_ref.update(generated_tax_res['tax_template_to_tax'])

        # Generating Accounts from templates.
        account_template_ref = obj_acc_template.generate_account(cr, uid, template_id, taxes_ref, account_ref, code_digits, company_id, context=context)
        account_ref.update(account_template_ref)

        # writing account values on tax after creation of accounts
        for key,value in generated_tax_res['account_dict'].items():
            if value['account_collected_id'] or value['account_paid_id']:
                obj_acc_tax.write(cr, uid, [key], {
                    'account_collected_id': account_ref.get(value['account_collected_id'], False),
                    'account_paid_id': account_ref.get(value['account_paid_id'], False),
                })

        if template.name <> 'Basic Indonesian Chart of Account':
            # Create Journals
            self.generate_journals(cr, uid, template_id, account_ref, company_id, context=context)

        # generate properties function
        self.generate_properties(cr, uid, template_id, account_ref, company_id, context=context)

        # Generate Fiscal Position , Fiscal Position Accounts and Fiscal Position Taxes from templates
        obj_fiscal_position_template.generate_fiscal_position(cr, uid, template_id, taxes_ref, account_ref, company_id, context=context)

        return account_ref, taxes_ref, tax_code_ref

    def execute(self, cr, uid, ids, context=None):
        '''
        This function is called at the confirmation of the wizard to generate the COA from the templates. It will read
        all the provided information to create the accounts, the banks, the journals, the taxes, the tax codes, the
        accounting properties... accordingly for the chosen company.
        '''
        obj_data = self.pool.get('ir.model.data')
        ir_values_obj = self.pool.get('ir.values')
        obj_wizard = self.browse(cr, uid, ids[0])
        company_id = obj_wizard.company_id.id

        self.pool.get('res.company').write(cr, uid, [company_id], {'currency_id': obj_wizard.currency_id.id})

        # When we install the CoA of first company, set the currency to price types and pricelists
        if company_id==1:
            for ref in (('product','list_price'),('product','standard_price'),('product','list0'),('purchase','list0')):
                try:
                    tmp2 = obj_data.get_object_reference(cr, uid, *ref)
                    if tmp2: 
                        self.pool.get(tmp2[0]).write(cr, uid, tmp2[1], {
                            'currency_id': obj_wizard.currency_id.id
                        })
                except ValueError, e:
                    pass

        # If the floats for sale/purchase rates have been filled, create templates from them
        self._create_tax_templates_from_rates(cr, uid, obj_wizard, company_id, context=context)

        # Install all the templates objects and generate the real objects
        acc_template_ref, taxes_ref, tax_code_ref = self._install_template(cr, uid, obj_wizard.chart_template_id.id, company_id, code_digits=obj_wizard.code_digits, obj_wizard=obj_wizard, context=context)

        # write values of default taxes for product as super user
        if obj_wizard.sale_tax and taxes_ref:
            ir_values_obj.set_default(cr, SUPERUSER_ID, 'product.product', "taxes_id", [taxes_ref[obj_wizard.sale_tax.id]], for_all_users=True, company_id=company_id)
        if obj_wizard.purchase_tax and taxes_ref:
            ir_values_obj.set_default(cr, SUPERUSER_ID, 'product.product', "supplier_taxes_id", [taxes_ref[obj_wizard.purchase_tax.id]], for_all_users=True, company_id=company_id)

        if obj_wizard.chart_template_id.name <> 'Basic Indonesian Chart of Account':
            # Create Bank journals
            self._create_bank_journals_from_o2m(cr, uid, obj_wizard, company_id, acc_template_ref, context=context)
        else:
            self.create_currency_account(cr, uid, obj_wizard, company_id, acc_template_ref, context=context)
            self.create_cash_account(cr, uid, obj_wizard, company_id, acc_template_ref, context=context)
            self.create_bank_account(cr, uid, obj_wizard, company_id, acc_template_ref, context=context)
        return {}

    def create_currency_account(self, cr, uid, obj_wizard, company_id, acc_template_ref, context=None):

        obj_account = self.pool.get('account.account')
        obj_account_template = self.pool.get('account.account.template')
        code_digits = obj_wizard.code_digits

        kriteria_account = ['Account Receivable',
                            'Advance Payment For Purchase',
                            'Deposit For Purchase',
                            'Trade Payable',
                            'Trade Payable Import',
                            'Purchase Discont',
                            'Purchase Return',
                            'Advance Payment For Sales',
                            'Deposit For Sales',
                            'Sales Revenue',
                            'Sales Return',
                            'Sales Price Different',
                            'Sales Discount'
                            ]

        if obj_wizard.currency_use_ids:
	        kriteria = [('name', 'in', kriteria_account)]
	        account_template_ids = obj_account_template.search(cr, uid, kriteria)
	        
	        for account_template in obj_account_template.browse(cr, uid, account_template_ids):
	            current_num = 1			
	            for currency in obj_wizard.currency_use_ids:
	                check = 0

	                while check == 0:
	                    new_code = str(account_template.code.ljust(code_digits-len(str(current_num)), '0')) + '0' + str(current_num)
	                    kriteria_check_new_code = [('code', '=', new_code)]
	                    check_new_code_ids = obj_account_template.search(cr, uid, kriteria_check_new_code)
	                    if not check_new_code_ids:
	                        check += 1
	                    else:
	                        current_num += 1
	                kriteria_type = [('parent_id', '=', account_template.id)]
	                account_idr_ids = obj_account_template.search(cr, uid, kriteria_type)
	                account_idr = obj_account_template.browse(cr, uid, account_idr_ids)[0]
	                

	                vals = {
	                        'code' : new_code,
	                        'name': account_template.name + ' ' + currency.name,
	                        'user_type': account_idr.user_type.id,
	                        'type': account_idr.type,
	                        'currency_id': currency.id,
	                        'parent_id' : acc_template_ref[account_template.id],
	                            }
	                
	                obj_account.create(cr, uid, vals, context=context)
	                current_num += 1
        return True

    def create_cash_account(self, cr, uid, obj_wizard, company_id, acc_template_ref, context=None):

        obj_account = self.pool.get('account.account')
        obj_account_template = self.pool.get('account.account.template')
        code_digits = obj_wizard.code_digits
        obj_data = self.pool.get('ir.model.data')
        
        kriteria_account = ['Cash']

        if obj_wizard.currency_use_ids:
            
            kriteria = [('name', 'in', kriteria_account)]
            account_template_ids = obj_account_template.search(cr, uid, kriteria)
            
            for account_template in obj_account_template.browse(cr, uid, account_template_ids):
                current_num = 1			
                for cash_account in obj_wizard.cash_account_ids:
                    check = 0

                    while check == 0:
                        new_code = str(account_template.code.ljust(code_digits-len(str(current_num)), '0')) + '0' + str(current_num)
                        kriteria_check_new_code = [('code', '=', new_code)]
                        check_new_code_ids = obj_account_template.search(cr, uid, kriteria_check_new_code)
                        if not check_new_code_ids:
                            check += 1
                        else:
                            current_num += 1
                    tmp = obj_data.get_object_reference(cr, uid, 'account', 'data_account_type_cash')
                    cash_type = tmp and tmp[1] or False
                    
                    vals = {
                            'code' : new_code,
                            'name': cash_account.name,
                            'user_type': cash_type,
                            'type': 'liquidity',
                            'currency_id': cash_account.currency_id and cash_account.currency_id.id or False,
                            'parent_id' : acc_template_ref[account_template.id],
                                }
                    #raise osv.except_osv(_('Error !'), _('%s')%vals)
                    obj_account.create(cr, uid, vals, context=context)
                    current_num += 1
        return True

    def create_bank_account(self, cr, uid, obj_wizard, company_id, acc_template_ref, context=None):

        obj_account = self.pool.get('account.account')
        obj_account_template = self.pool.get('account.account.template')
        code_digits = obj_wizard.code_digits
        obj_data = self.pool.get('ir.model.data')
        
        kriteria_account = ['Bank']

        if obj_wizard.currency_use_ids:
            
            kriteria = [('name', 'in', kriteria_account)]
            account_template_ids = obj_account_template.search(cr, uid, kriteria)
            
            for account_template in obj_account_template.browse(cr, uid, account_template_ids):
                current_num = 1			
                for bank_account in obj_wizard.bank_account_ids:
                    check = 0

                    while check == 0:
                        new_code = str(account_template.code.ljust(code_digits-len(str(current_num)), '0')) + '0' + str(current_num)
                        kriteria_check_new_code = [('code', '=', new_code)]
                        check_new_code_ids = obj_account_template.search(cr, uid, kriteria_check_new_code)
                        if not check_new_code_ids:
                            check += 1
                        else:
                            current_num += 1
                    tmp = obj_data.get_object_reference(cr, uid, 'account', 'data_account_type_bank')
                    bank_type = tmp and tmp[1] or False
                    
                    vals = {
                            'code' : new_code,
                            'name': bank_account.name,
                            'user_type': bank_type,
                            'type': 'liquidity',
                            'currency_id': bank_account.currency_id and bank_account.currency_id.id or False,
                            'parent_id' : acc_template_ref[account_template.id],
                                }
                    #raise osv.except_osv(_('Error !'), _('%s')%vals)
                    obj_account.create(cr, uid, vals, context=context)
                    current_num += 1
        return True

wizard_multi_charts_accounts()
