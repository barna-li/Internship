import os
import pandas as pd
import numpy as np
from application_logging.logger import App_Logger


class Encoding:
    """this class is used for encoding"""
    def __init__(self):
        self.dataset_location = f"{os.getcwd()}/dataset.csv"
        self.dataset = pd.read_csv(self.dataset_location)
        self.log_file = open("application_logging/logging.txt", 'a+')
        self.logging = App_Logger()

    def encode_df(self):
        """method used for encoding the training data"""
        try:
            self.logging.log(self.log_file, "encoding started")
            self.dataset['smoker'] = np.where(self.dataset['smoker'] == 'yes', 1, 0)
            self.dataset['sex'] = np.where(self.dataset['sex'] == 'male', 1, 0)
            direction = list(self.dataset.region.unique())
            dic = {feature: count for count, feature in enumerate(direction, 0)}
            self.dataset["region"] = self.dataset["region"].map(dic)
            self.logging.log(self.log_file, "done with encoding")
            return self.dataset
        except Exception as e:
            self.logging.log(self.log_file, f"encoding failed due to {e}")
            raise e

    @staticmethod
    def encode_df_for_prediction(dataset):
        """this is the static method which actually used to encode the data coming
        from UI """
        try:
            dataset['smoker'] = np.where(dataset['smoker'] == 'yes', 1, 0)
            dataset['sex'] = np.where(dataset['sex'] == 'male', 1, 0)
            dic = {'southwest': 0, 'southeast': 1, 'northwest': 2, 'northeast': 3}
            dataset["region"] = dataset["region"].map(dic)
            log_file = open("application_logging/logging.txt", 'a+')
            logging = App_Logger()
            logging.log(log_file, "done with encoding")
            return dataset
        except Exception as e:
            raise e



