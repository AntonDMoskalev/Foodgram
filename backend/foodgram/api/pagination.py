from rest_framework.pagination import PageNumberPagination


class LimitPagePagination(PageNumberPagination):
    """
    Custom paginator:
    page - Page number
    limit - The number of objects on the page.
    """
    page_size = 6
    page_size_query_param = 'limit'
