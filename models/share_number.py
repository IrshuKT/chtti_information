from odoo import models,fields
from odoo.exceptions import ValidationError
from odoo import api


class ShareNumber(models.Model):
    _name = 'share.number'
    _description = 'Share number of members'

    name = fields.Char('Share Number')


@api.constrains('name')
def _check_unique_name(self):
    for rec in self:
        if self.search_count([('name', '=', rec.name), ('id', '!=', rec.id)]) > 0:
            raise ValidationError('Share Number must be unique!')