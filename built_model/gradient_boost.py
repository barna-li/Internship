from sklearn.ensemble import GradientBoostingRegressor
from scaling.scaling import split_data
import pandas as pd
from application_logging.logger import App_Logger



class GradientBoost:
    """this class implements Gradient decent tree algorithm
       sc:split_data -- this object coming from scaling class
       and object of split data class, which renders options to split and scale the data"""
    def __init__(self, sc: split_data):
        self.gb = GradientBoostingRegressor()
        self.split_obj = sc
        self.log_file = open("application_logging/logging.txt", 'a+')
        self.logging = App_Logger()

    def train_model(self):
        """ this methods used for training the model"""
        try:
            y_train = self.split_obj.get_yTrain()
            scaled_x_train = self.split_obj.get_scaled_x_train()
            self.logging.log(self.log_file, "training of Gradient boost algorithm has begun")
            self.gb.fit(scaled_x_train, y_train)
            self.logging.log(self.log_file, f"training score of gradient boost is {self.gb.score(scaled_x_train, y_train)}")
            self.logging.log(self.log_file, "training done")
            return self.gb
        except Exception as e:
            self.logging.log(self.log_file, f"training is failed due to {e}")
            raise e

    def predict_model(self):
        """this method is used to predict the model"""
        try:
            gb = self.train_model()
            scaled_x_test = self.split_obj.get_scaled_x_test()
            y_test = self.split_obj.get_yTest()
            self.logging.log(self.log_file, "prediction started")
            df = pd.DataFrame(gb.predict(scaled_x_test))
            df.to_csv("prediction.csv")
            self.logging.log(self.log_file, f"testing score of gradient boost is {gb.score(scaled_x_test, y_test)}")
            return [gb.score(scaled_x_test, y_test), gb]
        except Exception as e:
            self.logging.log(self.log_file, f"training is failed due to {e}")
            raise e



