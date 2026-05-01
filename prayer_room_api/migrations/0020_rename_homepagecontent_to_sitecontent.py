from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("prayer_room_api", "0019_prayerresource_section_and_more"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="HomePageContent",
            new_name="SiteContent",
        ),
        migrations.AlterModelOptions(
            name="sitecontent",
            options={"ordering": ["key"]},
        ),
        migrations.AlterField(
            model_name="sitecontent",
            name="key",
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name="sitecontent",
            name="value",
            field=models.TextField(blank=True),
        ),
    ]
