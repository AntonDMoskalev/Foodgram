from django_filters import filters
from django_filters.rest_framework import FilterSet, filters

from recipes.models import Recipe
from users.models import User


class RecipeFilter(FilterSet):
    """
    Filtering recipes:
    1. By multiple tags
    2. By the author of the publication
    3. Only selected recipes
    4. Only recipes in the shopping list.
    """
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    author = filters.ModelChoiceFilter(queryset=User.objects.all())
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    def filter_is_favorited(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            return queryset.filter(shopping_carts__user=self.request.user)
        return queryset

    class Meta:
        model = Recipe
        fields = ['tags', 'author']
