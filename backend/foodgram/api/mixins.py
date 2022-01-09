from rest_framework import mixins, viewsets


class ListRetrieveCustomViewSet(mixins.ListModelMixin,
                                mixins.RetrieveModelMixin,
                                viewsets.GenericViewSet):
    """Only GET requests for Tags and Ingredients."""
    pass
