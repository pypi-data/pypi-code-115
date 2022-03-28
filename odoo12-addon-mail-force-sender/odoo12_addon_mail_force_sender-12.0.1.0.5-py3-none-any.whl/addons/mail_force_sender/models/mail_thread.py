from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)


class MailThread(models.AbstractModel):
    _name = "mail.thread"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    @api.multi
    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, body='', subject=None,
                     message_type='notification', subtype=None,
                     parent_id=False, attachments=None,
                     notif_layout=False, add_sign=True, model_description=False,
                     mail_auto_delete=True, **kwargs):
        kwargs['email_from'] = (
            self.sudo().env['ir.config_parameter'].get_param('mail_force_sender.sender_email_address')
        )
        return super().message_post(
            body=body, subject=subject, message_type=message_type,
            subtype=subtype, parent_id=parent_id, attachments=attachments,
            notif_layout=notif_layout, add_sign=add_sign,
            mail_auto_delete=mail_auto_delete, model_description=model_description, **kwargs)

