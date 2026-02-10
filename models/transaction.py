from odoo import models, fields

class CashBankTracking(models.Model):
    _name = 'share_investment.cash.bank.tracking'
    _description = 'Track Cash and Bank Balances'

    day_now = fields.Date(string="Transfer Date", default=fields.Date.context_today)
    total_cash = fields.Monetary(string="Total Cash", currency_field='currency_id', default=0.0)
    total_bank = fields.Monetary(string="Total Bank", currency_field='currency_id', default=0.0)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
