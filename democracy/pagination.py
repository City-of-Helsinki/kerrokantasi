from rest_framework.pagination import LimitOffsetPagination


class DefaultLimitPagination(LimitOffsetPagination):
    default_limit = 50
