from scaling.scaling import split_data
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, make_scorer
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import KFold
from application_logging.logger import App_Logger


class RandomForest:
    """this class implements random forest tree algorithm
       sc:split_data -- this object coming from scaling class
       and object of split data class, which renders options to split and scale the data"""
    def __init__(self, sc: split_data):
        self.estimator = RandomForestRegressor()
        self.split_obj = sc
        self.param_grid = {
            'n_estimators': [10, 5],
            'max_depth': [2, 5, 6, 7],
            'min_samples_split': [2, 5, 7, 10],
            'min_samples_leaf': [1, 2, 4, 6],
        }
        self.log_file = open("application_logging/logging.txt", 'a+')
        self.logging = App_Logger()

    def hyper_parameter_tuning(self):
        try:
            self.logging.log(self.log_file, "hyperparameter tuning of random forest has begun")
            k_fold = KFold(n_splits=5, shuffle=True, random_state=42)
            grid = GridSearchCV(estimator=self.estimator,
                                param_grid=self.param_grid,
                                cv=k_fold,
                                scoring=make_scorer(r2_score),
                                n_jobs=-1)
            self.logging.log(self.log_file, "hyperparameter tuning has done successfully")
            return grid
        except Exception as e:
            self.logging.log(self.log_file, f"error occured while tuning due to {e}")
            raise e

    def train_model(self):
        """method used for training the model"""
        try:
            grid = self.hyper_parameter_tuning()
            y_train = self.split_obj.get_yTrain()
            scaled_x_train = self.split_obj.get_scaled_x_train()
            self.logging.log(self.log_file, "training of random forest model has begun")
            grid.fit(scaled_x_train, y_train)
            self.logging.log(self.log_file, f"training score of random forest is {grid.score(scaled_x_train, y_train)}")
            self.logging.log(self.log_file, "training done")
            return grid
        except Exception as e:
            self.logging.log(self.log_file, f"error occured due to {e}")
            raise e

    def predict_model(self):
        """method used to predict the model"""
        try:
            grid = self.train_model()
            scaled_x_test = self.split_obj.get_scaled_x_test()
            y_test = self.split_obj.get_yTest()
            self.logging.log(self.log_file, "predicitng started")
            final_score = grid.score(scaled_x_test, y_test)
            self.logging.log(self.log_file, f"testing score random forest is {final_score}")
            return [final_score, grid]
        except Exception as e:
            self.logging.log(self.log_file, f"error occured due to {e} while predicting")
            raise e








