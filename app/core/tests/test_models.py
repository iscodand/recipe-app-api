"""
Test Models.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model


class ModelTests(TestCase):
    """Test Models."""

    def test_create_user_with_email_successful(self):
        """Test creating a user with and email is successful."""
        email = 'test@example.com'
        password = 'testpass123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test email is normalized for new users."""
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['Test3@EXAMPLE.COM', 'Test3@example.com'],
            ['Test4@example.COM', 'Test4@example.com'],
        ]

        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(
                email=email,
                password='samplepass123'
            )
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """Test that creating a user without an email raises a ValueError"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                email='',
                password='test123'
            )

    def test_create_superuser(self):
        """Test creating a superuser."""
        superuser = get_user_model().objects.create_superuser(
            email='superuser@example.com',
            password='test123'
        )

        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)
