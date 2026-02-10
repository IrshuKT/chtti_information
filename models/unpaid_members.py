from odoo import models,fields,_
from odoo.exceptions import ValidationError


class UnpaidMembersWizard(models.TransientModel):
    _name = 'share_investment.unpaid.wizard'
    _description = 'Find Unpaid Members'

    payment_month_id = fields.Selection(
        [
            ('01', 'January'), ('02', 'February'), ('03', 'March'),
            ('04', 'April'), ('05', 'May'), ('06', 'June'),
            ('07', 'July'), ('08', 'August'), ('09', 'September'),
            ('10', 'October'), ('11', 'November'), ('12', 'December'),
        ],
        string="Payment Month",
        required=True
    )

    payment_day = fields.Selection(
        [('10', '10'), ('20', '20'), ('30', '30'), ('all', 'All')],
        string="Payment Day",
        default='all',
        required=True
    )

    # -------------------------
    # INTERNAL: get unpaid members
    # -------------------------

    def _get_all_unpaid_members(self):
        domain = [('payment_month_id', '=', self.payment_month_id)]
        if self.payment_day != 'all':
            domain.append(('payment_dates', '=', self.payment_day))

        paid_members = self.env['share_investment.payment'].search(
            domain
        ).mapped('member_id')

        return self.env['share_investment.member'].search([
            ('id', 'not in', paid_members.ids),
            ('contact_number', '!=', False),
        ])

    def _get_unreminded_unpaid_members(self):
        return self._get_all_unpaid_members().filtered(
            lambda m: not m.reminder_sent
        )


    def _get_unpaid_members(self):
        domain = [('payment_month_id', '=', self.payment_month_id)]
        if self.payment_day != 'all':
            domain.append(('payment_dates', '=', self.payment_day))

        paid_members = self.env['share_investment.payment'].search(
            domain
        ).mapped('member_id')

        return self.env['share_investment.member'].search([
            ('id', 'not in', paid_members.ids),
            ('contact_number', '!=', False),
            ('reminder_sent', '=', False),
        ])

    # -------------------------
    # SEND FIRST / NEXT REMINDER
    # -------------------------
    def action_send_reminder(self):
        self.ensure_one()

        unpaid_members = self._get_unreminded_unpaid_members()
        if not unpaid_members:
            raise ValidationError(_("All reminders sent 🎉"))

        member = unpaid_members[0]

        month_name = dict(
            self._fields['payment_month_id'].selection
        ).get(self.payment_month_id)

        pending_days = (
            "10, 20, 30" if self.payment_day == 'all' else self.payment_day
        )

        msg = (
            f"റിമൈൻഡർ 🙏\n"
            f"{member.name} ജി,\n"
            f"താങ്കളുടെ {month_name} മാസം {pending_days} ലെ "
            f"കുറിയുടെ പൈസ ഇതുവരെ ലഭിച്ചിട്ടില്ല.\n"
            f"ദയവായി അടയ്ക്കുവാൻ അഭ്യർത്ഥിക്കുന്നു."
        )

        whatsapp_url = "https://api.whatsapp.com/send?phone=%s&text=%s" % (
            member.contact_number,
            msg
        )

        member.reminder_sent = True  # ✅ only reminder state

        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': whatsapp_url
        }

    # -------------------------
    # RESET (new month)
    # -------------------------
    def action_reset_reminders(self):
        members = self.env['share_investment.member'].search([])
        members.write({'reminder_sent': False})

    def action_find_unpaid(self):
        self.ensure_one()

        unpaid_members = self._get_all_unpaid_members()

        if not unpaid_members:
            raise ValidationError(_("Everyone has paid 🎉"))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Unpaid Members'),
            'res_model': 'share_investment.member',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', unpaid_members.ids)],
        }
