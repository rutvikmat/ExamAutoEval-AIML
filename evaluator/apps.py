# evaluator/apps.py

from django.apps import AppConfig
import os
from django.conf import settings

class EvaluatorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'evaluator'

    # Global variable to hold the loaded HWR model
    hwr_model = None

    def ready(self):
        # Only load the model if not running migrations or other management commands
        if os.environ.get('RUN_MAIN', None) != 'true':
            print("Loading HWR Model...")
            # self.hwr_model = load_custom_crnn_model() # Placeholder function you'd implement
            print("HWR Model Loaded successfully.")

        # This is where you would call the custom model loading function
        # from .hwr_service import load_custom_crnn_model