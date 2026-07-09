from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"datasets", views.DatasetViewSet, basename="dataset")

urlpatterns = [
    path("tables/", views.list_tables, name="list-tables"),
    path("tables/<str:table_name>/columns/", views.detect_columns, name="detect-columns"),
    path("", include(router.urls)),
]