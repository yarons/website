# Generated by Django 2.1.3 on 2019-07-17 10:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("weblate_web", "0005_donation_link_image")]

    operations = [
        migrations.AddField(
            model_name="donation",
            name="reward_new",
            field=models.IntegerField(
                choices=[
                    (0, "No reward"),
                    (1, "Name placement in the list of supporters"),
                    (2, "Link placement in the list of supporters"),
                    (3, "Logo & link placement on the Weblate website"),
                ],
                default=0,
            ),
            preserve_default=False,
        )
    ]
