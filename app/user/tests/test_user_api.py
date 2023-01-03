"""
Tests for user API.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test the public features of user API."""

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """Test creating a user successful."""
        payload = {
            'name': 'Test Name',
            'email': 'test@example.com',
            'password': 'pass1234'
        }
        response = self.client.post(CREATE_USER_URL, payload)

        user = get_user_model().objects.get(email=payload['email'])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', response.data)

    def test_create_user_with_email_exists_error(self):
        """Test error returned if user with email already exists."""
        payload = {
            'name': 'Test Name',
            'email': 'test@example.com',
            'password': 'pass1234'
        }
        create_user(**payload)

        response = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_with_password_too_short(self):
        """Test error returned if create user with password less than 8 chars."""
        payload = {
            'name': 'Test Name',
            'email': 'test@example.com',
            'password': 'pass'
        }
        response = self.client.post(CREATE_USER_URL, payload)

        user_exists = get_user_model().objects.filter(email=payload['email']).exists()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(user_exists)