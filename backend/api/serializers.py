from django.db import transaction
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers, status

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
    recipe = serializers.PrimaryKeyRelatedField(read_only=True)
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientsInRecipe
        fields = ('id', 'amount', 'recipe')


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
    cooking_time = serializers.IntegerField()

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

    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        tags = self.initial_data.get('tags')
        tags_sum = 0
        for tag in tags:
            tags_sum += 1
        ingredients_list = [ingredient['id'] for ingredient in ingredients]
        if not tags_sum > 0:
            raise serializers.ValidationError(
                'выберите хотя бы один тег'
            )
        for ingredient in ingredients:
            if int(ingredient['amount']) <= 0:
                raise serializers.ValidationError(
                   'Вес ингредиентов должен быть больше нуля'
                )
        if len(ingredients_list) == 0:
            raise serializers.ValidationError(
                'выберите хотя бы один ингредиент'
            )
        if len(ingredients_list) != len(set(ingredients_list)):
            raise serializers.ValidationError(
                'какой-то ингредиент выбран больше одного раза'
            )
        return data

    def validate_cooking_time(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                'Время готовки должно быть больше нуля'
            )
        return value


    def to_representation(self, instance):
        self.fields.pop('ingredients')
        self.fields.pop('tags')
        representation = super().to_representation(instance)
        representation['ingredients'] = IngredientRecipeGetSerializer(
            IngredientsInRecipe.objects.filter(recipe=instance), many=True
        ).data
        representation['tags'] = TagSerializer(
            instance.tags, many=True
        ).data
        return representation

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients_in_recipe')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)

        bulk_create_data = [
            IngredientsInRecipe(
                recipe=recipe,
                ingredient=ingredient_data['id'],
                amount=ingredient_data['amount'])
            for ingredient_data in ingredients_data
        ]
        IngredientsInRecipe.objects.bulk_create(bulk_create_data)
        return recipe

    def update(self, instance, validated_data):
        if 'tags' in self.validated_data:
            tags_data = validated_data.pop('tags')
            instance.tags.set(tags_data)
        if 'ingredients_in_recipe' in self.validated_data:
            ingredients_data = validated_data.pop('ingredients_in_recipe')
            with transaction.atomic():
                amount_set = IngredientsInRecipe.objects.filter(
                    recipe__id=instance.id)
                amount_set.delete()
                bulk_create_data = (
                    IngredientsInRecipe(
                        recipe=instance,
                        ingredient=ingredient_data['id'],
                        amount=ingredient_data['amount'])
                    for ingredient_data in ingredients_data
                )
                IngredientsInRecipe.objects.bulk_create(bulk_create_data)
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
