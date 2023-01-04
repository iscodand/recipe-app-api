"""
Tests for user API.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


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
        """
        Test error returned if create user with password less than 8 chars.
        """
        payload = {
            'name': 'Test Name',
            'email': 'test@example.com',
            'password': 'pass'
        }
        response = self.client.post(CREATE_USER_URL, payload)

        user_exists = get_user_model().objects.filter(
            email=payload['email']).exists()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test generates token for valid credentials."""
        user_details = {
            'name': 'Test Name',
            'email': 'test@example.com',
            'password': 'password123'
        }
        create_user(**user_details)

        payload = {
            'email': 'test@example.com',
            'password': 'password123'
        }
        response = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials(self):
        """Test return error if credentials invalid."""
        create_user(email='test@example.com', password='goodpassword')

        payload = {
            'email': 'test@example.com',
            'password': 'badpassword',
        }
        response = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        """Test posting a blank password returns an error."""
        payload = {
            'email': 'test@example.com',
            'password': '',
        }
        response = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Test authentication is required for users."""
        response = self.client.get(ME_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test API requests that require authentication"""

    def setUp(self):
        self.user = create_user(
            name='Test Name',
            email='test@example.com',
            password='testpass123'
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged user."""
        response = self.client.get(ME_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            'name': self.user.name,
            'email': self.user.email
        })

    def test_post_me_not_allowed(self):
        """Test POST is not allowed for the me endpoint."""
        response = self.client.post(ME_URL, {})

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_update_user_profile(self):
        """Test updating the user profile for the authenticated user."""
        payload = {
            'name': 'Updated Name',
            'password': 'updatedpass'
        }
        response = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
