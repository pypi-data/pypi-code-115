from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from oauth.python.oauth import forms as oauth
from oauth.python.utils import send_mail, core_utils


class Login(View):
    template_name = 'oauth/login.html'
    context = {}

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect('/')

        self.context['login_form'] = oauth.LoginForm()
        return render(self.request, template_name=self.template_name, context=self.context)

    def post(self, *args, **kwargs):
        login_form = oauth.LoginForm(self.request.POST)
        if login_form.is_valid():
            user_authenticate = authenticate(self.request,
                                             username=login_form.cleaned_data.get('user_email'),
                                             password=login_form.cleaned_data.get('password'))
            if user_authenticate:
                login(self.request, user=user_authenticate)

                # TODO: Ajustar para home
                return redirect('oauth:dashboard')
        messages.error(self.request, 'Usuário ou senha inválidos.')
        return render(self.request, self.template_name, self.context)


class Register(View):
    template_name = 'oauth/register.html'
    context = {}

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect('/')

        self.context['form'] = oauth.RegisterForm()
        return render(self.request, self.template_name, self.context)

    def post(self, *args, **kwargs):
        form = oauth.RegisterForm(data=self.request.POST)

        if form.is_valid():
            user = User(
                first_name=form.cleaned_data.get('first_name'),
                last_name=form.cleaned_data.get('last_name'),
                username=form.cleaned_data.get('email'),
                email=form.cleaned_data.get('email')
            )
            user.set_password(form.cleaned_data.get('password'))
            user.save()

            messages.success(self.request, 'Conta criada com sucesso. Faça login!')
            return redirect('oauth:login')

        else:
            self.context['form'] = form
            return render(self.request, self.template_name, self.context)


class RestorePassword(View):
    template_name = 'oauth/restore-passwd.html'
    template_email = ''
    context = {}

    def get(self, *args, **kwargs):
        return render(self.request, self.template_name, self.context)

    def post(self, *args, **kwargs):
        try:
            user = get_object_or_404(User, email=self.request.POST.get('email'))
            password = core_utils.password_generator()
            user.set_password(password)
            user.save()
            send_mail.send_email(
                subject='Nova Senha',
                recipient_list=(user.email,),
                html_message=f'Sua nova senha é: <strong>{password}</strong>'
            )
            messages.success(self.request, 'Senha enviada para o e-mail informado.')
            return redirect('oauth:login')
        except Exception as error:
            messages.error(self.request, error)
            return redirect('oauth:restore-password')


class ChangePassword(View):
    template_name = 'oauth/change-password.html'
    context = {}

    def get(self, *args, **kwargs):
        self.context['form'] = oauth.ChangePasswordForm(self)
        return render(self.request, self.template_name, self.context)

    def post(self, *args, **kwargs):
        user = User.objects.get(username=self.request.user)
        form = oauth.ChangePasswordForm(user, data=self.request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data.get('password'))
            user.save()
            return redirect('oauth:dashboard')

        self.context['form'] = form
        return render(self.request, self.template_name, self.context)


class UpdateUserInfo(View):
    template_name = 'oauth/update.html'
    context = {}

    @staticmethod
    def __start__(user):
        user = User.objects.get(username=user)
        form = oauth.RegisterFormBase(instance=user)
        form.fields['email'].disabled = True
        return form

    def get(self, *args, **kwargs):
        user = self.request.user
        address = oauth.Address.objects.filter(user=user).first()

        self.context['form'] = oauth.RegisterFormBase(instance=user)
        self.context['info_form'] = oauth.AddressForm(instance=address or None)

        return render(self.request, self.template_name, self.context)

    def post(self, *args, **kwargs):
        user_form = oauth.RegisterFormBase(data=self.request.POST)
        address_form = oauth.AddressForm(data=self.request.POST)

        if user_form.is_valid():
            user = User.objects.get(username=self.request.user)
            user.first_name = user_form.cleaned_data.get('first_name')
            user.last_name = user_form.cleaned_data.get('last_name')
            user.save()

            if oauth.Address.objects.filter(user=user).exists():
                user_info = get_object_or_404(oauth.Address, user=user)
                address_form = oauth.AddressForm(self.request.POST, instance=user_info)

            if address_form.is_valid():
                user_info = address_form.save(commit=False)
                user_info.user = user
                user_info.save()
            else:
                self.context['info_form'] = address_form
                self.context['form'] = user_form
                return render(self.request, self.template_name, self.context)

        self.context['info_form'] = address_form
        self.context['form'] = user_form
        return render(self.request, self.template_name, self.context)


class Logout(View):
    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            logout(self.request)
        return redirect('oauth:login')


class Dashboard(View):
    template_name = ''

    def get(self, *args, **kwargs):
        return redirect('/')
