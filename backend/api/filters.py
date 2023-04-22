import django_filters
from django.contrib.auth import get_user_model
from django_filters.rest_framework import NumberFilter

from recipes.models import Ingredient, Recipe, Tag

UserModel = get_user_model()


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ('name', 'measurement_unit')


class RecipeFilter(django_filters.FilterSet):
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = NumberFilter(
        method='get_is_favorited'
    )
    is_in_shopping_cart = NumberFilter(
        method='get_is_in_shopping_cart',
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author')

    def get_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value == 1:
            return queryset.filter(is_favorited__user=user)
        elif value == 0:
            return queryset.exclude(is_favorited__user=user)
        else:
            return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value == 1:
            return queryset.filter(is_in_shopping_cart__user=user)
        elif value == 0:
            return queryset.exclude(is_in_shopping_cart__user=user)
        else:
            return queryset
