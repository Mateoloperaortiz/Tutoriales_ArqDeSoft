from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("tienda_app", "0002_orden_libro"),
    ]

    operations = [
        migrations.CreateModel(
            name="OrdenItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cantidad", models.PositiveIntegerField()),
                ("precio_unitario", models.DecimalField(decimal_places=2, max_digits=10)),
                ("libro", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="orden_items", to="tienda_app.libro")),
                ("orden", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="tienda_app.orden")),
            ],
        ),
        migrations.AddConstraint(
            model_name="ordenitem",
            constraint=models.UniqueConstraint(fields=("orden", "libro"), name="unique_libro_por_orden"),
        ),
    ]
