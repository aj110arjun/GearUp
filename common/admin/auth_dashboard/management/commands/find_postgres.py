from django.core.management.base import BaseCommand
import os
import subprocess

class Command(BaseCommand):
    help = 'Find PostgreSQL installation (Ubuntu/Linux)'

    def handle(self, *args, **options):
        self.stdout.write('Searching for PostgreSQL...')

        # Common PostgreSQL installation paths on Ubuntu/Linux
        possible_paths = [
            "/usr/bin/pg_dump",
            "/usr/local/bin/pg_dump",
            "/usr/lib/postgresql/16/bin/pg_dump",
            "/usr/lib/postgresql/15/bin/pg_dump",
            "/usr/lib/postgresql/14/bin/pg_dump",
            "/usr/lib/postgresql/13/bin/pg_dump",
        ]

        found = False
        
        # Check common paths
        for path in possible_paths:
            if os.path.exists(path):
                self.stdout.write(self.style.SUCCESS(f"Found: {path}"))
                found = True
            else:
                self.stdout.write(f"Not found: {path}")

        # Check using `which`
        try:
            which_output = subprocess.getoutput("which pg_dump")
            if which_output and os.path.exists(which_output):
                self.stdout.write(self.style.SUCCESS(f"Found via 'which': {which_output}"))
                found = True
        except Exception:
            pass

        if not found:
            self.stdout.write(self.style.ERROR("PostgreSQL not found in common locations"))

        # Test DB connection
        from django.db import connections
        try:
            with connections['default'].cursor() as cursor:
                cursor.execute("SELECT version()")
                result = cursor.fetchone()
                self.stdout.write(self.style.SUCCESS(f"Database connection OK: {result[0]}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Database connection failed: {e}"))
