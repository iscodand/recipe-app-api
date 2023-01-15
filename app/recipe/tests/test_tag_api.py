"""
Tests for Tags API.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core.models.recipe import Tag
from recipe.serializers import TagSerializer


TAGS_URL = reverse('recipe:tag-list')


def detail_url(tag_id):
    return reverse('recipe:tag-detail', args=[tag_id])


def create_user(email='email@example.com', password='pass1234'):
    """Create and return a user."""
    return get_user_model().objects.create_user(
        email=email,
        password=password
    )


class PublicTagApiTests(TestCase):
    """Tests for unauthorized requests for the Tags API."""

    def setUp(self):
        self.client = APIClient()

    def test_retrieve_unauthorized(self):
        """Test auth is required to Tags API."""
        response = self.client.get(TAGS_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagApiTests(TestCase):
    """Tests API requests that requires authentication."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(user=self.user)

    def test_list_tags(self):
        """Test retrieving a list of tags."""
        Tag.objects.create(user=self.user, name='Vegan')
        Tag.objects.create(user=self.user, name='Dessert')

        tags = Tag.objects.all().order_by('-name')

        response = self.client.get(TAGS_URL)
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_list_tags_of_authenticated_user(self):
        """Test retrieve a list of tags for authenticated user."""
        user2 = create_user(email='user2@example.com')
        Tag.objects.create(name='Fruity', user=user2)

        user_tag = Tag.objects.create(name='Meats', user=self.user)

        response = self.client.get(TAGS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], user_tag.name)
        self.assertEqual(response.data[0]['id'], user_tag.id)

    def test_update_tag_successful(self):
        """Test updating a tag is successful."""
        tag = Tag.objects.create(user=self.user, name='After Dinner')

        payload = {'name': 'Dessert'}

        url = detail_url(tag.id)
        response = self.client.patch(url, payload)
        tag.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(tag.name, payload['name'])

    def test_delete_tag_successful(self):
        """Test deleting a tag is successful."""
        tag = Tag.objects.create(user=self.user, name='Dinner')

        url = detail_url(tag.id)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(user=self.user).exists())
