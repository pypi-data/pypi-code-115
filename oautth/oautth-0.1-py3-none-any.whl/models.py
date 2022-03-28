from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from oauth.python.utils import custom_messages
import re


class Address(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=False)
    address = models.CharField(max_length=100)
    number = models.CharField(max_length=5)
    complement = models.CharField(max_length=30)
    district = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=8)
    city = models.CharField(max_length=50)
    state = models.CharField(
        default='DF',
        max_length=2,
        choices=(
            ('AC', 'Acre'),
            ('AL', 'Alagoas'),
            ('AP', 'Amapá'),
            ('AM', 'Amazonas'),
            ('BA', 'Bahia'),
            ('CE', 'Ceará'),
            ('DF', 'Distrito Federal'),
            ('ES', 'Espírito Santo'),
            ('GO', 'Goiás'),
            ('MA', 'Maranhão'),
            ('MT', 'Mato Grosso'),
            ('MS', 'Mato Grosso do Sul'),
            ('MG', 'Minas Gerais'),
            ('PA', 'Pará'),
            ('PB', 'Paraíba'),
            ('PR', 'Paraná'),
            ('PE', 'Pernambuco'),
            ('PI', 'Piauí'),
            ('RJ', 'Rio de Janeiro'),
            ('RN', 'Rio Grande do Norte'),
            ('RS', 'Rio Grande do Sul'),
            ('RO', 'Rondônia'),
            ('RR', 'Roraima'),
            ('SC', 'Santa Catarina'),
            ('SP', 'São Paulo'),
            ('SE', 'Sergipe'),
            ('TO', 'Tocantins'),
        )
    )

    def __str__(self):
        return f'{self.user.username}'

    def clean(self):
        error_messages = {}

        if re.search(r'[^0-9]', self.zip_code) or len(self.zip_code) < 8:
            error_messages['zip_code'] = custom_messages.invalid_zip_code

        if error_messages:
            raise ValidationError(error_messages)
