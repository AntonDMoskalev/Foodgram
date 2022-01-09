import io

from django.http import FileResponse
from django.utils.translation import gettext as _
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Follow, User

from .filters import RecipeFilter
from .mixins import ListRetrieveCustomViewSet
from .pagination import LimitPagePagination
from .permissions import AuthorOrReadOnly
from .serializers import (FavoriteSerializers, FollowUserSerializers,
                          IngredientSerializers, RecipeSerializers,
                          ShoppingCardSerializers, TagSerializers)


class CustomUserViewSet(UserViewSet):
    """
    Redefining UserViewSetb added new endpoints for subscriptions:
    1. Subscribe
    2. Delete the subscription
    3. List of subscriptions
    Pagination:
    Page - page (by default 6 objects per page)
    Limit - limit on the output of objects per page
    Recipes_limit - the number of recipes the author has
    """
    pagination_class = LimitPagePagination

    @action(detail=False, permission_classes=[permissions.IsAuthenticated])
    def subscriptions(self, request):
        queryset = Follow.objects.filter(user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = FollowUserSerializers(page, many=True,
                                           context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True,
            methods=['post'],
            permission_classes=[permissions.IsAuthenticated])
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)
        if user == author:
            return Response({'errors':
                            _('You can not subscribe to yourself.')},
                            status=status.HTTP_400_BAD_REQUEST)
        if Follow.objects.filter(user=user, author=author).exists():
            return Response({'errors':
                            _('You have already subscribed to the author.')},
                            status=status.HTTP_400_BAD_REQUEST)
        Follow.objects.create(user=user, author=author)
        queryset = Follow.objects.get(user=request.user, author=author)
        serializer = FollowUserSerializers(queryset,
                                           context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def subscribe_del(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)
        if not Follow.objects.filter(user=user, author=author).exists():
            return Response({'errors': 'Подписки не существует.'},
                            status=status.HTTP_400_BAD_REQUEST)
        Follow.objects.get(user=user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(ListRetrieveCustomViewSet):
    """
    ViewSet for TagSerializers only GET requests.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializers
    permission_classes = (permissions.AllowAny,)


class IngredientViewSet(ListRetrieveCustomViewSet):
    """
    ViewSet for IngredientSerializers only GET requests.
    Filter by ingredient name.
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializers
    permission_classes = (permissions.AllowAny,)
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class RecipeViewSet(viewsets.ModelViewSet):
    """
    Receptviews with additional methods:
    1. Add/Remove from favorites
    2. Add/remove from the shopping list
    3. Get a shopping list in PDF format
    """
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializers
    pagination_class = LimitPagePagination
    filter_backends = (DjangoFilterBackend, )
    filter_class = RecipeFilter
    permission_classes = (AuthorOrReadOnly,)

    @action(detail=True, methods=['post'],
            permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            return Response({'errors':
                             _('Already added to the favorites list')},
                            status=status.HTTP_400_BAD_REQUEST)
        Favorite.objects.create(user=user, recipe=recipe)
        queryset = Favorite.objects.get(user=user, recipe=recipe)
        serializer = FavoriteSerializers(queryset,
                                         context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def favorite_del(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if not Favorite.objects.filter(user=user, recipe=recipe).exists():
            return Response({'errors': _('Not in favorites')},
                            status=status.HTTP_400_BAD_REQUEST)
        Favorite.objects.get(user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'],
            permission_classes=[permissions.IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            return Response({'errors':
                            _('Already added to the shopping list')},
                            status=status.HTTP_400_BAD_REQUEST)
        ShoppingCart.objects.create(user=user, recipe=recipe)
        queryset = ShoppingCart.objects.get(user=user, recipe=recipe)
        serializer = ShoppingCardSerializers(queryset,
                                             context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def shopping_cart_del(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if not ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            return Response({'errors':
                            _('The recipe is not in the shopping list')},
                            status=status.HTTP_400_BAD_REQUEST)
        ShoppingCart.objects.get(user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, permission_classes=[permissions.IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user
        ingredient_shop = {}
        ingredients = IngredientRecipe.objects.filter(
            recipe__shopping_carts__user=user
        )
        for ingredient in ingredients:
            if ingredient.ingredient.name not in ingredient_shop:
                ingredient_shop[ingredient.ingredient.name] = [
                    ingredient.ingredient.measurement_unit, ingredient.amount
                ]
            else:
                ingredient_shop[
                    ingredient.ingredient.name
                ][1] += ingredient.amount

        buffer = io.BytesIO()
        canvas = Canvas(buffer)
        pdfmetrics.registerFont(
            TTFont('Country', 'Country.ttf', 'UTF-8'))
        canvas.setFont('Country', size=36)
        canvas.drawString(70, 800, 'Продуктовый помощник')
        canvas.drawString(70, 760, 'список покупок:')
        canvas.setFont('Country', size=18)
        canvas.drawString(70, 700, 'Ингредиенты:')
        canvas.setFont('Country', size=16)
        canvas.drawString(70, 670, 'Название:')
        canvas.drawString(220, 670, 'Количество:')
        canvas.drawString(350, 670, 'Единица измерения:')
        height = 630
        for ingredients in ingredient_shop:
            canvas.drawString(70, height, f'{ingredients}')
            canvas.drawString(250, height,
                              f'{ingredient_shop[ingredients][1]}')
            canvas.drawString(380, height,
                              f'{ingredient_shop[ingredients][0]}')
            height -= 25
        canvas.save()
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True,
                            filename='Shoppinglist.pdf')
