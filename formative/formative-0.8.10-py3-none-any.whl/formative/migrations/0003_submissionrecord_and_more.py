# Generated by Django 4.0.2 on 2022-02-11 23:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('formative', '0002_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SubmissionRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('form', models.SlugField(allow_unicode=True, max_length=64)),
                ('submission', models.UUIDField(editable=False)),
                ('type', models.CharField(max_length=32)),
                ('recorded', models.DateTimeField(auto_now=True, verbose_name='recorded at')),
                ('text', models.TextField(blank=True)),
                ('number', models.PositiveBigIntegerField(blank=True, null=True)),
                ('deleted', models.BooleanField(default=False)),
                ('program', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='formative.program')),
            ],
        ),
        migrations.AddConstraint(
            model_name='submissionrecord',
            constraint=models.UniqueConstraint(fields=('submission', 'type'), name='unique_submission_record_type'),
        ),
    ]
