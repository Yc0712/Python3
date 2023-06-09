import maya.cmds as cmds
import maya.mel as mel

from PySide2 import QtWidgets
from PySide2 import QtCore
from shiboken2 import wrapInstance

import maya.OpenMayaUI as omui
import maya.api.OpenMaya as om

import traceback


class MM_RetimingUtils(object):

    @classmethod
    def retime_keys(cls, retime_value, incremental, move_to_next):
        range_start_time, range_end_time = cls.get_selected_range()
        start_keyframe_time = cls.get_start_keyframe_time(range_start_time)
        last_keyframe_time = cls.get_last_keyframe_time()
        current_time = start_keyframe_time

        new_keyframe_times = [start_keyframe_time]
        current_keyframe_values = [start_keyframe_time]

        while current_time != last_keyframe_time:
            next_keyframe_time = cls.find_keyframe("next", current_time)

            if incremental:
                time_diff = next_keyframe_time - current_time
                if current_time < range_end_time:
                    time_diff += retime_value
                    if time_diff < 1:
                        time_diff = 1
            else:
                if current_time < range_end_time:
                    time_diff = retime_value
                else:
                    time_diff = next_keyframe_time - current_time

            new_keyframe_times.append(new_keyframe_times[-1] + time_diff)
            current_time = next_keyframe_time

            current_keyframe_values.append(current_time)

        if len(new_keyframe_times) > 1:
            cls.retime_keys_recursive(start_keyframe_time, 0, new_keyframe_times)

        print(current_keyframe_values)
        print(new_keyframe_times)

        first_keyframe_time = cls.find_keyframe("first")
        if move_to_next and range_start_time >= first_keyframe_time:
            next_keyframe_time = cls.find_keyframe("next", start_keyframe_time)
            cls.set_current_time(next_keyframe_time)
        elif range_end_time > first_keyframe_time:
            cls.set_current_time(start_keyframe_time)
        else:
            cls.set_current_time(range_start_time)

    @classmethod
    def retime_keys_recursive(cls, current_time, index, new_keyframe_times):
        if index >= len(new_keyframe_times):
            return

        updated_keyframe_time = new_keyframe_times[index]
        next_keyframe_time = cls.find_keyframe("next", current_time)

        if updated_keyframe_time < next_keyframe_time:
            cls.change_keyframe_time(current_time, updated_keyframe_time)
            cls.retime_keys_recursive(next_keyframe_time, index + 1, new_keyframe_times)
        else:
            cls.retime_keys_recursive(next_keyframe_time, index + 1, new_keyframe_times)
            cls.change_keyframe_time(current_time, updated_keyframe_time)

    @classmethod
    def set_current_time(cls, time):
        cmds.currentTime(time)

    @classmethod
    def get_selected_range(cls):
        playback_slider = mel.eval("$tempVar = $gPlayBackSlider")
        selected_range = cmds.timeControl(playback_slider, q=True, rangeArray=True)

        return selected_range

    @classmethod
    def find_keyframe(cls, which, time=None):
        kwargs = {"which": which}
        if which in ["next", "previous"]:
            kwargs["time"] = (time, time)

        return cmds.findKeyframe(**kwargs)

    @classmethod
    def change_keyframe_time(cls, current_time, new_time):
        cmds.keyframe(e=True, time=(current_time, current_time), timeChange=new_time)

    @classmethod
    def get_start_keyframe_time(cls, range_start_time):
        start_times = cmds.keyframe(q=True, time=(range_start_time, range_start_time))
        if start_times:
            return start_times[0]

        start_time = cls.find_keyframe("previous", range_start_time)
        return start_time

    @classmethod
    def get_last_keyframe_time(cls):
        return cls.find_keyframe("last")


class MM_RetimingUi(QtWidgets.QWidget):
    WINDOW_TITLE = "Retiming Tool"

    RETIMING_PROPERTY_NAME = "retiming_data"

    @classmethod
    def maya_main_window(cls):

        maya_window_ptr = omui.MQtUtil.mainWindow()
        return wrapInstance(int(maya_window_ptr), QtWidgets.QWidget)

    def __init__(self, parent=None):
        super().__init__(parent=self.maya_main_window())

        self.setWindowTitle(self.WINDOW_TITLE)
        self.setWindowFlag(QtCore.Qt.Window.Dialog)

        self.create_widgets()
        self.create_layout()
        self.create_connections()

    def create_widgets(self):
        self.absolute_buttons = []
        for i in range(1, 7):
            btn = QtWidgets.QPushButton("{0}f".format(i))
            btn.setProperty(self.RETIMING_PROPERTY_NAME, [i, False])
            self.absolute_buttons.append(btn)

        self.relative_buttons = []
        for i in [-3, -2, -1, 1, 2, 3]:
            btn = QtWidgets.QPushButton("{0}f".format(i))
            btn.setFixedWidth(100)
            btn.setProperty(self.RETIMING_PROPERTY_NAME, [i, True])
            self.relative_buttons.append(btn)

        self.move_to_next_cb = QtWidgets.QCheckBox("Move to Next Frame")

    def create_layout(self):
        abs_layout = QtWidgets.QHBoxLayout()
        abs_layout.setSpacing(2)
        for btn in self.absolute_buttons:
            abs_layout.addWidget(btn)

        re_layout = QtWidgets.QHBoxLayout()
        re_layout.setSpacing(2)
        for btn in self.relative_buttons:
            re_layout.addWidget(btn)
            if re_layout.count() == 3:
                re_layout.addStretch()

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)
        main_layout.addLayout(abs_layout)
        main_layout.addLayout(re_layout)
        main_layout.addWidget(self.move_to_next_cb)
        main_layout.addStretch()

    def create_connections(self):
        for btn in self.absolute_buttons:
            btn.clicked.connect(self.retime)

        for btn in self.relative_buttons:
            btn.clicked.connect(self.retime)

    def retime(self):
        btn = self.sender()
        if btn:
            retime_data = btn.property(self.RETIMING_PROPERTY_NAME)
            move_to_next = self.move_to_next_cb.isChecked()

            cmds.undoInfo(openChunk=True)
            try:
                MM_RetimingUtils.retime_keys(retime_data[0], retime_data[1], move_to_next)
            except:
                traceback.print_exc()
                om.MGlobal.displayError("retime erro, please see scrip editor")
            cmds.undoInfo(closeChunk=True)


if __name__ == "__main__":

    try:
        Mretime.close()
        Mretime.deleteLater()
    except:
        pass
    Mretime = MM_RetimingUi()
    Mretime.show()
