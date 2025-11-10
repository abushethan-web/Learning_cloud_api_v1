# Generated manually for GradeLevel model and grade_level_model foreign key

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_alter_user_email'),
    ]

    operations = [
        migrations.CreateModel(
            name='GradeLevel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('level', models.IntegerField(help_text='Grade level number (0-4)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(4)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'grade_levels',
                'ordering': ['level'],
            },
        ),
        migrations.AddIndex(
            model_name='gradelevel',
            index=models.Index(fields=['level'], name='grade_level_level_idx'),
        ),
        migrations.AddField(
            model_name='user',
            name='grade_level_model',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='students', to='accounts.gradelevel'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['grade_level_model'], name='users_grade_l_model_idx'),
        ),
    ]

