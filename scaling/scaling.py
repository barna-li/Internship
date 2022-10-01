from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from application_logging.logger import App_Logger


class split_data:
    """this class is used to split the data"""
    def __init__(self, dataset):
        self.dataset = dataset
        self.scale = StandardScaler()
        self.log_file = open("application_logging/logging.txt", 'a+')
        self.logging = App_Logger()

    def split(self):
        try:
            df = self.dataset.copy()
            x = df.drop(['id', 'expenses'], axis=1)
            y = df['expenses']
            x_train, x_test, y_train, y_test = train_test_split(x, y, random_state=0)
            self.logging.log(self.log_file, "splitting done")
            return [x_train, x_test, y_train, y_test]
        except Exception as e:
            self.logging.log(self.log_file, f"error occured during splitting operation due to {e}")
            raise e

    def get_xTrain(self):
        return self.split()[0]

    def get_xTest(self):
        return self.split()[1]

    def get_yTrain(self):
        return self.split()[2]

    def get_yTest(self):
        return self.split()[3]

    def scale_data(self):
        try:
            scaled_x_train = self.scale.fit_transform(self.get_xTrain())
            self.logging.log(self.log_file, "training scaling is done")
            scaled_x_test = self.scale.transform((self.get_xTest()))
            self.logging.log(self.log_file, "testing scaling is done")
            return [scaled_x_train, scaled_x_test]
        except Exception as e:
            self.logging.log(self.log_file, f"error occured while scaling data due to {e}")
            raise e

    def get_scaled_x_train(self):
        return self.scale_data()[0]

    def get_scaled_x_test(self):
        return self.scale_data()[1]