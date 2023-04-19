from django.urls import include, path
from rest_framework import routers

from users.views import (FollowActionViewSet, FollowViewSet, UserLoginViewSet,
                         UserLogoutViewSet, UserViewSet)

from .views import IngredientsViewSet, RecipesViewSet, TagsViewSet

app_name = 'api'

router_v1 = routers.DefaultRouter()
router_v1_auth = routers.DefaultRouter()

router_v1_auth.register('token/login', UserLoginViewSet, basename='login')
router_v1_auth.register('token/logout', UserLogoutViewSet, basename='logout')

router_v1.register(
    'users/subscriptions',
    FollowViewSet,
    basename='subscriptions'
)
router_v1.register(
    r'users/(?P<id>\d+)/subscribe',
    FollowActionViewSet,
    basename='subscribe'
)
router_v1.register('users', UserViewSet, basename='users')

router_v1.register('tags', TagsViewSet, basename='tags')
router_v1.register('ingredients', IngredientsViewSet, basename='ingredients')
router_v1.register('recipes', RecipesViewSet, basename='recipes')

urlpatterns = [
    path('', include(router_v1.urls)),
    path('auth/', include(router_v1_auth.urls)),
]
