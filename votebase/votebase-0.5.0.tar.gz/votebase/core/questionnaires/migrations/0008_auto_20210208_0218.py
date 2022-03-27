# Generated by Django 3.1.6 on 2021-02-08 01:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaires', '0007_auto_20210208_0202'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='option',
            name='unique_prefix',
        ),
        migrations.RemoveConstraint(
            model_name='question',
            name='unique_tag',
        ),
        migrations.RemoveField(
            model_name='option',
            name='prefix',
        ),
        migrations.AddField(
            model_name='option',
            name='tag',
            field=models.CharField(blank=True, db_index=True, max_length=10, verbose_name='tag'),
        ),
        migrations.AddConstraint(
            model_name='option',
            constraint=models.UniqueConstraint(condition=models.Q(_negated=True, tag__in=(None, '', [], (), {})), fields=('question', 'tag'), name='unique_option_tag'),
        ),
        migrations.AddConstraint(
            model_name='question',
            constraint=models.UniqueConstraint(condition=models.Q(_negated=True, tag__in=(None, '', [], (), {})), fields=('survey', 'tag'), name='unique_question_tag'),
        ),
    ]
