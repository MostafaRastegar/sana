from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule
from rest_framework import serializers
# Celery Beat Serializers

class IntervalScheduleSerializer(serializers.ModelSerializer):
    """
    Serializer for IntervalSchedule model.
    """
    class Meta:
        model = IntervalSchedule
        fields = ['id', 'every', 'period']


class CrontabScheduleSerializer(serializers.ModelSerializer):
    """
    Serializer for CrontabSchedule model.
    """
    class Meta:
        model = CrontabSchedule
        fields = [
            'id', 'minute', 'hour', 'day_of_week',
            'day_of_month', 'month_of_year'
        ]


class PeriodicTaskSerializer(serializers.ModelSerializer):
    """
    Serializer for PeriodicTask model.
    """
    interval = IntervalScheduleSerializer(read_only=True)
    crontab = CrontabScheduleSerializer(read_only=True)

    class Meta:
        model = PeriodicTask
        fields = [
            'id', 'name', 'task', 'interval', 'crontab',
            'args', 'kwargs', 'enabled', 'last_run_at',
            'total_run_count', 'date_changed', 'description'
        ]
        read_only_fields = ['id', 'last_run_at', 'total_run_count', 'date_changed']
