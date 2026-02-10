from odoo import models, fields,api

class Ledger(models.Model):
    _name = 'share_investment.ledger'
    _description = 'Member Ledger'

    member_id = fields.Many2one('share_investment.member', string="Member")
    payment_id = fields.Many2one('share_investment.payment', string="Payment")
    payment_method = fields.Selection([('cash', 'Cash'), ('bank', 'Bank')], string="Payment Method", required=True)
    amount = fields.Monetary(string="Amount", currency_field='currency_id')
    date = fields.Date(string="Receipt Date", default=fields.Date.context_today)
    transaction_type = fields.Selection([('receipt', 'Receipt'), ('return', 'Return')], string="Payment Type",
                                    required=True)
    currency_id = fields.Many2one('res.currency', string="Currency", default=lambda self: self.env.company.currency_id)

    receipt_amount = fields.Monetary(compute='_compute_split_amounts', string="Receipts")
    payment_amount = fields.Monetary(compute='_compute_split_amounts', string="Payments")

    @api.depends('amount', 'transaction_type')
    def _compute_split_amounts(self):
        for rec in self:
            # ALWAYS initialize with 0.0 first to avoid CacheMiss/ValueError
            rec.receipt_amount = 0.0
            rec.payment_amount = 0.0

            if rec.transaction_type == 'receipt':
                rec.receipt_amount = rec.amount
            elif rec.transaction_type == 'return':
                rec.payment_amount = rec.amount