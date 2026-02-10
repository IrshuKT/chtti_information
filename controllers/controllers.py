# -*- coding: utf-8 -*-
# from odoo import http


# class ChittiInformation(http.Controller):
#     @http.route('/chitti_information/chitti_information', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/chitti_information/chitti_information/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('chitti_information.listing', {
#             'root': '/chitti_information/chitti_information',
#             'objects': http.request.env['chitti_information.chitti_information'].search([]),
#         })

#     @http.route('/chitti_information/chitti_information/objects/<model("chitti_information.chitti_information"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('chitti_information.object', {
#             'object': obj
#         })
