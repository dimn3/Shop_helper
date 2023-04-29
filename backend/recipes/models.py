from django.db import models
from django.core.validators import MinValueValidator
from users.models import User


class Tag(models.Model):
    name = models.CharField(max_length=200)
    color = models.CharField(max_length=7, default='#ffffff', null=True)
    slug = models.SlugField(max_length=200, unique=True, null=True)

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'


class Ingredient(models.Model):
    name = models.CharField('Название', max_length=100)
    measurement_unit = models.CharField(
        'Ед. измерения',
        default='Грамм',
        max_length=200
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Индгредиенты'

    def __str__(self) -> str:
        return self.name[:30]


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта'
    )
    tags = models.ManyToManyField(
        Tag,
        through='TagsInRecipe',
        related_name='recipes'
    )
    name = models.CharField(max_length=50)
    image = models.ImageField(
        'Картинка',
        blank=True,
    )
    text = models.CharField('Текст', max_length=500)
    cooking_time = models.PositiveIntegerField('Время приготовления')

    class Meta:
        ordering = ['-id']
        default_related_name = 'recipes'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self) -> str:
        return self.name[:30]


class IngredientsInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredients_in_recipe'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredients_in_recipe'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество ингредиентов',
        default=1,
        validators=[MinValueValidator(1)]
    )

    class Meta:
        default_related_name = 'recipeingredients'
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'

    def __str__(self):
        return self.ingredient.name


class TagsInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='tags_in_recipe'
    )
    tags = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name='tags_in_recipe'
    )

    class Meta:
        default_related_name = 'recipetags'
        verbose_name = 'Тэг рецепта'
        verbose_name_plural = 'Тэги рецепта'

    def __str__(self) -> str:
        return f'TR: {self.tags.name}->{self.recipe.name}'[:30]


class ShoppingCart(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name='carts',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name='carts'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'user',),
                name='recipe_user_shoppingcart_unique'
            )
        ]
        ordering = ['-id']
        default_related_name = 'shopping_cart'
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

    def __str__(self):
        return f'{self.recipes} - {self.user}'


class FavouriteRecipes(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favourites',
        verbose_name='recipes',
        null=False
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favourites',
        verbose_name='user'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'user'),
                name='recipe_user_unique'
            )
        ]
        ordering = ['-id']
        default_related_name = 'favorites_recipes'
        verbose_name = 'Любимый рецепт'
        verbose_name_plural = 'Любимые рецепты'


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower'
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followings'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'following'),
                name='unique followers'),
            models.CheckConstraint(
                check=~models.Q(user=models.F('following')),
                name='do not selffollow'),
        ]
