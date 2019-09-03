# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-08-27 00:11
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion

from config.constants import ResearcherRole
from database.study_models import Study
from database.user_models import Researcher, StudyRelation


# Researcher.studies used to A) exist and B) was many-to-many field.  We cannot access it after
# removing it from the model, but we can grab the raw sql emitted by the following operation:
#   some_researcher.studies.all().values_list("id", flat=True)
# (Note that because of the way django managers work we have to run this query on Study, not Researcher.)
SQL_GET_STUDY_ID = """
SELECT "database_study"."id"
FROM "database_study"
INNER JOIN "database_researcher_studies" ON ("database_study"."id" = "database_researcher_studies"."study_id")
WHERE "database_researcher_studies"."researcher_id" = {researcher_id}
""".strip()


def researcher_paradigm_shift(apps, schema_editor):
    # create a StudyRelation object for every researcher on their studies.
    for researcher in Researcher.objects.all():
        lower_username = researcher.username.lower()
        if "batch user" in lower_username or "aws lambda" in lower_username:
            continue

        # admin field -> site_admin, we convert all researchers that are not the default admin
        # account to a study admin on their studies.  Any exceptions to this will require
        # manual fixing.
        admin_status = ResearcherRole.study_admin if researcher.site_admin else ResearcherRole.researcher

        # We only want to elevate a site admin for the default admin, site admins have access to
        # everything but don't have any study relationships.
        if researcher.username != "default_admin":
            researcher.site_admin = False
            researcher.save()
            # for study in researcher.studies.all():
            for study in Study.objects.raw(SQL_GET_STUDY_ID.format(researcher_id=researcher.id)):
                StudyRelation.objects.create(
                    study=study,
                    researcher=researcher,
                    relationship=admin_status,
                )

class Migration(migrations.Migration):

    dependencies = [
        ('database', '0021_auto_20190716_0057'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudyRelation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deleted', models.BooleanField(default=False)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('relationship', models.CharField(max_length=32, db_index=True)),
                ('researcher', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='study_relations', to='database.Researcher', db_index=True)),
                ('study', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='study_relations', to='database.Study', db_index=True)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='studyrelation',
            unique_together=set([('study', 'researcher')]),
        ),
        migrations.RenameField(
            model_name='researcher',
            old_name='admin',
            new_name='site_admin',
        ),
        migrations.RunPython(researcher_paradigm_shift),
        migrations.RemoveField(
            model_name='researcher',
            name='studies',
        ),
    ]


