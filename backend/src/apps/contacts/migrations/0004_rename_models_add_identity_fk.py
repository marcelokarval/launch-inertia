# Generated manually for P0.1 + P0.2

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("contact_identity", "0002_attribution"),
        ("contacts", "0003_contact_version_contactemail_version_and_more"),
    ]

    operations = [
        # P0.1: Add identity FK to Contact
        migrations.AddField(
            model_name="contact",
            name="identity",
            field=models.OneToOneField(
                blank=True,
                help_text="The unified identity this CRM contact resolves to",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="crm_contact",
                to="contact_identity.identity",
                verbose_name="Resolved Identity",
            ),
        ),
        # P0.2: Rename CRM ContactEmail -> AdditionalEmail
        migrations.RenameModel(
            old_name="ContactEmail",
            new_name="AdditionalEmail",
        ),
        # P0.2: Rename CRM ContactPhone -> AdditionalPhone
        migrations.RenameModel(
            old_name="ContactPhone",
            new_name="AdditionalPhone",
        ),
        # Update related_name for AdditionalEmail
        migrations.AlterField(
            model_name="additionalemail",
            name="contact",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="additional_emails",
                to="contacts.contact",
            ),
        ),
        # Update related_name for AdditionalPhone
        migrations.AlterField(
            model_name="additionalphone",
            name="contact",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="additional_phones",
                to="contacts.contact",
            ),
        ),
        # Update verbose names and db_table for AdditionalEmail
        migrations.AlterModelOptions(
            name="additionalemail",
            options={
                "verbose_name": "Additional Email",
                "verbose_name_plural": "Additional Emails",
            },
        ),
        migrations.AlterModelTable(
            name="additionalemail",
            table="contacts_contactemail",
        ),
        # Update verbose names and db_table for AdditionalPhone
        migrations.AlterModelOptions(
            name="additionalphone",
            options={
                "verbose_name": "Additional Phone",
                "verbose_name_plural": "Additional Phones",
            },
        ),
        migrations.AlterModelTable(
            name="additionalphone",
            table="contacts_contactphone",
        ),
    ]
