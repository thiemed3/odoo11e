# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

import datetime
import logging
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import float_compare, float_round

class as_facturas(models.TransientModel):
    _name="as.modificador.factura"
    _description = "Factura Reports by AhoraSoft"
    
    as_invoice = fields.Many2one('account.invoice', string="Seleccione Factura", domain="[('type', '=', 'out_invoice'),('state', '=', 'open')]")
    num = fields.Integer(string='Numero de Factura')
    name = fields.Char(string='Nombre Actual')
    name_new = fields.Char(string='Nombre Resultante')

    @api.onchange('as_invoice','num')
    def onchange_name(self):
        sec = 0
        for inv in self:
            if inv.as_invoice:
                inv.name = inv.as_invoice.number
                secuencia = self.env['ir.sequence'].search([('name', '=', 'Facturas de cliente - Factura Electrónica')])
                padding = int(secuencia.padding)
                nombre = inv.as_invoice.number
                sec= int(len(nombre)) - padding
                array = nombre[0:sec]
                if inv.num:
                    numpad= int(len(str(inv.num)))
                    if numpad > padding:
                        raise UserError("El tamano del campo no puede superar al padding de la secuencia")
                    elif numpad < padding:
                        tamano = padding - numpad
                        nom = ''
                        for i in range(0,tamano):
                            nom+='0'
                        nuevo = array + nom + str(inv.num)
                    else:
                        nuevo = array+str(inv.num)
                    inv.name_new = nuevo
    @api.multi
    def modificar_factura(self):
        for inv in self:
            inv.write({'number':inv.name_new,'move_name':inv.name_new})
            mensaje = 'Verificar la secuencia en el Menu Ajuste>> Secuencia>> Facturas de cliente - Factura Electrónica: PROXIMO NUMERO'
            return True


