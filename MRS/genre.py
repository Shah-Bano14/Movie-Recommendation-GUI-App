import os
import sys
from os.path import dirname, realpath, join
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QTableWidget, QTableWidgetItem
from PyQt5.uic import loadUiType
import pandas as pd


From_Main, _ = loadUiType(join(dirname(__file__), "./ui/Main.ui"))

class MainWindow3(QWidget, From_Main):
    def __init__(self):
        super(MainWindow3, self).__init__()
        QWidget.__init__(self)
        self.setupUi(self)
        self.txt_display.setText("Genre based recommendation  ")
        self.BtnDescribe.clicked.connect(self.dataHead)
        self.all_data = pd.read_csv('./csvfiles/resultgb.csv', usecols=['title', 'year', 'popularity', 'overview', 'wr'])


    def dataHead(self):
        numColomn = self.spinBox.value()
        if numColomn == 0:
            NumRows = len(self.all_data.index)
        else:
            NumRows = numColomn
        self.tableWidget.setColumnCount(len(self.all_data.columns))
        self.tableWidget.setRowCount(NumRows)
        self.tableWidget.setHorizontalHeaderLabels(self.all_data.columns)

        for i in range(NumRows):
            for j in range(len(self.all_data.columns)):
                self.tableWidget.setItem(i, j, QTableWidgetItem(str(self.all_data.iat[i, j])))

        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.resizeRowsToContents()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    sheet = MainWindow3()
    sheet.show()
    sys.exit(app.exec_())