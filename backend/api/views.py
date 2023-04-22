
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from recipes.models import (FavouriteRecipes, Follow, Ingredient, Recipe,
                            RecipeIngredients, ShoppingList, Tag)
from .paginators import PageLimitPagination
from .permissions import IsAdmin, IsAuthorOrReadOnly
from .serializers import (FollowSerializer, IngredientSerializer,
                          RecipeFollowSerializer, RecipeGetSerializer,
                          RecipesSerializer, TagSerializer)
from .utils import delete_obj, post_obj

User = get_user_model()


class BaseViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
):
    permission_classes = (AllowAny,)
    pagination_class = None


class TagsViewSet(
    BaseViewSet,
    mixins.RetrieveModelMixin
):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class IngredientsViewSet(
    BaseViewSet,
    mixins.RetrieveModelMixin
):
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter,)
    filterset_class = IngredientFilter

    queryset = Ingredient.objects.all()


class RecipesViewSet(viewsets.ModelViewSet):
    serializer_class = RecipesSerializer
    pagination_class = PageLimitPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (IsAdmin | IsAuthorOrReadOnly,)
    queryset = Recipe.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeGetSerializer
        return RecipesSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response('Рецепт успешно удален',
                        status=status.HTTP_204_NO_CONTENT)

    @action(
            detail=False, methods=['post'],
            permission_classes=[IsAuthenticated]
        )
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
        return Response('Рецепт успешно создан',
                        status=status.HTTP_201_CREATED)

    @action(
            detail=True, methods=('POST', 'DELETE'),
            permission_classes=[IsAuthenticated]
        )
    def favorite(self, request, pk):
        if self.request.method == 'POST':
            return post_obj(
                request, pk, FavouriteRecipes, RecipeFollowSerializer
            )
        return delete_obj(request, pk, FavouriteRecipes)

    @action(
            detail=True, methods=('POST', 'DELETE'),
            permission_classes=[IsAuthenticated]
        )
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            return post_obj(request, pk, ShoppingList, RecipeFollowSerializer)
        return delete_obj(request, pk, ShoppingList)

    @action(
            detail=False, methods=('GET',),
            permission_classes=[IsAuthenticated]
        )
    def download_shopping_cart(self, request):
        if not request.user.cart.exists():
            return Response(
                'В корзине нет товаров', status=status.HTTP_400_BAD_REQUEST)
        ingredients = (
            RecipeIngredients.objects
            .filter(recipe__cart__user=request.user)
            .values('ingredients')
            .annotate(total_amount=Sum('amount'))
            .values_list(
                'ingredients__name',
                'total_amount',
                'ingredients__measurement_unit'
            )
        )

        text = ''
        for ingredient in ingredients:
            text += '{} - {} {}. \n'.format(*ingredient)

        file = HttpResponse(
            f'Покупки:\n {text}', content_type='text/plain'
        )

        file['Content-Disposition'] = ('attachment; filename=cart.txt')
        return file


class FollowListViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
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
