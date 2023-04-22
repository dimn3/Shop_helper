from django.contrib.auth.hashers import make_password
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from recipes.models import Follow
from users.models import User


class CustomUserSerializer(UserSerializer):
    username = serializers.SlugField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())],
    )
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())],
    )

    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        request_user = self.context.get('request').user
        if request_user.is_anonymous:
            return False
        return Follow.objects.filter(user=request_user, following=obj).exists()

    def validate(self, data):
        if 'password' in data:
            password = make_password(data['password'])
            data['password'] = password
            return data
        else:
            return data

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "is_subscribed",
            "password",
            "id",
        )
        extra_kwargs = {"password": {'write_only': True}}


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
        )


class UserLoginSerializer(serializers.Serializer):
    password = serializers.CharField(required=True, max_length=128)
    email = serializers.CharField(required=True, max_length=254)


class ChangePasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True, max_length=128)
    current_password = serializers.CharField(required=True, max_length=128)
