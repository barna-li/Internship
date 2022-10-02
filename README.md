# INSURANCE PREMIUM PREDICTION

# Objective
The objective of the project clearly predicts the cost of the insurance plan which gives the individual, an idea as to what kind of insurance premium they can prefer over a certain period of time looking at the constraints and viabilities of the insurance plan.e

# Problem Statement
The goal of this project is to give people an estimate of how much they need based on their individual health situation. After that, customers can work with any health insurance carrier and its plans and perks while keeping the projected cost from our study in mind. 

# Approach
1) Insertion into Database : Cassandra Database is used for insertion and retrieval of the insurance premium dataset used for prediction.
2) Data Visualisation : Plotted countplots, barplots, piecharts to get insights about the relation between dependent and independent variables.
3) Feature Engineering : Encoded three categorical variables into numeric, and performed standarisation of data to get all values in a fixed range.
4) Model Building : Tried out these 3 Machine learning algorithms along wiht hyperparameterized tuning using Grid Search CV that’s best fit and gives the highest accuracy for the insurance premium case:
     -Decision tree Regressor 
     -Gradient Boosting Regressor
     -Random forest Regressor 
      
5) Deployment : Once the best algorithm is choosen, our Flask main file which is the application.py file will be called to test our API endpoints in the developing environment.It'll act as the central configuration object for the entire application usually setting up the pieces of the application required for extended functionality.This app once create can be run on local machine as well as we have deployed it in AWS cloud plateform.
 
# Deployment Link 

http://inspremium-env.eba-tgvagk8w.ap-northeast-1.elasticbeanstalk.com/


# User Interface
![Screen Shot 2022-10-02 at 12 18 10 PM](https://user-images.githubusercontent.com/105154630/193457579-64e91cf7-22f4-4baf-9ec2-7b0806fe778a.png)


# Technology Used
1) Python
2) Pycharm
3) Jupyter Notebook
4) Sklearn
5) Flask
6) HTML
7) CSS
8) Pandas, Numpy 
9) Seaborn , Matplotlib
10) Cassandra Database
11) AWS Cloud Plateform
