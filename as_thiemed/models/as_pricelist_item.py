from odoo import api, fields, models
    
class product_pricelist_item(models.Model):
    _inherit = "product.pricelist.item"
    
    default_code = fields.Char('Referencia Interna', related='product_tmpl_id.default_code', store=True)
