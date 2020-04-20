from odoo import models, http
from odoo.http import request
from odoo.addons.web.controllers.main import serialize_exception, content_disposition

class Binary(http.Controller):

    def document(self, filename, filecontent):
        if not filecontent:
            return request.not_found()
        headers = [
            ('Content-Type', 'application/xml'),
            ('Content-Disposition', content_disposition(filename)),
            ('charset', 'utf-8'),
        ]
        return request.make_response(
                filecontent, headers=headers, cookies=None)

    @http.route(["/download/xml/invoice/<model('account.invoice'):document_id>"], type='http', auth='user')
    @serialize_exception
    def download_document(self, document_id, **post):
        filename = ('%s.xml' % document_id.document_number).replace(' ','_')
        filecontent = document_id.sii_xml_request.xml_envio
        return self.document(filename, filecontent)

    @http.route(["/download/xml/invoice_exchange/<model('account.invoice'):rec_id>"], type='http', auth='user')
    @serialize_exception
    def download_document_exchange(self, rec_id, **post):
        filename = ('%s.xml' % rec_id.document_number).replace(' ','_')
        filecontent = rec_id.sii_xml_request.xml_envio
        return self.document(filename, filecontent)

    @http.route(["/download/xml/cf/<model('account.move.consumo_folios'):rec_id>"], type='http', auth='user')
    @serialize_exception
    def download_cf(self, rec_id, **post):
        filename = ('CF_%s.xml' % rec_id.name).replace(' ','_')
        filecontent = rec_id.sii_xml_request
        return self.document(filename, filecontent)

    @http.route(["/download/xml/libro/<model('account.move.book'):rec_id>"], type='http', auth='user')
    @serialize_exception
    def download_book(self, rec_id, **post):
        filename = ('Libro_%s.xml' % rec_id.name).replace(' ','_')
        filecontent = rec_id.sii_xml_request
        return self.document(filename, filecontent)
