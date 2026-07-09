from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"queries", views.SavedQueryViewSet, basename="saved-query")

urlpatterns = [
    path("execute/", views.execute_query, name="execute-query"),
    path("", include(router.urls)),
]
