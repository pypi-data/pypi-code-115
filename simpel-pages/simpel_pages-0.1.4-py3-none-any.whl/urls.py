from django.urls import path

from . import views

urlpatterns = [
    path("", views.simpelpage, name="simpelpage"),
    path("<path:url>", views.simpelpage, name="simpelpage"),
]
