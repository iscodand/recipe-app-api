"""
Tests for recipe API.
"""
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models.recipe import (
    Recipe,
    Tag,
    Ingredient
)


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

    def test_create_recipe_with_tags(self):
        """Test creating a recipe with a list of tags is successful."""
        payload = {
            'title': 'Suculent Meat',
            'time_minutes': 45,
            'price': Decimal('20.50'),
            'tags': [{'name': 'Meats'}, {'name': 'Dinner'}]
        }
        response = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)

        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        """Test creating a recipe with existing tags."""
        tag_salad = Tag.objects.create(user=self.user, name='Salad')

        payload = {
            'title': 'Caesar Salad',
            'time_minutes': 10,
            'price': Decimal('5.50'),
            'tags': [{'name': 'Salad'}, {'name': 'Vegan'}]
        }
        response = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)

        self.assertIn(tag_salad, recipe.tags.all())

        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test creating tag when update a recipe."""
        recipe = create_recipe(user=self.user)

        payload = {
            'tags': [{'name': 'Lunch'}]
        }

        url = detail_url(recipe.id)
        response = self.client.patch(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='Lunch')
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test assigning an existing tag when updating a recipe."""
        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')
        payload = {
            'tags': [{'name': 'Lunch'}]
        }
        url = detail_url(recipe.id)
        response = self.client.patch(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """Test clearing a recipe tags."""
        tag = Tag.objects.create(user=self.user, name='Chinese')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {'tags': []}

        url = detail_url(recipe.id)
        response = self.client.patch(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredients(self):
        """Test creating a recipe with new ingredients."""
        payload = {
            'title': 'Salad',
            'time_minutes': 5,
            'price': Decimal('10.50'),
            'ingredients': [
                {'name': 'Lettuce'},
                {'name': 'Onion'},
                {'name': 'Tomato'}
            ]
        }

        response = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 3)

        for ingredient in payload['ingredients']:
            exists = Ingredient.objects.filter(
                user=self.user,
                name=ingredient['name']
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredients(self):
        """Test creating a recipe with existing ingredients."""
        cheese_ingredient = Ingredient.objects.create(
            user=self.user,
            name='Cheese'
        )

        payload = {
            'title': 'Pizza',
            'time_minutes': 60,
            'price': Decimal('20.50'),
            'ingredients': [
                {'name': 'Cheese'},
                {'name': 'Peperonni'},
                {'name': 'Mass'}
            ]
        }

        response = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 3)

        self.assertIn(cheese_ingredient, recipe.ingredients.all())

        for ingredient in payload['ingredients']:
            exists = Ingredient.objects.filter(
                user=self.user,
                name=ingredient['name']
            ).exists()
            self.assertTrue(exists)

    def test_create_ingredients_on_update(self):
        """Test creating an ingredient on recipe update."""
        recipe = create_recipe(user=self.user)

        payload = {
            'ingredients': [
                {'name': 'Corn'},
            ]
        }

        url = detail_url(recipe.id)
        response = self.client.patch(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ingredient = Ingredient.objects.get(user=self.user, name='Corn')
        self.assertIn(ingredient, recipe.ingredients.all())

    def test_update_recipe_assign_ingredients(self):
        """Test assigning an existing ingredient when updating a recipe."""
        recipe = create_recipe(user=self.user)
        ingredient_pea = Ingredient.objects.create(
            user=self.user,
            name='Pea-coat'
        )
        recipe.ingredients.add(ingredient_pea)

        ingredient_sausage = Ingredient.objects.create(
            user=self.user,
            name='Sausage'
        )
        payload = {
            'ingredients': [{'name': 'Sausage'}]
        }

        url = detail_url(recipe.id)
        response = self.client.patch(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient_sausage, recipe.ingredients.all())
        self.assertNotIn(ingredient_pea, recipe.ingredients.all())

    def test_clear_existing_ingredients(self):
        """Test clearing existing ingredients."""
        recipe = create_recipe(user=self.user)
        ingredient = Ingredient.objects.create(
            user=self.user,
            name='Olive Oil'
        )
        recipe.ingredients.add(ingredient)

        payload = {
            'ingredients': []
        }

        url = detail_url(recipe.id)
        response = self.client.patch(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)
