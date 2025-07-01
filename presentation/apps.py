from django.apps import AppConfig


class PresentationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'presentation'


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        import users.signals