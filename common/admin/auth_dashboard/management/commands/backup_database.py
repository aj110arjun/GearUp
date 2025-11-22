from django.core.management.base import BaseCommand
from django.conf import settings
import subprocess
import os
from datetime import datetime

class Command(BaseCommand):
    help = 'Backup main database to backup database (Ubuntu/Linux)'

    def handle(self, *args, **options):
        self.stdout.write('Starting database backup...')
        
        # Correct PostgreSQL paths for Ubuntu
        PG_DUMP_PATH = '/usr/bin/pg_dump'
        PSQL_PATH = '/usr/bin/psql'
        
        # Get database settings
        main_db = settings.DATABASES['default']
        backup_db = settings.DATABASES['backup']
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'/tmp/backup_{timestamp}.sql'
        
        # Create temp directory if needed
        os.makedirs(os.path.dirname(backup_file), exist_ok=True)
        
        try:
            # Step 1: Create backup dump
            self.stdout.write('Creating backup dump...')
            
            dump_cmd = [
                PG_DUMP_PATH,
                '-h', main_db['HOST'],
                '-U', main_db['USER'],
                '-d', main_db['NAME'],
                '-f', backup_file
            ]
            
            # Set password for pg_dump
            env = os.environ.copy()
            env['PGPASSWORD'] = main_db['PASSWORD']
            
            self.stdout.write(f'Running: {" ".join(dump_cmd)}')
            subprocess.run(dump_cmd, env=env, check=True, capture_output=True, text=True)
            
            self.stdout.write(self.style.SUCCESS(f'Backup created: {backup_file}'))
            
            # Step 2: Restore to backup DB
            self.stdout.write('Restoring to backup database...')
            
            restore_cmd = [
                PSQL_PATH,
                '-h', backup_db['HOST'],
                '-U', backup_db['USER'],
                '-d', backup_db['NAME'],
                '-f', backup_file
            ]
            
            env['PGPASSWORD'] = backup_db['PASSWORD']
            self.stdout.write(f'Running: {" ".join(restore_cmd)}')
            subprocess.run(restore_cmd, env=env, check=True, capture_output=True, text=True)
            
            self.stdout.write(self.style.SUCCESS('Backup completed successfully!'))
            
            # Clean temp file
            os.remove(backup_file)
        
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f'Command failed: {e}'))
            self.stdout.write(self.style.ERROR(f'STDERR: {e.stderr}'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Backup failed: {str(e)}'))
