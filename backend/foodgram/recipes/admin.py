from django.contrib import admin

from .models import Favorite, Ingredient, IngredientRecipe, Recipe, Tag


class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "color", "slug")
    search_fields = ('name', 'slug',)


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',) 


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('author', 'name', 'text', 'cooking_time', 'favorites')
    list_filter = ('author', 'name', 'tags')

    def favorites(self, obj):
        return obj.favorites.count()


class RecipeIngredient(admin.ModelAdmin):
    list_display = ('ingredient', 'recipe', 'amount')


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'user')
    list_filter = ('user',)


admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(IngredientRecipe, RecipeIngredient)
admin.site.register(Favorite, FavoriteAdmin)
