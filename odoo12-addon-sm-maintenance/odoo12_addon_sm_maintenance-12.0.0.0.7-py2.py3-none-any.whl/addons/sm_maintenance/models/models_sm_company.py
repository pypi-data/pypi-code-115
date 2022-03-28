# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.translate import _


class sm_company(models.Model):
  _inherit = 'res.company'

  ''' Load Data Configuration '''
  sm_user_person_group = fields.Char(string=_("Person Group"))
  sm_user_person_group_prepayment = fields.Char(string=_("Person Group Prepayment"))
  sm_user_person_default_language = fields.Char(string=_("Person Default Language"))
  sm_user_allowed_user_langs_es = fields.Char(string=_("Allowed User Langs ES"))
  sm_user_allowed_user_langs_ca = fields.Char(string=_("Allowed User Langs CA"))
  sm_tariff_month_duration_welcome = fields.Char(string=_("Tariff Month Duration Welcome"))
  sm_timezone = fields.Char(string=_("Timezone"))
  sm_system_project_id = fields.Integer(string=_("System Project ID"))
  sm_zip_api_key = fields.Char(string=_("ZIP API Key"))