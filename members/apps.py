from django.apps import AppConfig


class MembersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'members'

    def ready(self):
        # Register HEIC/HEIF support for Pillow so iPhone photos
        # can be processed by ImageKit and Django ImageFields.
        try:
            from pillow_heif import register_heif_opener
            register_heif_opener()
            print("✅ HEIC/HEIF support registered")
        except ImportError:
            print("⚠️ pillow-heif not installed – iPhone HEIC uploads may fail")
