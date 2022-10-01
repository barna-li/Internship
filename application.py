import math
import os
import pandas as pd
from flask import Flask, render_template, request, jsonify, Response, url_for, redirect
from flask_cors import CORS, cross_origin
from application_logging.logger import App_Logger
from scaling.scaling import split_data
from featuring_engineering.featureEngineering import Encoding
from database_operation.Database_operation import DBOperation
from built_model.model_selection import ModelSelection

application = Flask(__name__)


@application.route('/', methods=['GET', 'POST'])  # To render Homepage
@cross_origin()
def home_page():
    return render_template('index.html')


def main():
    log_writer = App_Logger()
    file = open("application_logging/logging.txt", 'a+')
    try:
        open(f"{os.getcwd()}\\dataset.csv")
        log_writer.log(file, "file is already been imported from the cassandra database")
    except FileNotFoundError:
        log_writer.log(file, "file is being imported from the database")
        db = DBOperation()
        log_writer.log(file, "database connection is established")
        db.create_table("experim")
        db.insert_data("experim")
        db.retrieve_data("experim")
    finally:
        lb_obj = Encoding()
        cleaned_df = lb_obj.encode_df()
        sc = split_data(cleaned_df)
        model_selection = ModelSelection(sc)
        final_model = model_selection.model_selection()
        return [final_model, sc.scale]


@application.route('/predict', methods=['GET', 'POST'])
@cross_origin()
def predict():
    log_writer = App_Logger()
    file = open("application_logging/logging.txt", 'a+')
    try:
        if request.method == 'POST':
            gd, sc = main()
            my_dic = dict()
            my_dic["age"] = request.form['age'],
            my_dic["bmi"] = request.form['bmi'],
            my_dic['children'] = request.form['children'],
            my_dic['region'] = request.form['region'].lower(),
            my_dic['sex'] = request.form['sex'].lower(),
            my_dic['smoker'] = request.form['smoker'].lower(),
            df = pd.DataFrame(my_dic)
            transformed_data = Encoding.encode_df_for_prediction(df)
            log_writer.log(file, f"final prediction for input is {gd.predict(sc.transform(transformed_data))}")
            return render_template('result.html',
                                   data=f"Predicted expenses for given input is: {math.floor(gd.predict(sc.transform(transformed_data)))} $")
        else:
            return render_template('result.html',
                                   data="Sorry! Invalid request")
    except Exception as e:
        return render_template('result.html', data="Sorry your input is invalid [requested inputs for region:'southwest','southeast','northwest','northeast']")


if __name__ == "__main__":
    application.run(debug=True)


