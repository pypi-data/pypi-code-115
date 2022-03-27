from django.contrib import admin
from django.urls import path
from jauth_example.urls import urlpatterns as jauth_example_urlpatterns


urlpatterns = [
    path('admin/', admin.site.urls),
] + jauth_example_urlpatterns
