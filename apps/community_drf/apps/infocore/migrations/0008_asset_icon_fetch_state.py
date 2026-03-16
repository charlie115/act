from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("infocore", "0007_per_symbol_notification"),
    ]

    operations = [
        migrations.AddField(
            model_name="asset",
            name="icon_fetch_failures",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="asset",
            name="icon_fetch_last_attempt_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="asset",
            name="icon_fetch_last_error",
            field=models.CharField(blank=True, max_length=500),
        ),
    ]
