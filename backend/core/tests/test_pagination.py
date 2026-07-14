import pytest
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request
from core.utils.pagination import CustomPagination


class TestCustomPagination:
    """Tests for CustomPagination class."""

    def setup_method(self):
        self.paginator = CustomPagination()
        factory = APIRequestFactory()
        self.request = Request(factory.get("/"))

    def test_default_page_size(self):
        assert self.paginator.page_size == 10

    def test_max_page_size(self):
        assert self.paginator.max_page_size == 100

    def test_page_size_query_param(self):
        assert self.paginator.page_size_query_param == "page_size"

    def test_custom_page_size_param(self):
        factory = APIRequestFactory()
        request = Request(factory.get("/?page_size=5"))
        self.paginator.request = request
        page_size = self.paginator.get_page_size(request)
        assert page_size == 5

    def test_page_size_clamped_to_max(self):
        factory = APIRequestFactory()
        request = Request(factory.get("/?page_size=999"))
        self.paginator.request = request
        page_size = self.paginator.get_page_size(request)
        assert page_size == 100

    def test_paginate_queryset_returns_page(self):
        class FakeQuerySet:
            def count(self):
                return 50

            def __getitem__(self, slice_obj):
                return [{"id": i} for i in range(slice_obj.start or 0, slice_obj.stop or 0)]

        self.paginator.request = self.request
        page = self.paginator.paginate_queryset(FakeQuerySet(), self.request)
        assert page is not None
        assert len(page) == 10  # default page_size

    def test_get_paginated_response_structure(self):
        class FakeQuerySet:
            def count(self):
                return 25

            def __getitem__(self, slice_obj):
                return [{"id": i} for i in range(slice_obj.start or 0, slice_obj.stop or 0)]

        self.paginator.request = self.request
        self.paginator.paginate_queryset(FakeQuerySet(), self.request)
        response = self.paginator.get_paginated_response([{"id": 1}])
        data = response.data
        assert "count" in data
        assert "next" in data
        assert "previous" in data
        assert "results" in data
        assert data["results"] == [{"id": 1}]