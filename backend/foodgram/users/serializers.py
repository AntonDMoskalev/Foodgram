from django.contrib.auth.hashers import make_password
from django.utils.translation import gettext as _
from rest_framework import serializers

from users.models import Follow, User


class CustomCreateUserSerializers(serializers.ModelSerializer):
    """
    User creation serializer, redefinition of the password field,
    for encoding the password when saving.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': _('password'), 'placeholder': _('Password')}
    )

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'password')

    def create(self, validated_data):
        validated_data['password'] = make_password(
            validated_data.get('password'))
        return super(CustomCreateUserSerializers, self).create(validated_data)


class CustomUserSerializers(serializers.ModelSerializer):
    """
    The user's serializer with an additional is_subscribed field,
    returns False or True depending on the subscription to the author.
    """

    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, author=obj.id).exists()

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'is_subscribed')
