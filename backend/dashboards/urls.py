from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"dashboards", views.DashboardViewSet, basename="dashboard")
router.register(r"users/search", views.UserSearchView, basename="user-search")

urlpatterns = [
    path("", include(router.urls)),
]
