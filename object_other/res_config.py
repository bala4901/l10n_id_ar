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
        return {}

wizard_multi_charts_accounts()
