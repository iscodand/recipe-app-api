"""
Test Models.
"""
from unittest.mock import patch
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model

from core.models import recipe


def create_user(email='user@example.com', password='pass1234'):
    return get_user_model().objects.create_user(
        email=email,
        password=password
    )


class UserModelTests(TestCase):
    """Test for User Model."""

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


class RecipesModelTests(TestCase):
    """Test for Recipes Model."""

    def test_create_recipe(self):
        """Test create a new recipe."""
        user = get_user_model().objects.create_user(
            'user@example.com',
            'pass1234'
        )

        new_recipe = recipe.Recipe.objects.create(
            user=user,
            title='Recipe Title',
            time_minutes=5,
            price=Decimal('5.50'),
            description='A fun description.'
        )

        self.assertEqual(new_recipe.user, user)
        self.assertEqual(str(new_recipe), new_recipe.title)

    def test_create_tag(self):
        """Test creating tag is successful."""
        user = create_user()

        tag = recipe.Tag.objects.create(
            user=user,
            name='Sample Tag',
        )

        self.assertEqual(str(tag), tag.name)

    def test_create_ingredient(self):
        """Test creating ingredient is successful."""
        user = create_user()

        ingredient = recipe.Ingredient.objects.create(
            user=user,
            name='Sample Ingredient'
        )

        self.assertEqual(str(ingredient), ingredient.name)

    @patch('core.models.uuid.uuid4')
    def test_recipe_file_name_uuid(self, mock_uuid):
        """Test generating image path."""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = recipe.recipe_image_file_path(None, 'example.jpg')

        self.assertEqual(file_path, f'uploads/recipe/{uuid}.jpg')
