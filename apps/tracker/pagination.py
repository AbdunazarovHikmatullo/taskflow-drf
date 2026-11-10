from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """Пагинация с возможностью задать размер страницы через ?page_size=."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
