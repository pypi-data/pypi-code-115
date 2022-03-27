# Generated by Django 3.2.5 on 2021-08-25 09:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('NearBeach', '0010_alter_change_task_block_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='kanban_card',
            name='is_archived',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='change_task_block',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
