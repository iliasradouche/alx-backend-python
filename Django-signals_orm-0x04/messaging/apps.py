from django.apps import AppConfig


class MessagingConfig(AppConfig):
    """
    Configuration class for the messaging app.
    This class handles the app configuration and ensures signals are properly connected.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'messaging'
    verbose_name = 'Messaging System'

    def ready(self):
        """
        Called when Django starts up.
        This method imports the signals module to ensure signal handlers are registered.
        """
        try:
            # Import signals to register signal handlers
            from . import signals
        except ImportError:
            # Handle the case where signals module might not be available during migrations
            pass