from django.apps import AppConfig
from django.db.models.signals import post_migrate

# class UsersConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'users'


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        from django.contrib.auth.models import Group
        from django.db.utils import OperationalError, ProgrammingError

        def create_roles(sender, **kwargs):
            roles = ['admin', 'teacher', 'curator', 'student', 'parent']
            for role in roles:
                Group.objects.get_or_create(name=role)

        try:
            post_migrate.connect(create_roles, sender=self)
        except (OperationalError, ProgrammingError):
            # Під час початкових міграцій можуть бути помилки — ігноруємо
            pass