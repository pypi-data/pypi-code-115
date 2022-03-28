from django.core.exceptions import ValidationError
from django import forms
from oauth.python.utils import core_utils
from django.contrib.auth.models import User
from oauth.models import Address

CSS_CLASSES = {
    'form-control': 'form-control'
}


class LoginForm(forms.Form):
    user_email = forms.CharField(widget=forms.TextInput(attrs={
        'class': CSS_CLASSES.get('form-control'),
        'placeholder': 'E-mail'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': CSS_CLASSES.get('form-control'),
        'placeholder': 'Password',
    }))


class PasswordForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': CSS_CLASSES.get('form-control'),
        'placeholder': 'Senha',
    }), required=False)
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': CSS_CLASSES.get('form-control'),
        'placeholder': 'Confirme a senha',
    }), required=False)

    def clean(self, *args, **kwargs):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')

        if core_utils.is_empty((password)):
            raise ValidationError({'password': 'Preencha todos os campos.'})

        if core_utils.is_empty((password2)):
            raise ValidationError({'password2': 'Preencha todos os campos. 2'})

        if password != password2:
            raise ValidationError({'password': 'Senhas não correspondem'})


class RegisterFormBase(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        labels = {'first_name': 'Primeiro Nome', 'last_name': 'Sobrenome'}
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': CSS_CLASSES.get('form-control'),
                'placeholder': 'Primeiro nome',
                'required': 'required'
            }),
            'last_name': forms.TextInput(attrs={
                'class': CSS_CLASSES.get('form-control'),
                'placeholder': 'Sobrenome',
                'required': 'required'
            }),
            'email': forms.EmailInput(attrs={
                'class': CSS_CLASSES.get('form-control'),
                'placeholder': 'email@example.com',
                'required': 'required'
            })
        }

    def clean(self, *args, **kwargs):
        first_name = self.cleaned_data.get('first_name')
        last_name = self.cleaned_data.get('last_name')
        if core_utils.is_empty((first_name, last_name)):
            raise ValidationError({'first_name': 'Preencha todos os campos.'})


class RegisterForm(RegisterFormBase, PasswordForm):

    def clean(self, *args, **kwargs):
        first_name = self.cleaned_data.get('first_name')
        last_name = self.cleaned_data.get('last_name')
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')

        if core_utils.is_empty((first_name, last_name, email, password, password2)):
            raise ValidationError({'first_name': 'Preencha todos os campos.'})

        if password != password2:
            raise ValidationError({'password': 'Senhas não correspondem'})

        if User.objects.filter(email=email).exists():
            raise ValidationError({'email': 'E-mail já cadastrado'})


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['address', 'number', 'complement', 'district', 'zip_code', 'city', 'state']
        widgets = {
            'address': forms.TextInput(attrs={
                'class': CSS_CLASSES.get('form-control'),
                'placeholder': 'Rua'
            }),
            'number': forms.TextInput(attrs={
                'class': CSS_CLASSES.get('form-control'),
                'placeholder': 'Número'
            }),
            'complement': forms.TextInput(attrs={
                'class': CSS_CLASSES.get('form-control'),
                'placeholder': 'Complemento'
            }),
            'district': forms.TextInput(attrs={
                'class': CSS_CLASSES.get('form-control'),
                'placeholder': 'Bairro'
            }),
            'zip_code': forms.TextInput(attrs={
                'class': CSS_CLASSES.get('form-control'),
                'placeholder': 'CEP'
            }),
            'city': forms.TextInput(attrs={
                'class': CSS_CLASSES.get('form-control'),
                'placeholder': 'Cidade'
            }),
            'state': forms.Select(attrs={
                'class': CSS_CLASSES.get('form-control'),
                'placeholder': 'Estado'
            })
        }

    def clean(self, *args, **kwargs):
        address = self.cleaned_data.get('address')
        number = self.cleaned_data.get('number')
        complement = self.cleaned_data.get('complement')
        district = self.cleaned_data.get('district')
        zip_code = self.cleaned_data.get('zip_code')
        city = self.cleaned_data.get('city')
        state = self.cleaned_data.get('state')

        if core_utils.is_empty((address, number, complement, district, zip_code, city, state)):
            raise ValidationError({'address': 'Preencha todos os campos.'})


class ChangePasswordForm(PasswordForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': CSS_CLASSES.get('form-control'),
        'placeholder': 'Nova Senha',
    }))

    old_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': CSS_CLASSES.get('form-control'),
        'placeholder': 'Senha atual',
    }))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if core_utils.is_empty((old_password,)):
            raise ValidationError('Preencha todos os campos.')

        mate_pass_db = self.user.check_password(old_password)
        if not mate_pass_db:
            raise ValidationError('Senha atual inválida. Informe a senha correta.')
