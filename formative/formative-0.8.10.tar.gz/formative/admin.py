from django import forms, urls
from django.contrib import admin, auth, messages
from django.contrib.admin.views.main import ChangeList
from django.core import mail
from django.db import connection
from django.db.models import Count, F, Q, Max
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template import Template
from django.template.response import TemplateResponse
from django.urls import path, reverse, NoReverseMatch
from django.utils import timezone
from django.utils.html import format_html
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin
from polymorphic.admin import (PolymorphicParentModelAdmin,
                               PolymorphicChildModelAdmin,
                               PolymorphicChildModelFilter)
import sys, importlib, time, types
from urllib.parse import unquote, parse_qsl

from .forms import ProgramAdminForm, FormAdminForm, StockBlockAdminForm, \
    CustomBlockAdminForm, CollectionBlockAdminForm, SubmissionAdminForm, \
    SubmissionItemAdminForm, EmailAdminForm, MoveBlocksAdminForm
from .models import Program, Form, FormLabel, FormBlock, FormDependency, \
    CustomBlock, CollectionBlock, SubmissionRecord
from .filetype import FileType
from .plugins import get_matching_plugin
from .signals import register_program_settings, register_form_settings
from .utils import send_email, submission_link


class FormativeAdminSite(admin.AdminSite):
    def __init__(self, *args, **kwargs):
        self.submissions_registered = None
        super().__init__(*args, **kwargs)
    
    def register_submission_models(self):
        if Form._meta.db_table in connection.introspection.table_names():
            for form in Form.objects.exclude(status=Form.Status.DRAFT):
                self.register(form.model, SubmissionAdmin)
                if form.item_model:
                    self.register(form.item_model, SubmissionItemAdmin)
        self.submissions_registered = True
    
    def catch_all_view(self, request, url):
        if not self.submissions_registered:
            self.get_app_list(request)
            return HttpResponseRedirect(request.get_full_path()) # better than 0
            # TODO a middleware is necessary to solve this?
        
        return super().catch_all_view(request, url)
    
    def get_app_list(self, request):
        if not self.submissions_registered: self.register_submission_models()
        
        # unlike normal Django, we might have had changes to the admin urls
        urls.clear_url_caches()
        if 'urls' in sys.modules: importlib.reload(sys.modules['urls'])
        
        return super().get_app_list(request)
    
    def app_index(self, request, *args, **kwargs):
        if not self.submissions_registered: self.get_app_list(request)
        
        return super().app_index(request, *args, **kwargs)


site = FormativeAdminSite()

site.register(auth.models.Group, auth.admin.GroupAdmin)
site.register(auth.models.User, auth.admin.UserAdmin)


@admin.register(Program, site=site)
class ProgramAdmin(admin.ModelAdmin, DynamicArrayMixin):
    list_display = ('name', 'created')
    form = ProgramAdminForm
    
    def get_fieldsets(self, request, obj=None):
        fields = self.get_fields(request, obj)
        
        main = (None, {'fields': fields})
        if not obj: return [main]
        
        responses = register_program_settings.send(self)
        admin_fields = { k: v for _, r in responses for k, v in r.items() }
        if not admin_fields: return [main]
        return [
            main,
            ('Options', {'fields': list(admin_fields)}),
        ]
    
    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        if obj: fields += ('slug',)
        return fields


class FormChangeList(ChangeList):
    def url_for_result(self, result):
        pk = getattr(result, self.pk_attname)
        url = reverse('admin:%s_formblock_formlist' % (self.opts.app_label,),
                       args=(int(pk),),
                       current_app=self.model_admin.admin_site.name)
        return url + '?page=1'


@admin.register(Form, site=site)
class FormAdmin(admin.ModelAdmin):
    list_display = ('name', 'program', 'created', 'modified')
    list_filter = ('program',)
    form = FormAdminForm
    
    def get_changelist(self, request, **kwargs):
        return FormChangeList
    
    def get_fieldsets(self, request, obj=None):
        fields = super().get_fields(request, obj)
        main_fields = ['program', 'name', 'slug', 'status', 'hidden']
        
        main = (None, {'fields': main_fields[:3] + main_fields[4:]})
        if not obj: return [main]
        
        for n in main_fields: fields.remove(n)
        main[1]['fields'] = main_fields
        
        ret = [
            main,
            ('Options', {'fields': fields}),
        ]
        responses = register_form_settings.send(obj)
        for receiver, response in responses:
            meta = get_matching_plugin(receiver.__module__)
            ret.append((meta.name, {'fields': list(response)}))
        return ret
    
    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        if obj:
            if obj.status == Form.Status.DRAFT: fields += ('status',)
            else: fields += ('program', 'slug')
        return fields
    
    def change_view(self, request, object_id, **kwargs):
        action, kwargs = None, {}
        if '_publish' in request.POST: action = 'publish'
        elif '_unpublish_confirmed' in request.POST: action = 'unpublish'
        
        if not action: return super().change_view(request, object_id, **kwargs)
        
        obj = self.get_object(request, object_id)
        getattr(obj, action)(**kwargs)
        
        return HttpResponseRedirect(request.get_full_path())
    
    def save_form(self, request, form, change):
        obj = super().save_form(request, form, change)
        if not change: return obj
        
        if obj.status == Form.Status.DRAFT:
            obj.modified = timezone.now()
        elif obj.status in (Form.Status.DISABLED, Form.Status.COMPLETED):
            if 'status' in form.changed_data: obj.completed = timezone.now()
        else: obj.completed = None
        
        return obj
        
    def response_change(self, request, obj):
        subs = []
        if obj.status != Form.Status.DRAFT:
            qs = obj.model.objects.all()
            if obj.item_model:
                qs = qs.annotate(num_items=Count('_item'))
                subs = qs.values_list('_email', 'num_items')
            else: subs = qs.values_list('_email')
        
        context = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'media': self.media,
            'object': obj,
            'submissions': subs,
            'title': 'Confirmation'
        }
#        if '_publish' in request.POST:
#            return TemplateResponse(request, 'admin/publish_confirmation.html',
#                                    context)
        if '_unpublish' in request.POST:
            request.current_app = self.admin_site.name
            template_name = 'admin/formative/unpublish_confirmation.html'
            return TemplateResponse(request, template_name, context)
        
        return super().response_change(request, obj)
    
    def response_post_save_change(self, request, obj):
        app_label = self.model._meta.app_label
        url = reverse('admin:%s_formblock_formlist' % (app_label,),
                      args=(obj.id,), current_app=self.admin_site.name)
        return HttpResponseRedirect(url)


@admin.register(FormLabel, site=site)
class FormLabelAdmin(admin.ModelAdmin):
    list_display = ('path', 'style', 'form')
    list_filter = ('form',)
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield= super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'text':
            attrs = formfield.widget.attrs
            attrs['class'], attrs['cols'] = 'vTextArea', 60
            formfield.widget = forms.Textarea(attrs=attrs)
        return formfield


class FormDependencyInline(admin.TabularInline):
    model = FormDependency
    extra = 0
    verbose_name_plural = 'dependency values'
    
    def has_add_permission(self, request, obj):
        if not obj: return False
        
        return obj.form.status == Form.Status.DRAFT
    
    def has_change_permission(self, request, obj):
        return self.has_add_permission(request, obj)
    
    def has_delete_permission(self, request, obj):
        return self.has_add_permission(request, obj)


class FormBlockBase:
    # only methods that can be safely overridden in either parent or child admin
    
    def get_fieldsets(self, request, obj=None):
        fields = list(dict.fromkeys(self.get_fields(request, obj)))
        fields.remove('dependence')
        fields.remove('negate_dependencies')
        fields.remove('no_review')
        
        main = (None, {'fields': fields})
        if not obj: return [main]
        return [
            main,
            ('Options', {'fields': ['no_review']}),
            ('Dependence', {'fields': ['dependence', 'negate_dependencies']})
        ]
    
    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        
        if obj and obj.form.status != Form.Status.DRAFT:
            fields += ('name', 'page', 'dependence', 'negate_dependencies')
        elif obj: fields += ('page',)
        
        return fields
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        form_id = request.GET.get('form_id')
        if form_id: form.form_id = form_id
        
        if obj and obj.form.status == Form.Status.DRAFT:
            # TODO: where would we modify form.fields instead?
            if 'dependence' in form.base_fields:
                qs = form.base_fields['dependence'].queryset
                qs = qs.filter(form=obj.form, page__gt=0)
                qs = qs.exclude(pk=obj.pk).exclude(page__gte=obj.page)
                form.base_fields['dependence'].queryset = qs
        
        return form
    
    def get_changeform_initial_data(self, request):
        changelist_filters = request.GET.get('_changelist_filters')
        if changelist_filters:
            filters = dict(parse_qsl(unquote(changelist_filters)))
            if 'page' in filters:
                return {'page': filters['page']}
        
        return {}
    
    def get_formsets_with_inlines(self, request, obj=None):
        for inline in self.get_inline_instances(request, obj):
            # only show the inline on the change form, not add:
            if not isinstance(inline, FormDependencyInline) or obj is not None:
                yield inline.get_formset(request, obj), inline
    
    def response_add(self, request, obj, **kwargs):
        if '_popup' in request.POST or '_continue' not in request.POST:
            return super().response_add(request, obj, **kwargs)
        
        opts = obj._meta
        model = opts.model_name
        if model in ('customblock', 'collectionblock'): model = 'formblock'
        url = reverse('admin:%s_%s_change' % (opts.app_label, model),
                      args=(obj.pk,), current_app=self.admin_site.name)
        
        preserved, args = request.GET.get('_changelist_filters'), {}
        if preserved: args['_changelist_filters'] = preserved
        args['form_id'] = obj.form.id
        url += '?' + urlencode(args)
        
        if 'get_url' in kwargs: return url
        return super().response_add(request, obj, post_url_continue=url)
    
    def response_change(self, request, obj):
        if '_popup' in request.POST or '_continue' not in request.POST:
            return super().response_change(request, obj)
        
        url = self.response_add(request, obj, get_url=True)
        return HttpResponseRedirect(url)
    
    def response_post_save_change(self, request, obj):
        app_label = self.model._meta.app_label
        form_id = request.GET.get('form_id')
        
        if not obj and not form_id:
            return super().response_post_save_change(request, obj)
        
        if not form_id: form_id = obj.form.id
        url = reverse('admin:%s_formblock_formlist' % (app_label,),
                      args=(form_id,), current_app=self.admin_site.name)
        changelist_filters = request.GET.get('_changelist_filters')
        if changelist_filters:
            filters = dict(parse_qsl(unquote(changelist_filters)))
            url += '?' + urlencode(filters)
        return HttpResponseRedirect(url)
    
    def response_post_save_add(self, request, obj):
        if request.GET.get('form_id'):
            return self.response_post_save_change(request, obj)
        return super().response_post_save_add(request, obj)
    
    def changeform_view(self, request, object_id=None, form_url='',
                        extra_context=None):
        form_id = request.GET.get('form_id')
        if form_id:
            form_arg = urlencode({'form_id': form_id})
            if form_url: form_url += '&' + form_arg
            else: form_url = '?' + form_arg
            
            if not extra_context: extra_context = {}
            name = get_object_or_404(Form, id=int(form_id)).name
            extra_context.update({'form_id': int(form_id), 'form_name': name})
            
            initial = self.get_changeform_initial_data(request)
            if 'page' in initial: extra_context['page'] = initial['page']
            else: extra_context['page'] = None
        
        return super().changeform_view(request, object_id, form_url,
                                       extra_context)
    
    def try_form_id(self, request, match):
        form = None
        if 'form_id' in match.kwargs: pk = match.kwargs['form_id']
        else: pk = request.GET.get('form_id')
        if not pk: return form
        
        try: form = Form.objects.get(pk=pk)
        except Form.DoesNotExist: pass
        return form
    
    def has_add_permission(self, request):
        match, app_label = request.resolver_match, self.model._meta.app_label
        # this will hide add button when we don't have the form_id
        if match and match.url_name == f'{app_label}_formblock_changelist':
            return False
        # or when the form is not a draft
        pages = (f'{app_label}_formblock_{n}' for n in ('formlist', 'change'))
        if match and match.url_name in pages:
            form = self.try_form_id(request, match)
            if form and form.status != Form.Status.DRAFT: return False
        
        return super().has_add_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        return self.has_add_permission(request)


class PageListFilter(admin.SimpleListFilter):
    title = 'page'
    parameter_name = 'page'
    template = 'admin/formative/formblock/filter.html'
    
    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request).distinct().order_by('page')
        return [ (p, f'Page {p}' if p else 'Auto-created blocks')
                 for p in qs.values_list('page', flat=True) ]
    
    def queryset(self, request, queryset):
        return queryset.filter(page=self.value())


@admin.action(description='Move to different page')
def move_blocks_action(modeladmin, request, queryset):
    if '_move' in request.POST:
        page, n = request.POST['page'], 0
        blocks, cur_page = queryset[0].form.blocks, queryset[0].page
        last_rank = blocks.filter(page=cur_page).aggregate(r=Max('_rank'))['r']
        for block in queryset.order_by('_rank'):
            block = FormBlock.objects.get(pk=block.pk) # clear side effects;
            block._rank = last_rank
            block.save() # it's now at the end of its page;
            block.page, block._rank = page, None # and then move to the new one,
            block.save() # so that the others on the old page are left sorted
            n, last_rank = n + 1, last_rank - 1
        
        msg = f'Moved {n} blocks to page {page}'
        modeladmin.message_user(request, msg, messages.SUCCESS)
        
        return HttpResponseRedirect(request.get_full_path())
    
    template_name = 'admin/formative/move_page.html'
    request.current_app = site.name
    min_page = max(block.min_allowed_page() for block in queryset)
    last_page = queryset[0].form.blocks.aggregate(p=Max('page'))['p']
    max_page = min(block.max_allowed_page(last_page) for block in queryset)
    new = max_page == last_page
    context = {
        **site.each_context(request),
        'opts': modeladmin.model._meta,
        'media': modeladmin.media,
        'blocks': queryset,
        'movable': queryset[0].form.status == Form.Status.DRAFT,
        'form': MoveBlocksAdminForm(max_page, min_page=min_page, new_page=new),
        'title': 'Move Blocks'
    }
    return TemplateResponse(request, template_name, context)

@admin.register(FormBlock, site=site)
class FormBlockAdmin(FormBlockBase, PolymorphicParentModelAdmin,
                     DynamicArrayMixin):
    child_models = (FormBlock, CustomBlock, CollectionBlock)
    list_display = ('_rank', 'name', 'block_type', 'dependence', 'labels_link')
    list_display_links = ('name',)
    list_editable = ('_rank',)
    list_filter = (PageListFilter,)
    form = StockBlockAdminForm
    inlines = [FormDependencyInline]
    actions = [move_blocks_action]
    sortable_by = ()
    polymorphic_list = True
    
    @admin.display(description='labels')
    def labels_link(self, obj):
        app_label = self.model._meta.app_label
        url = reverse('admin:%s_formlabel_changelist' % (app_label,),
                      current_app=self.admin_site.name)
        url += f'?form__id__exact={obj.form.pk}&path__startswith={obj.name}'
        return format_html('<a href="{}">{} labels</a>', url, obj.num_labels)
    
    @admin.display(description='type')
    def type(self, obj):
        # read-only version of the StockBlockAdminForm type field
        return obj.options['type']
    
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        fields = fieldsets[0][1]['fields']
        
        if not obj: return fieldsets
        
        options = fieldsets[1][1]['fields']
        admin_fields = obj.stock.admin_fields().keys()
        readonly_fields = obj.stock.admin_published_readonly()
        if obj.form.status == Form.Status.DRAFT:
            # special case: not really an option, so it goes on the general tab
            if 'choices' in admin_fields: fields.append('choices')
            options += [ f for f in admin_fields if f != 'choices' ]
        else:
            options += [ f for f in admin_fields if f not in readonly_fields ]
        
        sets = [(None, {'fields': fields}), ('Options', {'fields': options})] 
        return sets + fieldsets[2:]
    
    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        
        if not obj: return fields
        fields += ('type',)
        
        if obj.form.status != Form.Status.DRAFT:
            for field, label in obj.stock.admin_published_readonly().items():
                def field_callable(f, l):
                    @admin.display(description=l)
                    def callable(self, obj):
                        if f not in obj.options: return '-'
                        return obj.options[f]
                    return callable
                
                setattr(self, field,
                        types.MethodType(field_callable(field, label), self))
                fields += (field,)
        
        return fields
    
    def get_urls(self):
        urls = super().get_urls()
        
        url = path('form/<int:form_id>/', self.formlist_view,
                   name='%s_formblock_formlist' % (self.model._meta.app_label,))
        return [url] + urls
    
    def formlist_view(self, request, form_id, **kwargs):
        page = request.GET.get('page')
        if not page: return HttpResponseRedirect(request.path + '?page=1')
        
        name = get_object_or_404(Form, id=int(form_id)).name
        context = {'form_id': form_id, 'form_name': name}
        return self.changelist_view(request, extra_context=context)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        match, app_label = request.resolver_match, self.model._meta.app_label
        if match and match.url_name == f'{app_label}_formblock_formlist':
            qs = qs.filter(form_id=match.kwargs['form_id'])
        
        path_filter = Q(form__label__path__startswith=F('name'))
        qs = qs.annotate(num_labels=Count('form__label', filter=path_filter))
        return qs
    
    def get_changelist_form(self, request, **kwargs):
        class HiddenWithHandleInput(forms.HiddenInput):
            template_name = 'admin/formative/widgets/hidden_with_handle.html'
        
        kwargs['widgets'] = {'_rank': HiddenWithHandleInput}
        return super().get_changelist_form(request, **kwargs)
    
    def change_view(self, *args, **kwargs):
        # we still have the bulk action for delete - it redirects properly
        kwargs['extra_context'] = {'show_delete': False,
                                   'show_save_and_add_another': False}
        return super().change_view(*args, **kwargs)
    
    def get_preserved_filters(self, request):
        match, app_label = request.resolver_match, self.model._meta.app_label
        
        # we have to reimplement, because of our custom changelist view
        if self.preserve_filters and match:
            current_url = f'{match.app_name}:{match.url_name}'
            changelists = [ f'admin:{app_label}_formblock_{n}'
                            for n in ('formlist', 'changelist') ]
            if current_url in changelists: preserved = request.GET.urlencode()
            else: preserved = request.GET.get('_changelist_filters')
            
            args = {}
            if preserved: args['_changelist_filters'] = preserved
            if current_url == changelists[0]:
                args['form_id'] = match.kwargs['form_id']
            return urlencode(args)
        return ''


class FormBlockChildAdmin(FormBlockBase, PolymorphicChildModelAdmin):
    base_model = FormBlock
    inlines = [FormDependencyInline]


@admin.register(CustomBlock, site=site)
class CustomBlockAdmin(FormBlockChildAdmin, DynamicArrayMixin):
    form = CustomBlockAdminForm
    radio_fields = {'type': admin.VERTICAL}
    
    def choices(self, obj):
        return obj.options['choices']
    
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        fields = fieldsets[0][1]['fields']
        names = ['type', 'required', 'num_lines', 'min_chars', 'max_chars',
                 'min_words', 'max_words']
        
        if not obj:
            return [(None, {'fields': ['name', 'page', 'type']})]
        
        options = fieldsets[1][1]['fields']
        if obj.type == CustomBlock.InputType.TEXT: add = names[:1] + names[2:]
        elif obj.dependence: options.append('default_value')
        if obj.type == CustomBlock.InputType.BOOLEAN: add = names[:1]
        elif obj.type == CustomBlock.InputType.CHOICE:
            add = names[:2] + ['choices']
        elif obj.type == CustomBlock.InputType.NUMERIC:
            add = names[:2]
            options += ['numeric_min', 'numeric_max']
        
        names += ['choices', 'numeric_min', 'numeric_max', 'default_value']
        main = [ f for f in fields if f not in names ] + add
        
        sets = [(None, {'fields': main}), ('Options', {'fields': options})]
        return sets + fieldsets[2:]
    
    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        
        if obj: fields += ('type',)
        if obj and obj.form.status != Form.Status.DRAFT:
            if obj.type == CustomBlock.InputType.TEXT:
                fields += ('num_lines', 'max_chars')
            elif obj.type == CustomBlock.InputType.CHOICE:
                fields += ('choices',)
        return fields


@admin.register(CollectionBlock, site=site)
class CollectionBlockAdmin(FormBlockChildAdmin, DynamicArrayMixin):
    form = CollectionBlockAdminForm
    
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        fields = fieldsets[0][1]['fields']
        names = ['fixed', 'name1', 'name2', 'name3', 'has_file',
                 'min_items', 'max_items', 'file_optional']
        
        if not obj: add = names[:5]
        elif obj.fixed: add = names[:4] + ['choices']
        elif not obj.has_file: add = names[:6]
        else: add = names[:]
        
        main = ['name', 'page'] + add
        if not obj: return [(None, {'fields': main})]
        
        options = fieldsets[1][1]['fields']
        names += ['name', 'page', 'file_types', 'max_filesize',
                  'autoinit_filename', 'choices', 'wide']
        options += [ f for f in fields if f not in names ]
        if obj.has_file:
            options += ['file_types', 'max_filesize', 'autoinit_filename']
            total, processing = False, {}
            for name in obj.allowed_filetypes() or []:
                filetype = FileType.by_type(name)()
                if filetype.admin_limit_fields(): options.append(name)
                if filetype.admin_processing_fields(): processing[name] = True
                if filetype.admin_total_fields(): total = True
            if total: options.append('total')
            for name in processing: options.append(name + '_proc')
        
        if obj.name1 and obj.name2: options.append('wide')
        
        sets = [(None, {'fields': main}), ('Options', {'fields': options})]
        return sets + fieldsets[2:]
    
    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        
        if obj: fields += ('fixed', 'has_file')
        if obj and obj.form.status != Form.Status.DRAFT:
            fields += ('name1', 'name2', 'name3')
        
        return fields


class SubmittedListFilter(admin.SimpleListFilter):
    title = 'status'
    parameter_name = '_submitted'
    
    def lookups(self, request, model_admin):
        return (('yes', 'submitted'), ('no', 'unsubmitted'))
    
    def queryset(self, request, queryset):
        if self.value() == 'yes': return queryset.exclude(_submitted=None)
        if self.value() == 'no': return queryset.filter(_submitted=None)


EMAILS_PER_SECOND = 10

@admin.action(description='Send an email to applicants')
def send_email_action(modeladmin, request, queryset):
    if '_send' in request.POST:
        # TODO: celery task
        subject = Template(request.POST['subject'])
        content = Template(request.POST['content'])
        
        iterator = queryset.iterator()
        batch, form, last_time, done, n = [], None, None, False, 0
        while not done:
            submission = next(iterator, None)
            if not submission: done = True
            else: batch.append(submission)
            
            if len(batch) == EMAILS_PER_SECOND or done:
                if last_time:
                    this_time = time.time()
                    remaining = last_time + 1 - this_time
                    if remaining > 0: time.sleep(remaining)
                last_time = time.time()
                
                with mail.get_connection() as conn:
                    for sub in batch:
                        if not form: form = sub._get_form()
                        context = {
                            'submission': sub, 'form': form,
                            'submission_link': submission_link(sub, form)
                        }
                        if sub._submitted: sub._update_context(form, context)
                        
                        n += 1
                        send_email(content, sub._email, subject,
                                   context=context, connection=conn)
                batch = []
        
        msg = f'Emails sent to {n} recipients.'
        modeladmin.message_user(request, msg, messages.SUCCESS)
        
        return HttpResponseRedirect(request.get_full_path())
    
    form = queryset[0]._get_form()
    template_name = 'admin/formative/email_applicants.html'
    request.current_app = site.name
    context = {
        **site.each_context(request),
        'opts': modeladmin.model._meta,
        'media': modeladmin.media,
        'submissions': queryset,
        'form': EmailAdminForm(form=form),
        'email_templates': form.email_templates(),
        'title': 'Email Applicants'
    }
    return TemplateResponse(request, template_name, context)
    

class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('_email', '_created', '_modified', '_submitted')
    list_filter = ('_email', SubmittedListFilter)
    readonly_fields = ('_submitted', 'items_index',)
    form = SubmissionAdminForm
    actions = [send_email_action]
    
    @admin.display(description='items')
    def items_index(self, obj):
        app, name = self.model._meta.app_label, self.model._meta.model_name
        args = f'?_submission___id__exact={obj._id}'
        try:
            url = reverse('admin:%s_%s_changelist' % (app, name + '_i'),
                          current_app=self.admin_site.name) + args
        except NoReverseMatch: return ''
        
        return mark_safe(f'<a href="{url}">items listing</a>')
    
    def change_view(self, request, object_id, **kwargs):
        action, kwargs = None, {}
        if '_submit_confirmed' in request.POST: action = 'submit'
        elif '_unsubmit_confirmed' in request.POST: action = 'unsubmit'
        
        if not action:
            kwargs['extra_context'] = {'model_is_submission': True}
            return super().change_view(request, object_id, **kwargs)
        
        obj = self.get_object(request, object_id)
        rec, rtype = None, SubmissionRecord.RecordType.SUBMISSION
        try: rec = SubmissionRecord.objects.get(submission=obj._id, type=rtype)
        except SubmissionRecord.DoesNotExist: pass
        
        if action == 'submit':
            if not rec: obj._get_form().submit_submission(obj)
            else:
                obj._submit()
                rec.deleted = False
        else:
            obj._submitted = None
            obj.save()
            if rec: rec.deleted = True
        if rec: rec.save()
        return HttpResponseRedirect(request.get_full_path())
    
    def response_change(self, request, obj):
        context = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'media': self.media,
            'object': obj,
            'title': 'Confirmation'
        }
        template_name = 'admin/formative/submit_confirmation.html'
        if '_submit' in request.POST or '_unsubmit' in request.POST:
            request.current_app = self.admin_site.name
            if '_submit' in request.POST: context['submit'] = True
            else: context['unsubmit'] = True
            
            return TemplateResponse(request, template_name, context)
        
        return super().response_change(request, obj)
    
    def view_on_site(self, obj):
        url = obj._get_absolute_url()
        if obj._submitted: url += 'review'
        return url


class SubmissionItemAdmin(admin.ModelAdmin):
    list_display = ('_id', '_submission', '_collection', '_rank', '_file')
    list_filter = (
        '_submission', '_collection',
        ('_file', admin.EmptyFieldListFilter)
    )
    readonly_fields = ('_submission', '_block', '_rank')
    ordering = ('_submission', '_collection', '_block', '_rank')
    form = SubmissionItemAdminForm
    
    def has_add_permission(self, request):
        return False
