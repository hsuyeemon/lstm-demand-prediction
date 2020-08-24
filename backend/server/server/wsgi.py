"""
WSGI config for server project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')

application = get_wsgi_application()


# ML registry
import inspect
from apps.dl.registry import MLRegistry
from apps.dl.classifier.lstm import lstm_model

try:
    registry = MLRegistry() # create ML registry
    # Random Forest classifier
    rf = lstm_model()
    # add to ML registry
    registry.add_algorithm(endpoint_name = "classifier",
    algorithm_object = lstm_model(),
    algorithm_name = "LSTM witl multiple time lags",
    algorithm_status = "test",
    algorithm_version = "0.0.1",
    owner = "Hsu",
    algorithm_description = "lstm with keras with simple pre- and post-processing",
                            algorithm_code=inspect.getsource(lstm_model))

except Exception as e:
    print("Exception while loading the algorithms to the registry,", str(e))
