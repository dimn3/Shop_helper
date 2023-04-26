from django.contrib import admin

from .models import (FavouriteRecipes, Follow, Ingredient, Recipe,
                     IngredientsInRecipe, TagsInRecipe, ShoppingCart, Tag)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)


class RecipeTagsInLine(admin.TabularInline):
    model = TagsInRecipe
    extra = 1


class RecipeIngredientsInLine(admin.TabularInline):
    model = IngredientsInRecipe
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id',
                    'name',
                    'author',
                    'text',
                    'cooking_time',
                    'image',)
    list_filter = ('name', 'author__username',)
    search_fields = ('name',)
    inlines = (RecipeTagsInLine, RecipeIngredientsInLine)


@admin.register(IngredientsInRecipe)
class IngredientsInRecipeAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient',)
    list_filter = ('recipe',)
    search_fields = ('recipe',)


@admin.register(TagsInRecipe)
class TagsInRecipeAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'tags',)
    list_filter = ('recipe',)
    search_fields = ('recipe',)


@admin.register(FavouriteRecipes)
class FavouriteRecipesAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'user',)
    list_filter = ('user',)
    search_fields = ('user',)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'following',)
    list_filter = ('user',)
    search_fields = ('user',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'user',)
    list_filter = ('user',)
    search_fields = ('user',)
