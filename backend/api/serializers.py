from django.db import transaction
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from users.serializers import CustomUserSerializer
from recipes.models import (FavouriteRecipes, Follow, Ingredient, Recipe,
                            RecipeIngredients, ShoppingList, Tag)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        lookup_field = 'name'


class IngredientRecipeSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(read_only=True)
    amount = serializers.IntegerField(write_only=True)
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'amount', 'recipe')


class IngredientRecipeGetSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'name', 'measurement_unit', 'amount')
        validators = (
            UniqueTogetherValidator(
                queryset=RecipeIngredients.objects.all(),
                fields=('ingredient', 'recipe')
            )
        )


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')
        read_only_fields = (
            'name',
            'color',
            'slug'
        )


class RecipesSerializer(serializers.ModelSerializer):
    ingredients = IngredientRecipeSerializer(many=True)
    author = CustomUserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    image = Base64ImageField(max_length=None, use_url=True)
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'name', 'text', 'ingredients', 'tags',
                  'cooking_time', 'image')
        read_only_fields = ('id', 'author', 'tags')

    @staticmethod
    def bulk_create_recipe(validated_data, recipe):
        ingredients_data = validated_data.pop('ingredients')
        bulk_create_data = [
            RecipeIngredients(
                recipe=recipe,
                ingredient=ingredient_data['ingredient'],
                amount=ingredient_data['amount'])
            for ingredient_data in ingredients_data
        ]
        return RecipeIngredients.objects.bulk_create(bulk_create_data)

    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        tags = self.initial_data.get('tags')
        tags_list = [tag['id'] for tag in tags]
        ingredients_list = [ingredient['id'] for ingredient in ingredients]
        if not len(tags_list) > 0:
            raise serializers.ValidationError(
                'выберите хотя бы один тег'
            )
        if len(ingredients_list) == 0:
            raise serializers.ValidationError(
                'выберите хотя бы один ингредиент'
            )
        if not self.initial_data.get('cooking_time') > 0:
            raise serializers.ValidationError(
                'время готовки должно быть больше нуля'
            )

        for ingredient in ingredients:
            if not ingredient['amount'] > 0:
                raise serializers.ValidationError(
                    'вес ингредиентов должен быть больше нуля'
                )
        if len(ingredients_list) != len(set(ingredients_list)):
            raise serializers.ValidationError(
                'какой-то ингредиент выбран больше одного раза'
            )
        return data

    def create(self, validated_data):
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)

        self.bulk_create_recipe(validated_data, recipe)
        return recipe

    def update(self, instance, validated_data):
        recipe = instance
        if 'tags' in self.validated_data:
            tags_data = validated_data.pop('tags')
            instance.tags.set(tags_data)
        if 'ingredients' in self.validated_data:
            with transaction.atomic():
                amount_set = RecipeIngredients.objects.filter(
                    recipe__id=instance.id)
                amount_set.delete()
                self.bulk_create_recipe(validated_data, recipe)
        return super().update(instance, validated_data)


class RecipeGetSerializer(serializers.ModelSerializer):
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field="username",
        default=serializers.CurrentUserDefault(),
    )
    image = Base64ImageField()
    ingredients = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tag',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj):
        request_user = self.context['request'].user
        if request_user.is_anonymous:
            return False
        return FavouriteRecipes.objects.filter(
            recipe=obj, user=request_user
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        request_user = self.context['request'].user
        if request_user.is_anonymous:
            return False
        return ShoppingList.objects.filter(
            recipe=obj, user=request_user
        ).exists()

    def get_ingredients(self, obj):
        recipe_ingredients = RecipeIngredients.objects.filter(recipe=obj)
        return IngredientRecipeGetSerializer(
            recipe_ingredients, many=True
        ).data


class RecipeFollowSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='following.id')
    email = serializers.ReadOnlyField(source='following.email')
    username = serializers.ReadOnlyField(source='following.username')
    first_name = serializers.ReadOnlyField(source='following.first_name')
    last_name = serializers.ReadOnlyField(source='following.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source='following.recipes.count')

    class Meta:
        model = Follow
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=['following', 'user']
            )
        ]

    def get_is_subscribed(self, obj):
        return Follow.objects.filter(
            user=obj.user, following=obj.following
        ).exists()

    def get_recipes(self, obj):
        queryset = obj.following.recipes.all()
        return RecipeFollowSerializer(queryset, many=True).data

    def validate(self, data):
        author_id = self.context.get('id')
        user_id = self.context.get('request').user.id
        if Follow.objects.filter(
                user=user_id,
                following=author_id
        ).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на данного пользователя'
            )
        return data
