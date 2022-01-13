import io

from django.db.models import Sum
from django.http import FileResponse
from django.utils.translation import gettext as _
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from rest_framework import filters, permissions, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Follow, User

from .filters import RecipeFilter
from .mixins import CustomRecipeModelViewSet, ListRetrieveCustomViewSet
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
                            _('Вы не можете подписаться на себя.')},
                            status=status.HTTP_400_BAD_REQUEST)
        if Follow.objects.filter(user=user, author=author).exists():
            return Response({'errors':
                            _('Вы уже подписались на автора.')},
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


class RecipeViewSet(CustomRecipeModelViewSet):
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

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            return self.add_obj(model=Favorite,
                                pk=pk,
                                serializers=FavoriteSerializers,
                                user=request.user)
        elif request.method == 'DELETE':
            return self.del_obj(model=Favorite, pk=pk, user=request.user)
        return None

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[permissions.IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        if request.method == 'POST':
            return self.add_obj(model=ShoppingCart,
                                pk=pk,
                                serializers=ShoppingCardSerializers,
                                user=request.user)
        if request.method == 'DELETE':
            return self.del_obj(model=ShoppingCart, pk=pk, user=request.user)
        return Response(_('Разрешены только POST и DELETE запросы'),
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=False, permission_classes=[permissions.IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user
        ingredients = IngredientRecipe.objects.filter(
            recipe__shopping_carts__user=user).values(
                'ingredient__name',
                'ingredient__measurement_unit').order_by(
                    'ingredient__name').annotate(amount=Sum('amount'))
        buffer = io.BytesIO()
        canvas = Canvas(buffer)
        pdfmetrics.registerFont(
            TTFont('Country', 'Country.ttf', 'UTF-8'))
        canvas.setFont('Country', size=36)
        canvas.drawString(70, 800, _('Продуктовый помощник'))
        canvas.drawString(70, 760, _('список покупок:'))
        canvas.setFont('Country', size=18)
        canvas.drawString(70, 700, _('Ингредиенты:'))
        canvas.setFont('Country', size=16)
        canvas.drawString(70, 670, _('Название:'))
        canvas.drawString(220, 670, _('Количество:'))
        canvas.drawString(350, 670, _('Единица измерения:'))
        height = 630
        for ingredient in ingredients:
            canvas.drawString(70, height, f"{ingredient['ingredient__name']}")
            canvas.drawString(250, height,
                              f"{ingredient['amount']}")
            canvas.drawString(380, height,
                              f"{ingredient['ingredient__measurement_unit']}")
            height -= 25
        canvas.save()
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True,
                            filename='Shoppinglist.pdf')
