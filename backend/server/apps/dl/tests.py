from django.test import TestCase

from apps.dl.classifier.lstm import lstm_model

import inspect
from apps.dl.registry import MLRegistry

# ...
# the rest of the code
# ...




class MLTests(TestCase):
    # add below method to MLTests class:
    def test_registry(self):
        registry = MLRegistry()
        self.assertEqual(len(registry.endpoints), 0)
        endpoint_name = "classifier"
        algorithm_object = lstm_model()
        algorithm_name = "LSTM witl multiple time lags"
        algorithm_status = "test"
        algorithm_version = "0.0.1"
        algorithm_owner = "Hsu"
        algorithm_description = "lstm with keras with simple pre- and post-processing"
        algorithm_code = inspect.getsource(lstm_model)
        # add to registry
        registry.add_algorithm(endpoint_name, algorithm_object, algorithm_name,
                    algorithm_status, algorithm_version, algorithm_owner,
                    algorithm_description, algorithm_code)
        # there should be one endpoint available
        self.assertEqual(len(registry.endpoints), 1)
        
    def test_rf_algorithm(self):


        input_data = 'test.csv'
        my_alg = lstm_model()
        print('load model')
        response = my_alg.compute_prediction(input_data)
        self.assertEqual('OK', response['status'])
        self.assertTrue('label' in response)
        #self.assertEqual('<=50K', response['label'])
        self.assertTrue('demand' in response)
