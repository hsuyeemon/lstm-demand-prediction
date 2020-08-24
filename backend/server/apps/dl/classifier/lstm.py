# file backend/server/apps/ml/income_classifier/random_forest.py
from keras.models import load_model
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import MinMaxScaler
import pandas as pd

class lstm_model:
    def __init__(self):
        path_to_artifacts = "../../research/"
        #self.values_fill_missing =  joblib.load(path_to_artifacts + "train_mode.joblib")
        #self.encoders = joblib.load(path_to_artifacts + "encoders.joblib")
        #self.model = joblib.load(path_to_artifacts + "random_forest.joblib")

        self.model = load_model(path_to_artifacts+'model.h5')

    def preprocessing(self, input_data):
    #def preprocessing(self):
        # JSON to pandas DataFrame
        #input_data = pd.DataFrame(input_data, index=[0])

        input_data = pd.read_csv('~/work/Data/'+input_data)
        print(input_data.shape)
        input_data = input_data.to_numpy()

        num_lags = 30
        num_features = 1
        n_obs = num_lags * num_features
        test_X, test_y = input_data[:, :n_obs], input_data[:, -num_features]
        test_X = test_X.reshape((test_X.shape[0], num_lags, num_features))
        print(test_y.shape,test_X.shape)
        input_data = test_X
        # fill missing valuesload_model('model.h5')
        #input_data.fillna(self.values_fill_missing)


        return input_data

    def predict(self, input_data):

        return self.model.predict(input_data)

    def postprocessing(self, input_data):
        label = ""
        if input_data[1] > 5:
            label = "High demand"
        else:
            label = "Low demand"

        return {"demand": input_data[1], "label": label, "status": "OK"}

    def compute_prediction(self, input_data):
        try:
            print("try")
            input_data = self.preprocessing(input_data)
            prediction = self.predict(input_data) # only one sample
            prediction = self.postprocessing(prediction)
        except Exception as e:
            print(e)
            return {"status": "Error", "message": str(e)}

        return prediction
