"""
Recipe Model.
"""
from django.conf import settings
from django.db import models


class Recipe(models.Model):
    """Recipe Object."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=90)
    description = models.TextField(max_length=512, blank=True)
    time_minutes = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    link = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.title
