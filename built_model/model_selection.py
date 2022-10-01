from built_model.decison_tree import DecisionTree
from built_model.random_forest import RandomForest
from built_model.gradient_boost import GradientBoost
from scaling.scaling import split_data
from application_logging.logger import App_Logger
import pickle


class ModelSelection:
    """this class used for selecting the best algorithm out of many alogrithm"""
    def __init__(self, sc: split_data):
        self.scale = sc
        self.log_file = open("application_logging/logging.txt", 'a+')
        self.logging = App_Logger()

    def model_selection(self):
        try:
            self.logging.log(self.log_file, "model selection has begun")
            gradient_boost = GradientBoost(self.scale)
            gradient_boost_score, g_obj = gradient_boost.predict_model()
            self.logging.log(self.log_file, f"gradient boost score is {gradient_boost_score}")
            random_forest = RandomForest(self.scale)
            random_forest_score, r_obj = random_forest.predict_model()
            self.logging.log(self.log_file, f"random forest score is {random_forest_score}")
            decision_tree = DecisionTree(self.scale)
            decision_tree_score, d_obj = decision_tree.predict_model()
            self.logging.log(self.log_file, f"decision tree score is {decision_tree_score}")
            model_name = "gradient boost"
            max_score_model = g_obj
            max_score = gradient_boost_score
            if random_forest_score > max_score:
                max_score = random_forest_score
                max_score_model = r_obj
                model_name = "random_forest"
            elif decision_tree_score > max_score:
                max_score = decision_tree_score
                max_score_model = d_obj
                model_name = "decision tree"
            self.logging.log(self.log_file, f"maximum score model is {model_name} with score: {max_score}")
            return max_score_model
        except Exception as e:
            self.logging.log(self.log_file, f"error has occured due to {e} while model selection")
            raise e


