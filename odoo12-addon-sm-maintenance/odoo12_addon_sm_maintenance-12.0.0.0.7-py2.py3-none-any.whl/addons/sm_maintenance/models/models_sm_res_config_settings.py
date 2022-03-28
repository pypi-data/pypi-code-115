# -*- coding: utf-8 -*-
from odoo import fields, models, _

class ResConfigSettings(models.TransientModel):
  _inherit = 'res.config.settings'

  ''' Load Data Configuration '''
  sm_user_person_group = fields.Char(
    related='company_id.sm_user_person_group',
    string=_("Person Group"),
    readonly=False)
  sm_user_person_group_prepayment = fields.Char(
    related='company_id.sm_user_person_group_prepayment',
    string=_("Person Group Prepayment"),
    readonly=False)
  sm_user_person_default_language = fields.Char(
    related='company_id.sm_user_person_default_language',
    string=_("Person Default Language"),
    readonly=False)
  sm_user_allowed_user_langs_es = fields.Char(
    related='company_id.sm_user_allowed_user_langs_es',
    string=_("Allowed User Langs ES"),
    readonly=False)
  sm_user_allowed_user_langs_ca = fields.Char(
    related='company_id.sm_user_allowed_user_langs_ca',
    string=_("Allowed User Langs CA"),
    readonly=False)
  sm_tariff_month_duration_welcome = fields.Char(
    related='company_id.sm_tariff_month_duration_welcome',
    string=_("Tariff Month Duration Welcome"),
    readonly=False)
  sm_timezone = fields.Char(
    related='company_id.sm_timezone',
    string=_("Timezone"),
    readonly=False)
  sm_system_project_id = fields.Integer(
    related='company_id.sm_system_project_id',
    string=_("System Project ID"),
    readonly=False)
  sm_zip_api_key = fields.Char(
    related='company_id.sm_zip_api_key',
    string=_("ZIP API Key"),
    readonly=False)
