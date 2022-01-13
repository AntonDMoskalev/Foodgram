from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Follow
from users.serializers import CustomUserSerializers


class FollowRecipeSerializers(serializers.ModelSerializer):
    """
    Serializer for displaying a list of recipes in FollowUserSerializers.
    """
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowUserSerializers(serializers.ModelSerializer):
    """
    Subscriber serializer, with additional fields:
    is_subscribed - subscription to the author (True)
    recipes - recipes of the author
    recipes_count - number of recipes of the author
    Additionally, pagination for recipes is implemented:
    recipes_limit.
    """
    id = serializers.ReadOnlyField(source='author.id')
    email = serializers.ReadOnlyField(source='author.email')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, author=obj.author).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.GET.get('recipes_limit')
        queryset = Recipe.objects.filter(author=obj.author)
        if recipes_limit:
            queryset = queryset[:int(recipes_limit)]
        return FollowRecipeSerializers(queryset, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()

    class Meta:
        model = Follow
        fields = '__all__'


class TagSerializers(serializers.ModelSerializer):
    """
    Tag serializer for recipes.
    """
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializers(serializers.ModelSerializer):
    """
    Ingredients Serializer.
    """
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientRecipeSerializers(serializers.ModelSerializer):
    """
    Serializer of ingredients for recipes
    """
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientRecipe
        fields = '__all__'


class RecipeSerializers(serializers.ModelSerializer):
    """
    Recipe serializer with additional fields:
    1. Favorites field False/True
    2. The shopping list field is False/True
    Validation of adding ingredients,
    Method of adding ingredients to a recipe,
    Redefined methods:
    1. Creating a recipe
    2. Changing the recipe.
    """
    tags = TagSerializers(read_only=True, many=True)
    author = CustomUserSerializers(read_only=True)
    image = Base64ImageField()
    ingredients = IngredientRecipeSerializers(read_only=True, many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Favorite.objects.filter(user=user, recipe=obj.id).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(user=user, recipe=obj.id).exists()

    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        ingredients_list = {}
        if ingredients:
            for ingredient in ingredients:
                if ingredient.get('id') in ingredients_list:
                    raise ValidationError(
                        _('Ингредиент может быть добавлен только один раз'))
                if int(ingredient.get('amount')) <= 0:
                    raise ValidationError(
                        _('Добавьте количество для ингредиента больше 0')
                    )
                ingredients_list[ingredient.get('id')] = (
                    ingredients_list.get('amount')
                )
            return data
        else:
            raise ValidationError(_('Добавьте ингредиент в рецепт'))

    def ingredient_recipe_create(self, ingredients_set, recipe):
        for ingredient_get in ingredients_set:
            ingredient = Ingredient.objects.get(id=ingredient_get.get('id'))
            IngredientRecipe.objects.create(ingredient=ingredient,
                                            recipe=recipe,
                                            amount=ingredient_get.get('amount')
                                            )

    def create(self, validated_data):
        image = validated_data.pop('image')
        recipe = Recipe.objects.create(image=image,
                                       author=self.context['request'].user,
                                       **validated_data)
        tags = self.initial_data.get('tags')
        recipe.tags.set(tags)
        ingredients_set = self.initial_data.get('ingredients')
        self.ingredient_recipe_create(ingredients_set, recipe)
        return recipe

    def update(self, instance, validated_data):
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time',
                                                   instance.cooking_time)
        instance.tags.clear()
        tags = self.initial_data.get('tags')
        instance.tags.set(tags)
        instance.save()
        IngredientRecipe.objects.filter(recipe=instance).delete()
        ingredients_set = self.initial_data.get('ingredients')
        self.ingredient_recipe_create(ingredients_set, instance)
        return instance

    class Meta:
        model = Recipe
        fields = '__all__'


class FavoriteSerializers(serializers.ModelSerializer):
    """
    Serializer of selected recipes.
    """
    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    image = serializers.ImageField(source='recipe.image')
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')

    class Meta:
        model = Favorite
        fields = '__all__'


class ShoppingCardSerializers(serializers.ModelSerializer):
    """
    Shopping list serializer.
    """
    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    image = serializers.ImageField(source='recipe.image')
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')

    class Meta:
        model = ShoppingCart
        fields = '__all__'
