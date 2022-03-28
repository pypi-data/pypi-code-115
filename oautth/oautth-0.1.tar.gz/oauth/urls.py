from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

app_name = 'oauth'

urlpatterns = [
    path('login/', views.Login.as_view(), name='login'),
    path('register/', views.Register.as_view(), name='register'),
    path('restore-password/', views.RestorePassword.as_view(), name='restore-password'),
    path('change-password/', login_required(views.ChangePassword.as_view(), login_url='oauth:login'),
         name='change-password'),
    path('update-account/', login_required(views.UpdateUserInfo.as_view(), login_url='oauth:login'),
         name='update-account'),
    path('logout/', views.Logout.as_view(), name='logout'),
    path('', views.Dashboard.as_view(), name='dashboard'),
]
