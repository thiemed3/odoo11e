from odoo import api, fields, models, _

import pandas as pd

import logging
_logger = logging.getLogger(__name__)

import os
import sys

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import io
import base64

from six import u as unicode

from odoo.exceptions import UserError

class Charges(models.Model):
    _name = "charges"
    _description = "Charges"

    name = fields.Char("Name", required=True)
    b_products_inventary_filename = fields.Char("Load file of Products and Inventory name")
    b_products_inventary = fields.Binary("Load file of Products and Inventory", required=True)
    status_products = fields.Char("Status products")
    status_inventory_lots = fields.Char("Status inventory lots")
    status_inventory_series = fields.Char("Status inventory series")

    @api.one
    @api.model
    def load_products(self):
        categ_ids = self.env['product.category']._search(['|', ('name', '=', 'All'), ('name', '=', 'Todos')])

        categ_id = 0
        if len(categ_ids) > 0:
            categ_id = categ_ids[0]

        if categ_id == 0:
            raise UserError(_("Debe configurar la categoría " + str(categ_ids)))

        #nombre_archivo = "Maestro de productos e inventario Thiemed_second.xlsx"
        
        inputx = io.BytesIO()
        data = base64.b64decode(self.b_products_inventary)
        inputx.write(data)

        df = pd.read_excel(inputx, "Maestro")
        
        cargado = False

        for index, row in df.iterrows():
            sku = str(row['Referencia Interna /SKU'])
            nombre_producto = unicode(row['Nombre producto'])
            numero_serie = str(row['Numero de serie'])
            codigo_ean = '' if str(row['Codigo EAN']) == 'nan' else str(row['Codigo EAN'])
            costo_promedio = float(0) if str(row['Costo Promedio']) == 'nan' else float(row['Costo Promedio'])
            categoria = str(row['Categoria'])

            categ_ids = self.env['product.category']._search(['|', ('name', '=', 'All'), ('name', '=', 'Todos')])
            
            values = {'name': nombre_producto, 'description_pickingin': 'nuevos', 'type': 'product', 'invoice_policy': 'delivery', 'purchase_method': 'receive', 'categ_id': categ_id, 'standard_price': costo_promedio, 'categ_id': categ_ids[0]}

            _logger.info("SKU=" + str(sku))

            if len(codigo_ean) > 0 and codigo_ean:
                values.update({'barcode': codigo_ean})
            
            if numero_serie == "Lote":
                values.update({'tracking': 'lot'})
            elif numero_serie == "NumSerie":
                values.update({'tracking': 'serial'})

            product_ids = self.env['product.template'].search([('default_code', '=', sku)])

            if len(product_ids) == 1:
                result = product_ids.write(values)

                if not result:
                    raise UserError(_("Write falló para SKU " + sku))
            elif len(product_ids) == 0:
                values.update({'default_code': sku})
                result = self.env['product.template'].create(values)

                if not result:
                    raise UserError(_("Create falló para SKU " + sku))

            elif len(product_ids) > 1:
                raise UserError(_("ERROR: Hay más de un producto con el mismo SKU que se trata de cargar. SKU " + sku))

            cargado = True
        
        if cargado:
            self.write({'status_products': 'Cargado'})
        else:
            self.write({'status_products': 'No cargado, sin productos que cargar'})
        
        return True

    @api.one
    @api.model
    def load_inventory(self):
        cargado = False
        
        inputx = io.BytesIO()
        data = base64.b64decode(self.b_products_inventary)
        inputx.write(data)
        
        df = pd.read_excel(inputx, "Inventario de series")
        
        _logger.info("Inventario de series")

        for index, row in df.iterrows():
            sku = str(row['Referencia Interna'])
            inventario = str(row['Inventario al 31/12'])
            numero_serie = str(row['Numero de Serie'])
            bodega = str(row['Bodega'])
            
            values = {'new_quantity': inventario}
            
            product_id = self.env['product.product']._search([('default_code', '=', sku)], limit=1)
            
            product_id = product_id[0]
            
            values.update({'product_id': product_id})

            warehouse_ids = self.env['stock.warehouse'].search([('name', '=', bodega), ('lot_stock_id.usage', '=', 'internal')])

            warehouse_read = warehouse_ids.read()
            
            location_id = self.env['stock.location']._search([('id', '=', warehouse_read[0]['lot_stock_id'][0])], limit=1)
            
            location_id = location_id[0]
            
            values.update({'location_id': location_id})
            
            lot_ids = self.env['stock.production.lot'].search([('name', '=', numero_serie), ('product_id', '=', product_id)], limit=1)
            
            if len(lot_ids) == 0:
                result = self.env['stock.production.lot'].create({'name': numero_serie, 'product_id': product_id})
                lot_id = result
            else:
                lot_id = lot_ids
                
            values.update({'lot_id': lot_id.id})
            
            id_stock_qty = self.env['stock.change.product.qty'].create(values)
            
            id_stock_qty = self.env['stock.change.product.qty'].search([('id', '=', id_stock_qty.id)])
            
            result = id_stock_qty.with_context({'assign_custom_date': True}).change_product_qty()
            
            cargado = True
            
        if cargado:
            self.write({'status_inventory_lots': 'Cargado'})
        else:
            self.write({'status_inventory_lots': 'No cargado, sin series que cargar'})
        
        cargado = False
        
        inputx.close()
        
        inputx = io.BytesIO()
        data = base64.b64decode(self.b_products_inventary)
        inputx.write(data)
        
        df = pd.read_excel(inputx, "Inventario de lotes")
        _logger.info("Inventario de lotes")
        
        for index, row in df.iterrows():
            sku = str(row['Referencia Interna'])
            inventario = str(row['Inventario al 31/12'])
            numero_serie = str(row['Lote'])
            bodega = str(row['Bodega'])
            
            _logger.info(str(sku) + " " + str(inventario) + " " + str(numero_serie) + " " + str(bodega))
            
            values = {'new_quantity': inventario}
            
            product_id = self.env['product.product'].search([('default_code', '=', sku)], limit=1)
            
            product_id = product_id
            
            values.update({'product_id': product_id.id, 'product_tmpl_id': product_id.product_tmpl_id.id})

            warehouse_id = self.env['stock.warehouse'].search([('name', '=', bodega), ('lot_stock_id.usage', '=', 'internal')], limit=1)
            
            location_id = self.env['stock.location'].search([('id', '=', warehouse_id[0].lot_stock_id.id)], limit=1)
            
            location_id = location_id.id
            
            values.update({'location_id': location_id})
            
            lot_ids = self.env['stock.production.lot'].search([('name', '=', numero_serie), ('product_id', '=', product_id.id)], limit=1)
            
            if len(lot_ids) == 0:
                result = self.env['stock.production.lot'].create({'name': numero_serie, 'product_id': product_id.id})
                lot_id = result
            else:
                lot_id = lot_ids
                
            values.update({'lot_id': lot_id.id})
            
            id_stock_qty = self.env['stock.change.product.qty'].create(values)
            
            id_stock_qty = self.env['stock.change.product.qty'].search([('id', '=', id_stock_qty.id)])
            
            _logger.info(str(values))
            
            result = id_stock_qty.with_context({'assign_custom_date': True}).change_product_qty()
            
            cargado = True
            
        if cargado:
            self.write({'status_inventory_lots': 'Cargado'})
        else:
            self.write({'status_inventory_lots': 'No cargado, sin lotes que cargar'})
        
        return True

    @api.one
    @api.model
    def load_products_and_inventary(self):
        categ_ids = self.env['product.category']._search(['|', ('name', '=', 'All'), ('name', '=', 'Todos')])

        categ_id = 0
        if len(categ_ids) > 0:
            categ_id = categ_ids[0]

        if categ_id == 0:
            raise UserError(_("Debe configurar la categoría " + str(categ_ids)))
            return False

        #nombre_archivo = "Maestro de productos e inventario Thiemed_second.xlsx"
        
        inputx = io.BytesIO()
        data = base64.b64decode(self.b_products_inventary)
        inputx.write(data)

        df = pd.read_excel(inputx, "Maestro")
        
        cargado = False

        for index, row in df.iterrows():
            sku = str(row['Referencia Interna /SKU'])
            nombre_producto = unicode(row['Nombre producto'])
            numero_serie = str(row['Numero de serie'])
            codigo_ean = '' if str(row['Codigo EAN']) == 'nan' else str(row['Codigo EAN'])
            costo_promedio = float(0) if str(row['Costo Promedio']) == 'nan' else float(row['Costo Promedio'])
            categoria = str(row['Categoria'])

            categ_ids = self.env['product.category']._search(['|', ('name', '=', 'All'), ('name', '=', 'Todos')])
            
            values = {'name': nombre_producto, 'description_pickingin': 'nuevos', 'type': 'product', 'invoice_policy': 'delivery', 'purchase_method': 'receive', 'categ_id': categ_id, 'standard_price': costo_promedio, 'categ_id': categ_ids[0]}

            if len(codigo_ean) > 0 and codigo_ean:
                values.update({'barcode': codigo_ean})
            
            if numero_serie == "Lotes":
                values.update({'tracking': 'lot'})
            elif numero_serie == "NumSerie":
                values.update({'tracking': 'serial'})

            product_ids = self.env['product.template'].search([('default_code', '=', sku)])

            if len(product_ids) == 1:
                result = product_ids.write(values)

                if not result:
                    raise UserError(_("Write falló para SKU " + sku))
            elif len(product_ids) == 0:
                values.update({'default_code': sku})
                result = self.env['product.template'].create(values)

                if not result:
                    raise UserError(_("Create falló para SKU " + sku))

            elif len(product_ids) > 1:
                raise UserError(_("ERROR: Hay más de un producto con el mismo SKU que se trata de cargar. SKU " + sku))

            cargado = True
        
        if cargado:
            self.write({'status_products': 'Cargado'})
        else:
            self.write({'status_products': 'No cargado, sin productos que cargar'})
        
        cargado = False
        
        inputx.close()
        
        inputx = io.BytesIO()
        data = base64.b64decode(self.b_products_inventary)
        inputx.write(data)
        
        df = pd.read_excel(inputx, "Inventario de series")
        
        _logger.info("Inventario de series")

        for index, row in df.iterrows():
            sku = str(row['Referencia Interna'])
            inventario = str(row['Inventario al 31/12'])
            numero_serie = str(row['Numero de Serie'])
            bodega = str(row['Bodega'])
            
            values = {'new_quantity': inventario}
            
            product_id = self.env['product.product']._search([('default_code', '=', sku)], limit=1)
            
            product_id = product_id[0]
            
            values.update({'product_id': product_id})

            warehouse_ids = self.env['stock.warehouse'].search([('name', '=', bodega), ('lot_stock_id.usage', '=', 'internal')])

            warehouse_read = warehouse_ids.read()
            
            location_id = self.env['stock.location']._search([('id', '=', warehouse_read[0]['lot_stock_id'][0])], limit=1)
            
            location_id = location_id[0]
            
            values.update({'location_id': location_id})
            
            lot_ids = self.env['stock.production.lot'].search([('name', '=', numero_serie), ('product_id', '=', product_id)], limit=1)
            
            if len(lot_ids) == 0:
                result = self.env['stock.production.lot'].create({'name': numero_serie, 'product_id': product_id})
                lot_id = result
            else:
                lot_id = lot_ids
                
            values.update({'lot_id': lot_id.id})
            
            id_stock_qty = self.env['stock.change.product.qty'].create(values)
            
            id_stock_qty = self.env['stock.change.product.qty'].search([('id', '=', id_stock_qty.id)])
            
            result = id_stock_qty.with_context({'assign_custom_date': True}).change_product_qty()
            
            cargado = True
            
        if cargado:
            self.write({'status_inventory_lots': 'Cargado'})
        else:
            self.write({'status_inventory_lots': 'No cargado, sin series que cargar'})
        
        cargado = False
        
        inputx.close()
        
        inputx = io.BytesIO()
        data = base64.b64decode(self.b_products_inventary)
        inputx.write(data)
        
        df = pd.read_excel(inputx, "Inventario de lotes")
        _logger.info("Inventario de lotes")
        
        for index, row in df.iterrows():
            sku = str(row['Referencia Interna'])
            inventario = str(row['Inventario al 31/12'])
            numero_serie = str(row['Lote'])
            bodega = str(row['Bodega'])
            
            _logger.info(str(sku) + " " + str(inventario) + " " + str(numero_serie) + " " + str(bodega))
            
            values = {'new_quantity': inventario}
            
            product_id = self.env['product.product'].search([('default_code', '=', sku)], limit=1)
            
            product_id = product_id
            
            values.update({'product_id': product_id.id, 'product_tmpl_id': product_id.product_tmpl_id.id})

            warehouse_id = self.env['stock.warehouse'].search([('name', '=', bodega), ('lot_stock_id.usage', '=', 'internal')], limit=1)
            
            location_id = self.env['stock.location'].search([('id', '=', warehouse_id[0].lot_stock_id.id)], limit=1)
            
            location_id = location_id.id
            
            values.update({'location_id': location_id})
            
            lot_ids = self.env['stock.production.lot'].search([('name', '=', numero_serie), ('product_id', '=', product_id.id)], limit=1)
            
            if len(lot_ids) == 0:
                result = self.env['stock.production.lot'].create({'name': numero_serie, 'product_id': product_id.id})
                lot_id = result
            else:
                lot_id = lot_ids
                
            values.update({'lot_id': lot_id.id})
            
            id_stock_qty = self.env['stock.change.product.qty'].create(values)
            
            id_stock_qty = self.env['stock.change.product.qty'].search([('id', '=', id_stock_qty.id)])
            
            _logger.info(str(values))
            
            result = id_stock_qty.with_context({'assign_custom_date': True}).change_product_qty()
            
            cargado = True
            
        if cargado:
            self.write({'status_inventory_lots': 'Cargado'})
        else:
            self.write({'status_inventory_lots': 'No cargado, sin lotes que cargar'})
        
        return True
