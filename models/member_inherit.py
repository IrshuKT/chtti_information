import urllib

from odoo import models,fields
from odoo.exceptions import ValidationError


class InheritMember(models.Model):

    _inherit = 'share_investment.member'



    def send_random_msg(self):
        self.ensure_one()

        if not self.contact_number:
            raise ValidationError('No WhatsApp Number')

        msg = f" *പ്രിയ {self.name} അപ്പൊ ഇന്നത്തെ ഭാഗ്യവാൻ Chithra*"
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