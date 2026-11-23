"""Pagination of the offer list."""
from rest_framework.pagination import PageNumberPagination


class OfferPagination(PageNumberPagination):
    """Six offers per page (same as PAGE_SIZE in the frontend).

    The client may change it with ?page_size=.
    """

    page_size = 6
    page_size_query_param = "page_size"
    max_page_size = 100
