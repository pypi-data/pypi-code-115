# -*- coding: utf-8 -*-
import pytz
from datetime import datetime

from odoo.addons.base_iban.models.res_partner_bank import \
  normalize_iban, pretty_iban, _map_iban_template


class sm_utils(object):

  @staticmethod
  def get_today_date():
    timezone = pytz.timezone('Europe/Madrid')
    date_time = datetime.now(tz=timezone)
    return datetime.date(date_time)

  @staticmethod
  def send_email_from_template(parent, template):
    company = parent.env.user.company_id
    mail_template = getattr(company, template)
    email_values = {'send_from_code': True}
    mail_template.with_context(email_values).send_mail(parent.id,force_send=True)

  @staticmethod
  def diff_month(d1, d2):
    return (d1.year - d2.year) * 12 + d1.month - d2.month

  @staticmethod
  def record_exists(parent, child_model, relation_name, name_query):
    if relation_name:
      relation = getattr(parent, relation_name)
      if relation.id:
        return True
    else:
      existing_model = parent.env[child_model].sudo().search(
        [('name', '=', name_query)])
      if existing_model.id:
        return True
    return False

  @staticmethod
  def get_create_existing_model(model_env, query, creation_data=False):
    existing_model = model_env.search(query)
    create_model = True
    if existing_model:
      if existing_model.exists():
        model = existing_model
        create_model = False
    if create_model:
      if creation_data:
        model = model_env.create(creation_data)
    return model

  @staticmethod
  def delete_existing_model(model_env, query):
    existing_model = model_env.search(query)
    if existing_model:
      if existing_model.exists():
        existing_model.unlink()
        return True
    return False

  @staticmethod
  def create_system_task(parent,task_name=False,task_description=False):
    company = parent.env.user.company_id
    parent.env['project.task'].create({
      'name': task_name,
      'description': task_description,
      'project_id': company.sm_system_project_id
    })

  @staticmethod
  def is_module_active(contextself, module_name):
    module = contextself.env['ir.module.module'].search(
      [('name', '=', module_name), ('state', '=', 'installed')])
    return module.exists()

  @staticmethod
  def validate_iban(parent,iban):
    if iban:
      # Code copied from base_bank_from_iban module:
      # https://github.com/OCA/community-data-files/blob/12.0/base_bank_from_iban/models/res_partner_bank.py#L13  # noqa
      acc_number = pretty_iban(normalize_iban(iban)).upper()
      country_code = acc_number[:2].lower()
      iban_template = _map_iban_template[country_code]
      first_match = iban_template[2:].find('B') + 2
      last_match = iban_template.rfind('B') + 1
      bank_code = acc_number[first_match:last_match].replace(' ', '')
      bank = parent.env['res.bank'].search([
        ('code', '=', bank_code),
        ('country.code', '=', country_code.upper()),
      ], limit=1)
      if bank:
        return True
    return False

  @staticmethod
  def local_to_utc_datetime(local_date_str):
    mad_tz = pytz.timezone('Europe/Madrid')
    utc_tz = pytz.timezone('UTC')
    local_date = datetime.strptime(local_date_str, "%Y-%m-%d %H:%M:%S")
    local_date_localized = mad_tz.localize(local_date)
    return local_date_localized.astimezone(utc_tz)

  def utc_to_local_datetime(utc_date_str):
    mad_tz = pytz.timezone('Europe/Madrid')
    utc_tz = pytz.timezone('UTC')
    utc_date = datetime.strptime(utc_date_str, "%Y-%m-%d %H:%M:%S")
    utc_date_localized = utc_tz.localize(utc_date)
    return utc_date_localized.astimezone(mad_tz)
