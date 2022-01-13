from django.contrib import admin

from .models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                     ShoppingCart, Tag)


class TagAdmin(admin.ModelAdmin):
    """Admin panel for the Tag model"""
    list_display = ("name", "color", "slug")
    search_fields = ('name', 'slug',)


class IngredientAdmin(admin.ModelAdmin):
    """Admin panel for the Ingredient model"""
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)


class IngredientInLine(admin.StackedInline):
    """Adds a selection of ingredients for a recipe"""
    model = IngredientRecipe
    extra = 3


class RecipeAdmin(admin.ModelAdmin):
    """Admin panel for the Recipe model"""
    list_display = ('author', 'name', 'text', 'cooking_time', 'favorites')
    list_filter = ('author', 'name', 'tags')
    inlines = [IngredientInLine]

    def favorites(self, obj):
        """Counts how many times a recipe has been added to favorites"""
        return obj.favorites.count()


class ShoppingCartAdmin(admin.ModelAdmin):
    """Admin panel for the ShoppingCart model"""
    list_display = ('user', 'recipe')
    search_fields = ('user', 'recipe',)


class FavoriteAdmin(admin.ModelAdmin):
    """Admin panel for the Favorite model"""
    list_display = ('recipe', 'user')
    list_filter = ('user',)


admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
admin.site.register(Favorite, FavoriteAdmin)
