# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (c) 2017 Konos http://www.konos.cl

from . import models

from odoo import api, SUPERUSER_ID
from odoo.addons import account

SYSCOHADA_LIST = ['BJ', 'BF', 'CM', 'CF', 'KM', 'CG', 'CI', 'GA', 'GN', 'GW', 'GQ', 'ML', 'NE', 'CD', 'SN', 'TD', 'TG']

def _auto_install_l10n(cr, registry):
    #check the country of the main company (only) and eventually load some module needed in that country
    env = api.Environment(cr, SUPERUSER_ID, {})
    country_code = env.user.company_id.country_id.code
    if country_code:
        #auto install localization module(s) if available
        module_list = []
        if country_code in SYSCOHADA_LIST:
            #countries using OHADA Chart of Accounts
            module_list.append('l10n_syscohada')
        elif country_code == 'GB':
            module_list.append('l10n_uk')
        elif country_code == 'DE':
            module_list.append('l10n_de_skr03')
            module_list.append('l10n_de_skr04')
        else:
            if country_code.lower() == 'cl' and env['ir.module.module'].search([('name', '=', 'l10n_cl_chart_of_account')]):
                module_list.append('l10n_cl_chart_of_account')
            elif env['ir.module.module'].search([('name', '=', 'l10n_' + country_code.lower())]):
                module_list.append('l10n_' + country_code.lower())
            else:
                module_list.append('l10n_generic_coa')
        if country_code == 'US':
            module_list.append('account_plaid')
            module_list.append('account_check_printing')
        if country_code in ['US', 'AU', 'NZ', 'CA', 'CO', 'EC', 'ES', 'FR', 'IN', 'MX', 'UK']:
            module_list.append('account_yodlee')
        if country_code in SYSCOHADA_LIST + [
            'AT', 'BE', 'CA', 'CO', 'DE', 'EC', 'ES', 'ET', 'FR', 'GR', 'IT', 'LU', 'MX', 'NL', 'NO', 
            'PL', 'PT', 'RO', 'SI', 'TR', 'UK', 'VE', 'VN'
            ]:
            module_list.append('base_vat')

        #european countries will be using SEPA
        europe = env.ref('base.europe', raise_if_not_found=False)
        if europe:
            europe_country_codes = [x.code for x in europe.country_ids]
            if country_code in europe_country_codes:
                module_list.append('account_sepa')
        module_ids = env['ir.module.module'].search([('name', 'in', module_list), ('state', '=', 'uninstalled')])
        module_ids.sudo().button_install()

#mokeypatch para reemplazar funcion y al ser chile instale este paquete contable en lugar del original
account._auto_install_l10n = _auto_install_l10n