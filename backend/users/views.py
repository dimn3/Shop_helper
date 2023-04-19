from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.shortcuts import get_object_or_404
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.models import Follow
from api.serializers import FollowSerializer

from .serializers import (ChangePasswordSerializer, CustomUserSerializer,
                          UserLoginSerializer)

User = get_user_model()


class FollowViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = FollowSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Follow.objects.filter(user=self.request.user)


class FollowActionViewSet(
    viewsets.GenericViewSet,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin
):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = FollowSerializer

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            following=get_object_or_404(
                User, pk=self.kwargs.get('id')
            )
        )

    def delete(self, request, *args, **kwargs):
        follow = get_object_or_404(
            Follow,
            user=self.request.user,
            following=get_object_or_404(
                User, pk=self.kwargs.get('id')
            )
        )
        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['id'] = int(self.kwargs.get('id'))
        return context


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = (AllowAny,)

    lookup_field = 'id'

    def set_password(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        current_user = self.request.user

        if not check_password(
                serializer.validated_data['current_password'],
                current_user.password
        ):
            message = "Current Password is incorrect"
            return Response(message, status=status.HTTP_401_UNAUTHORIZED)

        current_user.set_password(serializer.validated_data['new_password'])
        current_user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('GET',),
        permission_classes=(permissions.IsAuthenticated,)
    )
    def me(self, request):
        """Возможность получения Пользователя данных о себе
        GET запрос"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        user = get_object_or_404(User, pk=kwargs.get('id'))
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserLoginViewSet(
    viewsets.GenericViewSet, mixins.CreateModelMixin,
):
    permission_classes = (AllowAny,)

    serializer_class = UserLoginSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, )

        serializer.is_valid(raise_exception=True)

        password = serializer.validated_data.get('password')
        email = serializer.validated_data.get('email')

        if not User.objects.filter(email=email).exists():
            message = "This email has already been taken"
            return Response(
                data=message,
                status=status.HTTP_400_BAD_REQUEST
            )

        user = get_object_or_404(User, email=email)
        if not check_password(password, user.password):
            message = "password is incorrect"
            return Response(
                data=message,
                status=status.HTTP_400_BAD_REQUEST
            )

        token, _ = Token.objects.get_or_create(user=user)

        response = {
            "auth_token": str(token)
        }

        return Response(
            data=response,
            status=status.HTTP_201_CREATED
        )


class UserLogoutViewSet(
    viewsets.GenericViewSet, mixins.CreateModelMixin,
):
    permission_classes = (IsAuthenticated,)

    serializer_class = UserLoginSerializer

    def create(self, request, *args, **kwargs):
        Token.objects.filter(user_id=self.request.user.id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
