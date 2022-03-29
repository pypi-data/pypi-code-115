from django.apps import apps
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from django.views import View


class AdminSingleDeleteView(View):
    model = None
    object_id_list = None
    next = None
    object_list = []

    def get(self, request, *args, **kwargs):
        if request.GET.get('next') is None:
            raise KeyError(str(_("key next must be included in request")))

        if kwargs.get('pk', None):
            self.object_id_list = kwargs['pk'].split(',')
            self.model = apps.get_model(kwargs['app_label'], kwargs['model'])
        for object_id in self.object_id_list:
            self.object_list.append(self.model.objects.get(id=int(object_id)))
        return render(request, 'softdelete/delete_confirmation.html', {
            'content': self.object_list,
            'next': request.GET.get('next'),
        })

    def post(self, request, *args, **kwargs):
        if kwargs.get('pk', None):
            self.object_id_list = kwargs['pk'].split(',')
            self.model = apps.get_model(kwargs['app_label'], kwargs['model'])
        self.model.objects.filter(pk__in=self.object_id_list).delete()
        return redirect(request.GET.get('next'))
