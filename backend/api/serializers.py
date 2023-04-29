from django.db import transaction
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from users.serializers import CustomUserSerializer
from recipes.models import (FavouriteRecipes, Follow, Ingredient, Recipe,
                            IngredientsInRecipe, ShoppingCart, Tag)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        lookup_field = 'name'


class IngredientRecipeGetSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientsInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')
        read_only_fields = (
            'name',
            'color',
            'slug'
        )


class IngredientsListingSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(min_value=1, max_value=1000)

    class Meta:
        model = IngredientsInRecipe
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    ingredients = IngredientsListingSerializer(
        many=True,
        source='ingredients_in_recipe'
    )
    image = Base64ImageField()
    author = CustomUserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        )

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients_in_recipe')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        IngredientsInRecipe.objects.bulk_create(
            IngredientsInRecipe(
                amount=ingredient['amount'],
                ingredient=ingredient['id'],
                recipe=recipe,
            ) for ingredient in ingredients
        )
        return recipe


class RecipesSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientsListingSerializer(
        many=True,
        source='ingredients_in_recipe'
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    image = Base64ImageField(max_length=None, use_url=True)
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'name', 'ingredients', 'text', 'tags',
                  'cooking_time', 'image')

    @staticmethod
    def bulk_create_recipe(validated_data, recipe):
        ingredients_data = validated_data.pop('ingredients_in_recipes')
        bulk_create_data = [
            IngredientsInRecipe(
                recipe=recipe,
                ingredient=ingredient_data['id'],
                amount=ingredient_data['amount'])
            for ingredient_data in ingredients_data
        ]
        IngredientsInRecipe.objects.bulk_create(bulk_create_data)

    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        coocking_time = self.initial_data.get('cooking_time')
        tags = self.initial_data.get('tags')
        tags_sum = 0
        for tag in tags:
            tags_sum += 1
        ingredients_list = [ingredient['id'] for ingredient in ingredients]
        if not tags_sum > 0:
            raise serializers.ValidationError(
                'выберите хотя бы один тег'
            )
        if len(ingredients_list) == 0:
            raise serializers.ValidationError(
                'выберите хотя бы один ингредиент'
            )
        if coocking_time == '0':
            raise serializers.ValidationError(
                'время готовки должно быть больше нуля'
            )

        for ingredient in ingredients:
            if int(ingredient['amount']) <= 0:
                raise serializers.ValidationError(
                    'вес ингредиентов должен быть больше нуля'
                )
        if len(ingredients_list) != len(set(ingredients_list)):
            raise serializers.ValidationError(
                'какой-то ингредиент выбран больше одного раза'
            )
        return data

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.bulk_create_recipe(validated_data, recipe)

    def update(self, instance, validated_data):
        recipe = instance
        if 'tags' in self.validated_data:
            tags_data = validated_data.pop('tags')
            instance.tags.set(tags_data)
        if 'ingredients' in self.validated_data:
            with transaction.atomic():
                amount_set = IngredientsInRecipe.objects.filter(
                    recipe__id=instance.id)
                amount_set.delete()
                self.bulk_create_recipe(validated_data, recipe)
        return super().update(instance, validated_data)


class RecipeGetSerializer(serializers.ModelSerializer):
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField()
    ingredients = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
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
        return ShoppingCart.objects.filter(
            recipe=obj, user=request_user
        ).exists()

    def get_ingredients(self, obj):
        recipe_ingredients = IngredientsInRecipe.objects.filter(recipe=obj)
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
