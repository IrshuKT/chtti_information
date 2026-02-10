# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'



    weekly_payment = fields.Float(string='Weekly Payment')
    chitti_number_ids = fields.One2many(
        'partner.chitti.number',
        'partner_id',
        string='Chitti Numbers'
    )


class PartnerChittiNumber(models.Model):
    _name = 'partner.chitti.number'
    _description = 'Partner Chitti Numbers'

    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    number = fields.Char(string='Chitti Number', required=True)
    active = fields.Boolean(string='Active', default=True)

    @api.depends('chitti_number_ids.number')
    def _compute_chitti_numbers(self):
        for partner in self:
            partner.chitti_numbers = ', '.join(
                partner.chitti_number_ids.mapped('number')
            )

    _sql_constraints = [
        ('number_unique', 'unique(partner_id, number)', 'This chitti number already exists for this partner!'),
    ]