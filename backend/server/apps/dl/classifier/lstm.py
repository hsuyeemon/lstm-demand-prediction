# file backend/server/apps/ml/income_classifier/random_forest.py
from keras.models import load_model
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import MinMaxScaler
import pandas as pd
import json
from numpy import concatenate

class lstm_model:
    def __init__(self):
        self.path_to_artifacts = "../../research/"
        #self.values_fill_missing =  joblib.load(path_to_artifacts + "train_mode.joblib")
        #self.encoders = joblib.load(path_to_artifacts + "encoders.joblib")
        #self.model = joblib.load(path_to_artifacts + "random_forest.joblib")



        self.model = load_model(self.path_to_artifacts+'model.h5')
        self.num_lags = 30
        self.num_features = 1
        self.scaler = MinMaxScaler(feature_range=(0, 1))

    # convert series to supervised learning
    def series_to_supervised(self,data, n_in=1, n_out=1, dropnan=True):
        n_vars = 1 if type(data) is list else data.shape[1]
        df = pd.DataFrame(data)
        cols, names = list(), list()
    	# input sequence (t-n, ... t-1)
        for i in range(n_in, 0, -1):
            cols.append(df.shift(i))
            names += [('var%d(t-%d)' % (j+1, i)) for j in range(n_vars)]
    	# forecast sequence (t, t+1, ... t+n)
        for i in range(0, n_out):
            cols.append(df.shift(-i))
            if i == 0:
                names += [('var%d(t)' % (j+1)) for j in range(n_vars)]
            else:
                names += [('var%d(t+%d)' % (j+1, i)) for j in range(n_vars)]
    	# put it all together
        print("Series")
        print(cols)

        agg = pd.concat(cols, axis=1)
        agg.columns = names
    	# drop rows with NaN values
        if dropnan:
            agg.dropna(inplace=True)
        return agg

    def setTimeLags(self,timelags):
        self.timelags = timelags
        if timelags == 30:
            self.model = load_model(self.path_to_artifacts+'model.h5')
        elif timelags == 90:
            self.model = load_model(self.path_to_artifacts+'model-90days.h5')
        else:
            self.model = load_model(self.path_to_artifacts+'model-365days.h5')

    def preprocessing(self, history):

        print("preprocessing")
        history_data = pd.read_csv('~/work/Data/'+history)
        print("hist",history_data.head(10))
        # manually specify column names
        history_data.columns = ['date', 'quantity']
        history_data.index.name = 'date'
        print(history_data.head(10))

        date_index = history_data['date'].values
        ii = self.timelags
        date_index = date_index[-ii:]

        print(history_data.head(10))
        values = history_data.values

        # integer encode direction
        encoder = LabelEncoder()
        values[:,0] = encoder.fit_transform(values[:,0])


        # normalize features
        #scaler = MinMaxScaler(feature_range=(0, 1))
        scaled = self.scaler.fit_transform(values)

        # frame as supervised learning
        reframed = self.series_to_supervised(scaled, self.num_lags, 1)

        values = reframed.values

        #input_data = input_data.to_numpy()
        input_data = values[-ii:, :]


        n_obs = self.num_lags * self.num_features
        test_X, test_y = input_data[:, :n_obs], input_data[:, -self.num_features]
        test_X = test_X.reshape((test_X.shape[0], self.num_lags, self.num_features))
        print(test_y.shape,test_X.shape)
        input_data = test_X

        # fill missing valuesload_model('model.h5')
        #input_data.fillna(self.values_fill_missing)


        return input_data,date_index

    def predict(self, input_data):

        return self.model.predict(input_data)

    def postprocessing(self, prediction,input_data,date_index):


        input_data = input_data.reshape((input_data.shape[0], self.num_lags*self.num_features))

        #scaler = MinMaxScaler(feature_range=(0, 1))

        # invert scaling for forecast
        inv_yhat = concatenate((prediction, input_data[:, -1:]), axis=1)
        print(inv_yhat.shape)

        inv_yhat = self.scaler.inverse_transform(inv_yhat)
        inv_yhat = inv_yhat[:,0]
        print(inv_yhat)

        objret = []
        #print(input_data)
        in_d = 0
        for i in inv_yhat:
            label = ""
            print("postprocessing",i)
            if i > 5:
                label = "High demand"
            else:
                label = "Low demand"




            objret.append({"date":date_index[in_d],"demand":str(round(i, 2)), "label": label, "status": "OK"})
            in_d = in_d + 1
        #print(type(objret))
        return objret

    def compute_prediction(self, history):
        print("prediction")
        try:


            input_data,date_index = self.preprocessing(history)
            prediction = self.predict(input_data) # only one sample
            print("predict")
            prediction = self.postprocessing(prediction,input_data,date_index)
        except Exception as e:
            print(e)
            return {"status": "Error", "message": str(e)}

        return prediction
