from django.contrib import admin

# Register your models here.
from .models import about_user, bug, bug_client, campus, change_task, change_task_block, contact_history, cost,\
    customer, customer_campus, document, document_permission, email_content, email_contact, folder,\
    group_permission, group, kanban_board, kanban_card, kanban_column, kanban_level, kudos, list_of_amount_type,\
    list_of_bug_client, list_of_currency, list_of_contact_type, list_of_country_region, list_of_country,\
    list_of_lead_source, list_of_opportunity_stage,\
    list_of_quote_stage, list_of_requirement_item_status,\
    list_of_requirement_item_type, list_of_requirement_status, list_of_requirement_type, list_of_tax,\
    list_of_title, nearbeach_option, object_assignment,\
    object_note, opportunity, organisation, permission_set, project_customer, project, quote, request_for_change,\
    request_for_change_group_approval, request_for_change_stakeholder, requirement, requirement_customer,\
    requirement_item, tag, tag_assignment, task_action, task_customer, task, timesheet, to_do, user_group,\
    user_want, user_weblink, whiteboard

admin.site.register(about_user)
admin.site.register(bug)
admin.site.register(bug_client)
admin.site.register(campus)
admin.site.register(change_task)
admin.site.register(change_task_block)
admin.site.register(contact_history)
admin.site.register(cost)
admin.site.register(customer)
admin.site.register(customer_campus)
admin.site.register(document)
admin.site.register(document_permission)
admin.site.register(email_content)
admin.site.register(email_contact)
admin.site.register(folder)
admin.site.register(group_permission)
admin.site.register(group)
admin.site.register(kanban_board)
admin.site.register(kanban_card)
admin.site.register(kanban_column)
admin.site.register(kanban_level)
admin.site.register(kudos)
admin.site.register(list_of_amount_type)
admin.site.register(list_of_bug_client)
admin.site.register(list_of_currency)
admin.site.register(list_of_contact_type)
admin.site.register(list_of_country_region)
admin.site.register(list_of_country)
admin.site.register(list_of_lead_source)
admin.site.register(list_of_opportunity_stage)
admin.site.register(list_of_quote_stage)
admin.site.register(list_of_requirement_item_status)
admin.site.register(list_of_requirement_item_type)
admin.site.register(list_of_requirement_status)
admin.site.register(list_of_requirement_type)
admin.site.register(list_of_tax)
admin.site.register(list_of_title)
admin.site.register(nearbeach_option)
admin.site.register(object_assignment)
admin.site.register(object_note)
admin.site.register(opportunity)
# admin.site.register(opportunity_connection)
admin.site.register(organisation)
admin.site.register(permission_set)
admin.site.register(project_customer)
# admin.site.register(project_history)
# admin.site.register(project_stage)
# admin.site.register(project_task)
admin.site.register(project)
admin.site.register(quote)
admin.site.register(request_for_change)
admin.site.register(request_for_change_group_approval)
admin.site.register(request_for_change_stakeholder)
admin.site.register(requirement)
admin.site.register(requirement_customer)
admin.site.register(requirement_item)
# admin.site.register(stage)
admin.site.register(tag)
admin.site.register(tag_assignment)
admin.site.register(task_action)
admin.site.register(task_customer)
# admin.site.register(task_history)
admin.site.register(task)
admin.site.register(timesheet)
admin.site.register(to_do)
admin.site.register(user_group)
admin.site.register(user_want)
admin.site.register(user_weblink)
admin.site.register(whiteboard)
