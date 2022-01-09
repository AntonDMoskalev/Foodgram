from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext as _


class User(AbstractUser):
    """
    Redefining the User model.
    New extensions of the standard model have been added:
    1. Roles for users (user, admin, block(ban))
    2. User role verification
    """
    USER = 'user'
    ADMIN = 'admin'
    BLOCK = 'block'

    CHOICES = [(USER, _('user')),
               (ADMIN, _('admin')),
               (BLOCK, _('block'))]

    email = models.EmailField(_('email'), max_length=254, unique=True)
    username = models.CharField(_('username'), unique=True, max_length=150)
    first_name = models.CharField(_('first_name'), max_length=150)
    last_name = models.CharField(_('last_name'), max_length=150)
    password = models.CharField(_('password'), max_length=150)
    role = models.CharField(_('role'),
                            choices=CHOICES,
                            default=USER,
                            max_length=20)

    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    @property
    def is_admin(self):
        return self.is_superuser or self.is_staff or self.role == User.ADMIN

    @property
    def is_block(self):
        return self.role == User.BLOCK

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        ordering = ['-first_name']
        verbose_name = _('User')
        verbose_name_plural = _('Users')


class Follow(models.Model):
    """Subscription model for recipe authors"""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='follower',
        verbose_name=_('user'))
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='following',
        verbose_name=_('author'))

    class Meta():
        models.UniqueConstraint(
            fields=['user', 'author'], name='unique_recording')
