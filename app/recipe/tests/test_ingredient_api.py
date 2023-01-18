"""
Tests for ingredients API.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core.models.recipe import Ingredient
from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse('recipe:ingredient-list')


def detail_url(ingredient_id):
    return reverse('recipe:ingredient-detail', args=[ingredient_id])


def create_user(email='email@example.com', password='pass1234'):
    """Create and return a user."""
    return get_user_model().objects.create_user(
        email=email,
        password=password
    )


class PublicIngredientApiTests(TestCase):
    """Tests for unauthorized requests for the Ingredients API."""

    def setUp(self):
        self.client = APIClient()

    def test_retrieve_unauthorized(self):
        """Test auth is required for ingredients API."""
        response = self.client.get(INGREDIENTS_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTests(TestCase):
    """Tests for requests that requires authentication."""

    def setUp(self):
        self.client = APIClient()

        self.user = create_user()
        self.client.force_authenticate(user=self.user)

    def test_list_ingredients(self):
        """Test listing all ingredients for current user."""
        Ingredient.objects.create(user=self.user, name='Apple')
        Ingredient.objects.create(user=self.user, name='Tomato')

        ingredients = Ingredient.objects.all().order_by('-name')

        response = self.client.get(INGREDIENTS_URL)
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_list_ingredients_for_authenticated_user(self):
        """Test retrieve a list of ingredients for authenticated user."""
        user2 = create_user(email='user2@example.com')
        Ingredient.objects.create(user=user2, name='Orange')

        ingredient = Ingredient.objects.create(user=self.user, name='Beer')

        response = self.client.get(INGREDIENTS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], ingredient.id)
        self.assertEqual(response.data[0]['name'], ingredient.name)

    def test_update_ingredient_successful(self):
        """Test updating a ingredient is successful."""
        ingredient = Ingredient.objects.create(user=self.user, name='Lettuce')

        payload = {'name': 'Purple Lettuce'}

        url = detail_url(ingredient.id)
        response = self.client.patch(url, payload)
        ingredient.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(payload['name'], ingredient.name)

    def test_delete_ingredient_successful(self):
        """Test deleting a ingredient is successful."""
        ingredient = Ingredient.objects.create(user=self.user, name='Meat')

        url = detail_url(ingredient.id)
        response = self.client.delete(url)

        ingredient_exists = Ingredient.objects.filter(
            name=ingredient.name
        ).exists()

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ingredient_exists)
