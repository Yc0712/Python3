import sys

from PySide2 import QtCore
from PySide2 import QtWidgets
from PySide2 import QtGui



class ValueLadderSection(QtWidgets.QWidget):

    def __init__(self, increment_size, parent=None):
        super().__init__(parent)

        self.increment_size = increment_size

        self.setAutoFillBackground(True)
        self.setMinimumHeight(40)

        self.increment_lable = QtWidgets.QLabel("{0}".format(self.increment_size))
        self.increment_lable.setAlignment(QtCore.Qt.AlignCenter)

        self.value_lable = QtWidgets.QLabel("0.0")
        self.value_lable.setAlignment(QtCore.Qt.AlignCenter)
        self.set_active(False)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.increment_lable)
        main_layout.addWidget(self.value_lable)

    def set_active(self, active):
        self.active = active

        pal = self.palette()
        if self.active:
            pal.setColor(QtGui.QPalette.Background, QtCore.Qt.yellow)
        else:
            pal.setColor(QtGui.QPalette.Background, QtCore.Qt.white)

        self.setPalette(pal)

        self.value_lable.setVisible(self.active)

    def set_value(self, value):
        self.value_lable.setText("{0}".format(value))


class ValueLadder(QtWidgets.QWidget):


    PIXELS_PER_INCREMENT = 20

    value_changed = QtCore.Signal(float)
    def __init__(self, parent=None):
        super().__init__(parent)

        self.active_section = None

        self.initial_value = 0
        self.current_value = 0

        self.x_start = sys.maxsize
        self.multiplier = 0


        self.setMinimumSize(60, 140)
        self.setWindowFlags(QtCore.Qt.Popup)

        pal = self.palette()
        pal.setColor(QtGui.QPalette.Background, QtCore.Qt.black)
        self.setPalette(pal)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(1)

        for increment in [100, 10, 1, 0.1, 0.01, 0.001]:
            main_layout.addWidget(ValueLadderSection(increment))

    def set_position(self, pos):
        self.move(pos.x() - (0.5 * self.width()), pos.y() - (0.5 * self.height()))

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.MiddleButton:
            self.close()

    def set_initial_value(self, value):
        self.initial_value = value
    def mouseMoveEvent(self, event):
        pos = event.pos()

        widget_under_mouse = self.childAt(pos)
        if widget_under_mouse:
            self.activate_section(widget_under_mouse)
        else:
            if self.x_start == sys.maxsize:
                self.x_start = pos.x()

            temp_multiplier = int((pos.x() - self.x_start) / ValueLadder.PIXELS_PER_INCREMENT)
            if self.multiplier != temp_multiplier:
                self.multiplier = temp_multiplier

                self.current_value = round(self.initial_value + (self.multiplier * self.active_section.increment_size), 4)
                self.active_section.set_value(self.current_value)

                self.value_changed.emit(self.current_value)
    def activate_section(self, widget_under_mouse):
        if not self.is_value_ladder_section(widget_under_mouse):
            while widget_under_mouse:
                widget_under_mouse = widget_under_mouse.parentWidget()
                if self.is_value_ladder_section(widget_under_mouse):
                    break

        if self.active_section != widget_under_mouse:
            self.current_value = self.initial_value
            self.x_start = sys.maxsize

            if self.active_section:
                self.active_section.set_active(False)

            self.active_section = widget_under_mouse

            if self.active_section:
                self.active_section.set_active(True)
                self.active_section.set_value(self.current_value)


    def is_value_ladder_section(self, widget):
        if type(widget) == ValueLadderSection:
            return True
        return False



class ladderSpinBox(QtWidgets.QDoubleSpinBox):


    def __init__(self):
        super().__init__(parent=None)

        self.value_ladder = None

        self.setButtonSymbols(QtWidgets.QDoubleSpinBox.NoButtons)
        self.setMinimum(-9999.9999)
        self.setMaximum(9999.9999)
        self.setMinimumWidth(200)
        self.setDecimals(4)

        self.lineEdit().installEventFilter(self)

    def eventFilter(self, watched, event):
        if watched == self.lineEdit():
            if event.type() == QtCore.QEvent.MouseButtonPress and event.button() == QtCore.Qt.MiddleButton:
                self.show_ladder(self.mapToGlobal(event.pos()))
                return True

        return super().eventFilter(watched, event)

    def show_ladder(self, pos):
        if not self.value_ladder:
            self.value_ladder = ValueLadder()
            self.value_ladder.value_changed.connect(self.setValue)

        self.value_ladder.set_initial_value(self.value())
        self.value_ladder.show()

        self.value_ladder.set_position(pos)

class StandaloneWindow(QtWidgets.QWidget):

    def __init__(self):
        super().__init__(parent=None)

        self.setWindowTitle("Value ladder")
        self.setMinimumWidth(250)

        self.create_widgets()
        self.create_layout()

    def create_widgets(self):
        self.translate_sb = ladderSpinBox()
        self.rotate_sb = ladderSpinBox()
        self.scale_sb = ladderSpinBox()

    def create_layout(self):
        main_layout = QtWidgets.QFormLayout(self)
        main_layout.addRow("Translate:", self.translate_sb)
        main_layout.addRow("Rotate:", self.rotate_sb)
        main_layout.addRow("Scale:", self.scale_sb)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    window = StandaloneWindow()
    window.show()

    app.exec_()
