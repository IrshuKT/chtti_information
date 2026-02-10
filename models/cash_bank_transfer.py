from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CashBankTransfer(models.Model):
    _name = 'share_investment.cash.bank.transfer'
    _description = 'Track Cash to Bank or Bank to Cash Transfer'

    transfer_amount = fields.Monetary(string="Transfer Amount", required=True, currency_field='currency_id')
    transfer_type = fields.Selection([
        ('cash_to_bank', 'Cash to Bank'),
        ('bank_to_cash', 'Bank to Cash'),
    ], string="Transfer Type", required=True)
    transfer_date = fields.Date(string="Transfer Date", default=fields.Date.context_today)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    remarks = fields.Text('Notes')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed')
    ], default='draft', string="Status", readonly=True)

    def action_confirm(self):
        """Triggers the actual movement of money"""
        for rec in self:
            if rec.status == 'confirmed':
                continue

            # Find or create tracking record
            tracking = self.env['share_investment.cash.bank.tracking'].search([], limit=1)
            if not tracking:
                tracking = self.env['share_investment.cash.bank.tracking'].create({})

            # Validate balance before transfer (Optional but recommended)
            if rec.transfer_type == 'cash_to_bank' and tracking.total_cash < rec.transfer_amount:
                raise UserError(_("Insufficient Cash balance to perform this transfer!"))
            if rec.transfer_type == 'bank_to_cash' and tracking.total_bank < rec.transfer_amount:
                raise UserError(_("Insufficient Bank balance to perform this transfer!"))

            # Execute Transfer
            if rec.transfer_type == 'cash_to_bank':
                tracking.total_cash -= rec.transfer_amount
                tracking.total_bank += rec.transfer_amount
            else:
                tracking.total_bank -= rec.transfer_amount
                tracking.total_cash += rec.transfer_amount

            rec.status = 'confirmed'

    def action_reset_to_draft(self):
        for rec in self:
            if rec.status != 'confirmed':
                continue

            tracking = self.env['share_investment.cash.bank.tracking'].search([], limit=1)
            if not tracking:
                raise UserError(_("Tracking record not found."))

            # Reverse the transfer
            if rec.transfer_type == 'cash_to_bank':
                if tracking.total_bank < rec.transfer_amount:
                    raise UserError(_("Cannot reset: insufficient bank balance to reverse."))
                tracking.total_cash += rec.transfer_amount
                tracking.total_bank -= rec.transfer_amount
            else:  # bank_to_cash
                if tracking.total_cash < rec.transfer_amount:
                    raise UserError(_("Cannot reset: insufficient cash balance to reverse."))
                tracking.total_bank += rec.transfer_amount
                tracking.total_cash -= rec.transfer_amount

            rec.status = 'draft'

    def unlink(self):
        for rec in self:
            if rec.status == 'confirmed':
                raise UserError(_("Confirmed transfers cannot be deleted."))
        return super(CashBankTransfer, self).unlink()