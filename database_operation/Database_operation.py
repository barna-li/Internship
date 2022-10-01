from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
import os
from application_logging.logger import App_Logger
import pandas as pd


class DBOperation:
    """this class used for database connection """
    def __init__(self):
        self.file_location = f"{os.getcwd()}/database_operation"
        self.client_secret = "Ys_wawYqinGKDc2Rd6FYmmuhQcomcZl4begGMhs0RuT3_Ack8LlHaC1,rfjtdYLiivUx.t7iOdY3w0P3Xm,owtQZ5UXbSD9mKNoH7GwR+vMXNT26_AiRJWG2wgXG4C0o"
        self.client_id = 'YjEYDTlddZlaxJICMmvNqqHQ'
        self.bundle = 'secure-connect-major-project.zip'
        self.keyspace = "puni"
        self.data_file = "../venv/insurance.csv"
        self.log_file = open("application_logging/logging.txt", 'a+')
        self.logging = App_Logger()

    def connect_db(self):
        """this method used to connect the DB"""
        try:
            cloud_config = {
                'secure_connect_bundle': f'{os.getcwd()}\{self.bundle}'
            }
            auth_provider = PlainTextAuthProvider(self.client_id, self.client_secret)
            cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
            self.logging.log(self.log_file," connection is established")
            return cluster.connect()
        except Exception as e:
            self.logging.log(self.log_file, f" connection is failed due to {e}")
            raise e

    def create_table(self, tablename):
        """this method used to create a table in database"""
        try:
            session = self.connect_db()
            query = f"create table if not exists {self.keyspace}.{tablename} (id int primary key, age int, sex text, bmi float, children int, smoker text,region text, expenses float)"
            session.execute(query)
            self.logging.log(self.log_file, f"{tablename} is created successfully")
            return tablename
        except Exception as e:
            self.logging.log(self.log_file, f"table creation is failed error occured due to {e}")
            raise e

    def insert_data(self, tablename):
        """this method is used to insert the data to the DB"""
        try:
            session = self.connect_db()
            df = pd.read_csv(f'{os.getcwd()}\insurance.csv')
            index = [i for i in range(1, len(df) + 1)]
            df.insert(0, "id", index)
            self.logging.log(self.log_file, "insertion has begun")
            for i in range(1, len(df)):
                data = tuple(df.iloc[i])
                print(data)
                q = f"INSERT INTO {self.keyspace}.{tablename}(id,age,sex,bmi,children,smoker,region,expenses) VALUES{data}"
                session.execute(q)
            self.logging.log(self.log_file, "inserting is done successfully")
        except Exception as e:
            self.logging.log(self.log_file, f"insertion operation is failed due to {e}")
            raise e

    def retrieve_data(self, tablename):
        """This method is used to retrieve the data from the database """
        try:
            session = self.connect_db()
            self.logging.log(self.log_file, "fetching operation has begun")
            q = f"select * from {self.keyspace}.{tablename}"
            data = session.execute(q)
            lst = []
            for i in data.all():
                lst.append(i)
            df = pd.DataFrame(lst)
            df.to_csv(f"{os.getcwd()}\\dataset.csv", index=False)
            self.logging.log(self.log_file, "fetching operation has been completed successfully")
            return df
        except Exception as e:
            self.logging.log(self.log_file, f"fetching operation is failed due to {e}")
            raise e

