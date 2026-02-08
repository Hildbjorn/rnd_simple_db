from django.apps import AppConfig


class RndConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rnd'
    verbose_name = "База-НТИ"
    
    def ready(self):
        # Импортируем сигналы при старте приложения
        import rnd.signals
