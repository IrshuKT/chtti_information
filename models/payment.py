from odoo import models, fields, api,_
from odoo.exceptions import ValidationError


class Payment(models.Model):
    _name = 'share_investment.payment'
    _description = 'Payments to Members'
    _rec_name = 'member_id'

    member_id = fields.Many2one('share_investment.member', string="Member",required=True)
    phone = fields.Char(
        string="Mobile Number",related='member_id.contact_number',store=True,readonly=True)
    payment_type = fields.Selection([('receipt', 'Receipt'), ('return', 'Return')], string="Receipt Type",
                                    required=True,default='receipt')
    amount = fields.Monetary(string="Amount", required=True, currency_field='currency_id',)
    date = fields.Date(string="Receipt Date", default=fields.Date.context_today)
    currency_id = fields.Many2one('res.currency', string="Currency", default=lambda self: self.env.company.currency_id)
    payment_method = fields.Selection([('cash', 'Cash'), ('bank', 'Bank')], string="Receipt Method", required=True,default='cash')
    # payment_month = fields.Date(string="Payment Month",required=True,
    #     help="Any date inside the month this payment belongs to")
    payment_month_id = fields.Selection([
        ('01', 'January'),
        ('02', 'February'),
        ('03', 'March'),
        ('04', 'April'),
        ('05', 'May'),
        ('06', 'June'),
        ('07', 'July'),
        ('08', 'August'),
        ('09', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December'),
    ], string="Payment Month")

    payment_dates = fields.Selection([
        ('10','10'),('20','20'),('30','30')],string='Payment Day',required=True)

    @api.model
    def create(self, vals):
        payment = super(Payment, self).create(vals)
        # Update balance and ledger
        payment.update_cash_bank_balances()
        payment.create_member_ledger_entry()
        return payment

    def write(self, vals):
        # To handle updates: reverse the OLD values, then apply NEW values
        for rec in self:
            # 1. Reverse old impact
            rec._reverse_old_impact()

            # 2. Update the record
            super(Payment, rec).write(vals)

            # 3. Apply new impact and update ledger
            rec._apply_new_balance_impact()
            rec.create_member_ledger_entry()
        return True



    def _reverse_old_impact(self):
        """Helper to undo the current record's financial impact"""
        tracking = self.env['share_investment.cash.bank.tracking'].search([], limit=1)
        if tracking:
            # We do the exact opposite of the current state
            # If it was a receipt (+), we subtract. If return (-), we add.
            adjustment = self.amount if self.payment_type == 'receipt' else -self.amount
            if self.payment_method == 'cash':
                tracking.total_cash -= adjustment
            else:
                tracking.total_bank -= adjustment

    def _check_balance_availability(self, tracking_record, amount, method, p_type):
        """Helper to verify if enough funds exist in Global Tracking AND Member Ledger"""
        if p_type == 'return':
            # --- GLOBAL BALANCE CHECK ---
            if method == 'cash' and tracking_record.total_cash < amount:
                raise ValidationError(
                    _("Insufficient Global Cash! Available: %s, Required: %s") % (tracking_record.total_cash, amount)
                )
            elif method == 'bank' and tracking_record.total_bank < amount:
                raise ValidationError(
                    _("Insufficient Global Bank Balance! Available: %s, Required: %s") % (
                    tracking_record.total_bank, amount)
                )

            # # --- MEMBER LEDGER BALANCE CHECK ---
            # # Search all ledger entries for this specific member
            # ledger_entries = self.env['share_investment.ledger'].search([
            #     ('member_id', '=', self.member_id.id)
            # ])
            #
            # # Sum up their total investment (receipts) and their total withdrawals (returns)
            # total_receipts = sum(ledger_entries.filtered(lambda l: l.transaction_type == 'receipt').mapped('amount'))
            # total_previous_returns = sum(
            #     ledger_entries.filtered(lambda l: l.transaction_type == 'return').mapped('amount'))
            #
            # # If we are UPDATING a record, we shouldn't count its own old value in the total_previous_returns
            # # But since your write() method reverses the old impact first, the ledger search
            # # will stay accurate.
            #
            # available_member_balance = total_receipts - total_previous_returns
            #
            # if amount > available_member_balance:
            #     raise ValidationError(
            #         _("Member Balance Exceeded! This member only has %s available for return, but you are trying to pay %s.")
            #         % (available_member_balance, amount)
            #     )

    def _apply_new_balance_impact(self):
        """Apply the balance impact with availability check"""
        tracking_record = self.env['share_investment.cash.bank.tracking'].search([], limit=1)
        if not tracking_record:
            tracking_record = self.env['share_investment.cash.bank.tracking'].create({})

        # Perform the check before applying changes
        self._check_balance_availability(tracking_record, self.amount, self.payment_method, self.payment_type)

        if self.payment_method == 'cash':
            if self.payment_type == 'receipt':
                tracking_record.total_cash += self.amount
            elif self.payment_type == 'return':
                tracking_record.total_cash -= self.amount
        elif self.payment_method == 'bank':
            if self.payment_type == 'receipt':
                tracking_record.total_bank += self.amount
            elif self.payment_type == 'return':
                tracking_record.total_bank -= self.amount

    def update_cash_bank_balances(self):
        """Update logic for the create method with availability check"""
        tracking_record = self.env['share_investment.cash.bank.tracking'].search([], limit=1)
        if not tracking_record:
            tracking_record = self.env['share_investment.cash.bank.tracking'].create({})

        for payment in self:
            # Verify balance
            payment._check_balance_availability(tracking_record, payment.amount, payment.payment_method,
                                                payment.payment_type)

            adjustment = payment.amount if payment.payment_type == 'receipt' else -payment.amount
            if payment.payment_method == 'cash':
                tracking_record.total_cash += adjustment
            elif payment.payment_method == 'bank':
                tracking_record.total_bank += adjustment
    def create_member_ledger_entry(self):
        # Search for existing ledger entry for this payment
        ledger_entry = self.env['share_investment.ledger'].search([
            ('payment_id', '=', self.id)
        ], limit=1)

        ledger_vals = {
            'member_id': self.member_id.id,
            'payment_id': self.id,  # Link to the payment record
            'transaction_type': self.payment_type,
            'payment_method': self.payment_method,
            'amount': self.amount,
            'date': self.date,
            'currency_id': self.currency_id.id,
        }

        if ledger_entry:
            # Update existing ledger entry
            ledger_entry.write(ledger_vals)
        else:
            # Create new ledger entry
            self.env['share_investment.ledger'].create(ledger_vals)

    def unlink(self):
        # Process each payment one by one to ensure proper cleanup
        for payment in self:
            # Adjust cash/bank balance first
            if payment.payment_method == 'cash':
                if payment.payment_type == 'receipt':
                    # Deduct the amount from total cash
                    tracking_record = self.env['share_investment.cash.bank.tracking'].search([], limit=1)
                    if tracking_record:
                        tracking_record.total_cash -= payment.amount
                elif payment.payment_type == 'return':
                    # Add the amount back to total cash
                    tracking_record = self.env['share_investment.cash.bank.tracking'].search([], limit=1)
                    if tracking_record:
                        tracking_record.total_cash += payment.amount

            elif payment.payment_method == 'bank':
                if payment.payment_type == 'receipt':
                    # Deduct the amount from total bank
                    tracking_record = self.env['share_investment.cash.bank.tracking'].search([], limit=1)
                    if tracking_record:
                        tracking_record.total_bank -= payment.amount
                elif payment.payment_type == 'return':
                    # Add the amount back to total bank
                    tracking_record = self.env['share_investment.cash.bank.tracking'].search([], limit=1)
                    if tracking_record:
                        tracking_record.total_bank += payment.amount

            # Delete the corresponding ledger entry
            ledger_entry = self.env['share_investment.ledger'].search([
                ('payment_id', '=', payment.id)
            ], limit=1)

            if ledger_entry:
                ledger_entry.unlink()

        # Now delete all payment records at once
        return super(Payment, self).unlink()

    def send_message(self):
        if not self.member_id.contact_number:
            raise ValidationError('No WhatsApp Number')

        month_name = dict(
            self._fields['payment_month_id'].selection
        ).get(self.payment_month_id)

        msg = (
            f"{self.member_id.name}  "
            f"താങ്കളുടെ {month_name} {self.payment_dates} ലെ "
            f"കുറിയുടെ പൈസ {self.amount} {self.payment_method} "
            f"കിട്ടി {self.date.strftime('%d-%m-%Y')}"
        )

        whatsapp_url = "https://api.whatsapp.com/send?phone=%s&text=%s" % (
            self.member_id.contact_number,
            msg
        )

        return {
            'type': "ir.actions.act_url",
            'target': 'new',
            'url': whatsapp_url
        }



    @api.onchange('date')
    def _onchange_date_set_month(self):
        if self.date:
            self.payment_month_id = self.date.strftime('%m')

