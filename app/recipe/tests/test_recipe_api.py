"""
Tests for recipe API.
"""
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models.recipe import Recipe
from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer
)


RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """Create and return a detail URL."""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_recipe(user, **params):
    """Create and return a new sample recipe."""
    defaults = {
        'title': 'Sample Title',
        'description': 'Sample random description.',
        'time_minutes': 25,
        'price': Decimal('10.50'),
        'link': 'https://example.com/recipe.pdf'
    }
    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)

    return recipe


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicRecipeApiTests(TestCase):
    """Test the public attemps requests for Recipes API."""

    def setUp(self):
        self.client = APIClient()

    def test_retrieve_unauthorized(self):
        """Test auth is required to request."""
        response = self.client.get(RECIPES_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test API requests that require authentication."""

    def setUp(self):
        self.client = APIClient()

        self.user = create_user(email='user@example.com', password='pass1234')
        self.client.force_authenticate(self.user)

    def test_list_all_recipes(self):
        """Test retrieving a list of recipes"""
        create_recipe(self.user)
        create_recipe(self.user)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        response = self.client.get(RECIPES_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_list_recipes_of_authenticated_user(self):
        """Test list recipes is limited to authenticated user."""
        other_user = create_user(
            email='other@example.com',
            password='pass1234'
        )
        create_recipe(other_user)
        create_recipe(self.user)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        response = self.client.get(RECIPES_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test get recipe detail."""
        recipe = create_recipe(self.user)

        url = detail_url(recipe.id)
        response = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_recipe(self):
        """Test creating a new recipe."""
        payload = {
            'title': 'New Recipe',
            'description': 'A new description for a new recipe.',
            'time_minutes': 20,
            'price': Decimal('25.00'),
            'link': 'https://newrecipe.com/recipe.pdf'
        }
        response = self.client.post(RECIPES_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=response.data['id'])
        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)

        self.assertEqual(recipe.user, self.user)

    def test_partial_update_recipe(self):
        """Test partial update for a recipe."""
        original_link = 'https://example.com/recipe.pdf'
        recipe = create_recipe(
            user=self.user,
            title='New Title',
            link=original_link
        )

        payload = {'title': 'Uptaded Title'}
        url = detail_url(recipe.id)
        response = self.client.patch(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)

    def test_full_update_recipe(self):
        """Test full update for a recipe."""
        recipe = create_recipe(user=self.user)
        payload = {
            'title': 'New Title',
            'description': 'New random description.',
            'time_minutes': 45,
            'price': Decimal('45.50'),
            'link': 'https://recipes-api.com/recipe.pdf'
        }

        url = detail_url(recipe.id)
        response = self.client.put(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()
        get_recipe = Recipe.objects.get(id=response.data['id'])
        for key, value in payload.items():
            self.assertEqual(getattr(get_recipe, key), value)

    def test_update_user_raises_error(self):
        """Test update a user raises an error."""
        new_user = create_user(
            email='sample@example.com',
            password='pass1234'
        )
        recipe = create_recipe(self.user)

        payload = {'user': new_user}

        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()

        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test delete a recipe."""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_user_recipe_raises_error(self):
        """Test deleting other user recipe raises an error."""
        new_user = create_user(
            email='sample@example.com',
            password='pass1234'
        )
        recipe = create_recipe(user=new_user)

        url = detail_url(recipe.id)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())
