"""
Django command to wait for the database to be available.
"""
import time

from psycopg2 import OperationalError as Psycopg2Error

from django.db.utils import OperationalError
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Django command to wait for database."""

    def handle(self, *args, **options):
        """Entrypoint for command."""
        self.stdout.write("Waiting for database...")
        database_up = False

        while database_up is False:
            try:
                self.check(databases=['default'])
                database_up = True
            except (Psycopg2Error, OperationalError):
                self.stdout.write("Database unavaible. Waiting 1 second...")
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS("Database avaible!"))
