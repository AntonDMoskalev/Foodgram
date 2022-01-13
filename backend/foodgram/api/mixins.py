from django.utils.translation import gettext as _
from rest_framework import mixins, status, viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from recipes.models import Recipe


class ListRetrieveCustomViewSet(mixins.ListModelMixin,
                                mixins.RetrieveModelMixin,
                                viewsets.GenericViewSet):
    """Only GET requests for Tags and Ingredients."""
    pass


class CustomRecipeModelViewSet(viewsets.ModelViewSet):
    """
    Custom View Set for Recipes added 2 methods:
    1. Adds an object to the model
    2. Removes an object from the model
    """
    def add_obj(self, serializers, model, user, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if model.objects.filter(user=user, recipe=recipe).exists():
            return Response({'errors':
                             _(f'{recipe} уже добавлен в {model}')},
                            status=status.HTTP_400_BAD_REQUEST)
        model.objects.create(user=user, recipe=recipe)
        queryset = model.objects.get(user=user, recipe=recipe)
        serializer = serializers(queryset)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def del_obj(self, model, pk, user):
        recipe = get_object_or_404(Recipe, id=pk)
        if not model.objects.filter(user=user, recipe=recipe).exists():
            return Response({'errors': _(f'{recipe} не добавлен в {model}')},
                            status=status.HTTP_400_BAD_REQUEST)
        model.objects.get(user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
