from colorfield.fields import ColorField
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext as _

from users.models import User


class Tag(models.Model):
    """
    Recipe tag model, color field with a choice of colors in hex format.
    """
    name = models.CharField(_('name'), max_length=50, unique=True)
    color = ColorField(unique=True)
    slug = models.SlugField(_('slug'), unique=True)

    def __str__(self):
        return self.name

    class Meta():
        ordering = ['-name']
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')


class Ingredient(models.Model):
    """
    Ingredient Model
    """
    name = models.CharField(_('name'), max_length=50, unique=True)
    measurement_unit = models.CharField(_('unit'), max_length=20)

    def __str__(self):
        return self.name

    class Meta():
        ordering = ['-name']
        verbose_name = _('Ingredient')
        verbose_name_plural = _('Ingredients')


class Recipe(models.Model):
    """Recipe Model"""
    tags = models.ManyToManyField(Tag, verbose_name=_('Tag'))
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='recipes',
                               verbose_name=_('author'))
    name = models.CharField(_('name'), max_length=200, unique=True)
    image = models.ImageField(_('image'), upload_to='recipe/')
    text = models.TextField(_('Description'))
    cooking_time = models.PositiveIntegerField(
        _('cooking_time'),
        validators=[MinValueValidator(limit_value=1,
                    message=_("Enter a number greater than 1"))])

    def __str__(self):
        return self.name

    class Meta():
        ordering = ['-id']
        verbose_name = _('Recipe')
        verbose_name_plural = _('Recipes')


class IngredientRecipe(models.Model):
    """
    A model for linking recipes, ingredients and the number of ingredients.
    """
    ingredient = models.ForeignKey(Ingredient,
                                   on_delete=models.CASCADE,
                                   related_name='recipes',
                                   verbose_name=_('ingredient'))
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               related_name='ingredients',
                               verbose_name=_('recipe'))
    amount = models.PositiveSmallIntegerField()

    class Meta():
        verbose_name = _('Ingredient recipe')
        verbose_name_plural = _('Ingredients recipe')


class Favorite(models.Model):
    """
    Model of selected recipes
    """
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='recipes_favorites',
                             verbose_name=_('user'))
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               related_name="favorites",
                               verbose_name=_('recipe'))

    class Meta():
        verbose_name = _('Favorite')
        verbose_name_plural = _('Favorites')


class ShoppingCart(models.Model):
    """
    Shopping List Model
    """
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='shopping_carts',
                             verbose_name=_('user'))
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               related_name='shopping_carts',
                               verbose_name=_('recipe'))

    class Meta():
        verbose_name = _('Shopping Cart')
        verbose_name_plural = _('Shopping Carts')
        models.UniqueConstraint(
            fields=['user', 'recipe'], name='unique_recording')
