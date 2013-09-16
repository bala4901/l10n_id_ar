# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2009 P. Christeas <p_christ@hol.gr>. All Rights Reserved
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
{
    'name': 'Indonesia - Accounting',
    'version': '1.0',
    'author': 'Andhitia Rama & Michael Viriyananda',
    'website': 'andhitiarama.wordpress.com',
    'category': 'Localization/Account Charts',
    'description': """
    Locatization data for Indonesia :
    1. Account Type
    2. Account
    3. Bank
    
    """,
    'depends': ['account_chart'],
    'demo': [],
    'data': [   
                        'view/view_MultiChartAccount.xml',
                        'account_chart_template.xml',
                        'data/account.account.type.csv',
                        'data/account.account.template.csv',
                        'data/account.tax.template.csv',
                        'data/res.bank.csv',
                        'data/account.tax.code.template.csv',
                        'data/res.country.state.csv',
                        'account_chart_template_after.xml',
                        'l10n_id_ar_wizard.xml',],
    'installable': True,
    'images': [],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

