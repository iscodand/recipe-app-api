"""
Serializer for the Recipe API View.
"""
from rest_framework import serializers

from core.models.recipe import Recipe


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for the recipe object."""

    class Meta:
        model = Recipe
        fields = [
            'id', 'title', 'time_minutes',
            'price', 'link'
        ]
        read_only_fields = ['id']


class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for the recipe details object."""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description']
