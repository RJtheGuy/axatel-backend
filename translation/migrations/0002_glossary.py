from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("translation", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="protectedterm",
            options={"ordering": ["term"], "verbose_name": "Glossario di traduzione",
                     "verbose_name_plural": "Glossario di traduzione"},
        ),
        migrations.AlterField(
            model_name="protectedterm",
            name="term",
            field=models.CharField(help_text="Es. 'Angel River' (nome da non tradurre) o 'concessionarie stradali'.",
                                   max_length=80, unique=True, verbose_name="Termine italiano"),
        ),
        migrations.AddField(
            model_name="protectedterm",
            name="translation_en",
            field=models.CharField(blank=True, help_text="Vuoto (anche il francese) = il termine resta com'è.",
                                   max_length=120, verbose_name="Traduzione inglese"),
        ),
        migrations.AddField(
            model_name="protectedterm",
            name="translation_fr",
            field=models.CharField(blank=True, max_length=120, verbose_name="Traduzione francese"),
        ),
    ]
