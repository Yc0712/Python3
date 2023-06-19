import sys

from PySide2 import QtGui
from PySide2 import QtWidgets


class standalongwindow(QtWidgets.QWidget):

    def __init__(self):
        super().__init__(parent=None)

        self.setWindowTitle("QlineEdit Example")
        self.setMinimumWidth(400)

        self.lineedit = QtWidgets.QLineEdit()

        self.le_btn_action = self.lineedit.addAction(QtGui.QIcon(
            r"C:\Users\yuchao\Desktop\Qt for Python Tips and Tricks\qt_for_python_tips_and_tricks_project_files\09-qt_for_python_tips_and_tricks-qlineedit_buttons\clear.png"),
            QtWidgets.QLineEdit.TrailingPosition)
        self.le_btn_action.triggered.connect(self.clean_line_edit)

        main_layout = QtWidgets.QFormLayout(self)
        main_layout.addRow("Filename:", self.lineedit)

    def clean_line_edit(self):
        self.lineedit.setText("")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = standalongwindow()
    window.show()
    app.exec_()
