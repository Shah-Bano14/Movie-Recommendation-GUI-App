import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5.uic import loadUi
from movie_recommendation import Ui_MainWindow
import urllib3
import mysql.connector
from collections.abc import MutableMapping
from bcrypt import hashpw, gensalt, checkpw

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="movierecommendation"
)

mycursor = db.cursor()

# Create a table for user authentication if not exists
create_user_table_query = """
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL
);
"""
mycursor.execute(create_user_table_query)

db.commit()

class Login(QDialog):
    def __init__(self):
        super(Login,self).__init__()
        loadUi("ui\\login.ui",self)
        self.loginbutton.clicked.connect(self.loginfunction)
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.createaccbutton.clicked.connect(self.gotocreate)
        self.txt_in.setVisible(False)

    def loginfunction(self):
        email=self.email.text()
        password=self.password.text()
        try:
            # Authenticate the user against the MySQL database
            mycursor.execute("SELECT * FROM users WHERE email=%s", (email,))
            user_data = mycursor.fetchone()
            if user_data:
                if checkpw(password.encode('utf-8'), user_data[2].encode('utf-8')):
                    self.Win = QtWidgets.QMainWindow()
                    self.ui = Ui_MainWindow()
                    self.ui.setupUi(self.Win)
                    self.Win.show()
                else:
                    # Passwords don't match, login failed
                    self.txt_in.setVisible(True)
                    print("Invalid Email or Password")
            else:
                # User with the given email not found
                self.txt_in.setVisible(True)
                print("Invalid Email or Password")
        except Exception as e:
            print("User does not exist")


    def gotocreate(self):
        createacc=CreateAcc()
        widget.addWidget(createacc)
        widget.setCurrentIndex(widget.currentIndex()+1)

class CreateAcc(QDialog):
    def __init__(self):
        super(CreateAcc,self).__init__()
        loadUi("ui\\createacc.ui",self)
        self.signupbutton.clicked.connect(self.createaccfunction)
        self.btn_back.clicked.connect(self.back)
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.confirmpass.setEchoMode(QtWidgets.QLineEdit.Password)
        self.invalid.setVisible(False)

    def createaccfunction(self):
        email = self.email.text()
        if self.password.text()==self.confirmpass.text():
            password=self.password.text()
            hashed_password = hashpw(password.encode('utf-8'), gensalt())
            try:
                # Insert a new user into the MySQL database
                mycursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", 
                (email, hashed_password))
                db.commit()
                self.back()
            except mysql.connector.Error as err:
                self.invalid.setVisible(True)
                print(f"Error: {err}")
            except Exception as e:
                self.invalid.setVisible(True)
                print("invalid")
        else:
            self.invalid.setVisible(True)
            print("Passwords do not match")


    def back(self):
        login = Login()
        widget.addWidget(login)
        widget.setCurrentIndex(widget.currentIndex() + 1)



if __name__ == '__main__':

    app=QApplication(sys.argv)
    mainwindow=Login()
    widget=QtWidgets.QStackedWidget()
    widget.addWidget(mainwindow)
    widget.setFixedWidth(480)
    widget.setFixedHeight(620)
    widget.show()
    app.exec_()
