from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ScheduledReportViewSet

router = DefaultRouter()
router.register(r"reports", ScheduledReportViewSet, basename="report")

urlpatterns = [
    path("", include(router.urls)),
]