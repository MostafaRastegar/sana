from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('charts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chart',
            name='chart_type',
            field=models.CharField(choices=[('bar', 'Bar'), ('line', 'Line'), ('pie', 'Pie'), ('scatter', 'Scatter'), ('area', 'Area'), ('heatmap', 'Heatmap'), ('kpi', 'KPI / Scorecard'), ('gauge', 'Gauge'), ('funnel', 'Funnel'), ('treemap', 'Treemap'), ('radar', 'Radar')], max_length=50, verbose_name='Chart Type'),
        ),
    ]
