from odoo import models, fields

class Share(models.Model):
    _name = 'share_investment.share'
    _description = 'Share Information'

    member_id = fields.Many2one('share_investment.member', string="Member")
    share_number = fields.Integer(string="Share Number", required=True, unique=True)

    payment_count = fields.Integer(compute='_compute_payment_count', string="Payment Count")

    def _compute_payment_count(self):
        for record in self:
            record.payment_count = self.env['share_investment.payment'].search_count([
                ('member_id', '=', record.id)
            ])

    def action_view_payments(self):
        self.ensure_one()
        return {
            'name': 'Payments',
            'type': 'ir.actions.act_window',
            'res_model': 'share_investment.payment',
            'view_mode': 'tree,form',
            'domain': [('member_id', '=', self.id)],
            'context': {'default_member_id': self.id},  # Auto-fills member when creating new payment
        }
