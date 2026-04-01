from odoo import models, fields, api
import random
import urllib.parse

from odoo.exceptions import ValidationError


class Member(models.Model):
    _name = 'share_investment.member'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Member Information'

    name = fields.Char(string="Member Name", required=True, tracking=True)
    contact_number = fields.Char(string="Contact Number", tracking=True)
    share_count = fields.Integer(string="Number of Shares", required=True, tracking=True)
    shares = fields.One2many('share_investment.share', 'member_id', string="Shares")
    ledger = fields.One2many('share_investment.ledger', 'member_id', string="Member Ledger")
    active = fields.Boolean('Active',default = True, tracking=True)
    share_numbers_id = fields.Many2many('share.number',string='Share Number')
    has_received_payment = fields.Boolean(
        string="Payment Received",default=False,tracking=True)
    reminder_sent = fields.Boolean(string="Reminder Sent", default=False)

    @api.depends('shares.share_number')
    def _compute_count_values(self):
        for member in self:
            share_numbers = member.mapped('shares.share_number')
            member.count_values = ', '.join(map(str, share_numbers)) if share_numbers else 'No shares'

    def open_member(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Member',
            'res_model': 'share_investment.member',
            'res_id': self.name,
            'view_mode': 'form',
            'target': 'current',
        }

    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed')
    ], default='draft', string='Status', tracking=True)

    def action_confirm(self):
        self.ensure_one()
        self.status = 'confirmed'
        return self.send_message()

    def action_draft(self):
        for record in self:
            record.status = 'draft'

    def send_message(self):
        self.ensure_one()

        if not self.contact_number:
            raise ValidationError('No WhatsApp Number')

        share_numbers = ', '.join(self.share_numbers_id.mapped('name'))

        msg = f"{self.name} താങ്കളുടെ  സഹായ കുറി  നറുക്ക് നമ്പർ : {share_numbers}"
        encoded_msg = urllib.parse.quote(msg)

        whatsapp_url = (
                "https://api.whatsapp.com/send?phone=%s&text=%s"
                % (self.contact_number, encoded_msg)
        )

        return {
            'type': 'ir.actions.act_url',
            'url': whatsapp_url,
            'target': 'new',
        }

    def reminder_msg(self):
        self.ensure_one()
        if not self.contact_number:
            raise ValidationError('No WhatsApp Number')
        msg = f"{self.name} ഇന്നലത്തെ ഇന്നത്തെയും   അടുത്ത ആഴ്ചയിലെ 10 ലെ ഭാഗ്യവാനും ഷാഫി പി  "
        encoded_msg = urllib.parse.quote(msg)

        whatsapp_url = (
                "https://api.whatsapp.com/send?phone=%s&text=%s"
                % (self.contact_number, encoded_msg)
        )
        return {
            'type': 'ir.actions.act_url',
            'url': whatsapp_url,
            'target': 'new',
        }

    def winner_msg(self):
        self.ensure_one()

        if not self.contact_number:
            raise ValidationError('No WhatsApp Number')


        msg = f"{self.name} നമ്മുടെ കുറിയുടെ 2nd ഭാഗ്യവാൻ Naseeba K T "
        encoded_msg = urllib.parse.quote(msg)

        whatsapp_url = (
                "https://api.whatsapp.com/send?phone=%s&text=%s"
                % (self.contact_number, encoded_msg)
        )

        return {
            'type': 'ir.actions.act_url',
            'url': whatsapp_url,
            'target': 'new',
        }

    last_payment_date = fields.Date(
        string="Last Receipt Date",
        compute="_compute_last_payment",
        store=False
    )

    last_payment_amount = fields.Monetary(
        string="Last Amount",
        compute="_compute_last_payment",
        currency_field='currency_id'
    )

    last_payment_day = fields.Char(
        string="Last Payment Day",
        compute="_compute_last_payment"
    )

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )

    def _compute_last_payment(self):
        Payment = self.env['share_investment.payment']

        for member in self:
            last_payment = Payment.search([
                ('member_id', '=', member.id),
                ('payment_type', '=', 'receipt')
            ], order='date desc', limit=1)

            if last_payment:
                member.last_payment_date = last_payment.date
                member.last_payment_amount = last_payment.amount
                member.last_payment_day = last_payment.payment_dates
            else:
                member.last_payment_date = False
                member.last_payment_amount = 0
                member.last_payment_day = False