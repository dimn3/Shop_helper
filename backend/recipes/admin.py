from django.contrib import admin

from .models import (FavouriteRecipes, Follow, Ingredient, Recipe,
                     RecipeIngredients, RecipeTags, ShoppingList, Tag)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)


class RecipeTagsInLine(admin.TabularInline):
    model = Recipe.tag.through
    extra = 1


class RecipeIngredientsInLine(admin.TabularInline):
    model = Recipe.ingredients.through
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id',
                    'name',
                    'author',
                    'pub_date',
                    'text',
                    'cooking_time',
                    'image',)
    list_filter = ('name', 'author__username', 'pub_date',)
    search_fields = ('name',)
    inlines = (RecipeTagsInLine, RecipeIngredientsInLine)


@admin.register(RecipeIngredients)
class RecipeIngredientsAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredients',)
    list_filter = ('recipe',)
    search_fields = ('recipe',)


@admin.register(RecipeTags)
class RecipeTagsAdmin(admin.ModelAdmin):
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


@admin.register(ShoppingList)
class ShoppingListAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'user',)
    list_filter = ('user',)
    search_fields = ('user',)
