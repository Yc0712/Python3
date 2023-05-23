import os
import subprocess
import sys
from PySide2 import QtGui
from PySide2 import QtWidgets
from PySide2 import QtCore


class TranscodeWindow(QtWidgets.QWidget):
    FFMPEG_PATH = "P:/ffmpeg/bin/ffmpeg.exe"

    QUALITY_OPTIONS = [
        ["very high", "18"],  # combobox item label, crf value
        ["high", "20"],
        ["medium", "23"],
        ["low", "26"]
    ]
    QUALITY_DEFAULT = "medium"

    PRESETS = [
        ["very slow", "veryslow"],  # combobox item label, preset value
        ["slower", "slower"],
        ["slow", "slow"],
        ["medium", "medium"],
        ["fast", "fast"],
        ["faster", "faster"],
        ["very fast", "veryfast"],
        ["ultra fast", "ultrafast"]
    ]
    PRESET_DEFAULT = "medium"

    def __init__(self):
        super(TranscodeWindow, self).__init__(parent=None)

        self.setWindowTitle("FFmpeg Transcoder")
        self.setMinimumSize(400, 300)

        self.create_widgets()
        self.create_layout()
        self.create_connections()

    def create_widgets(self):
        self.input_path_le = QtWidgets.QLineEdit()
        self.input_path_btn = QtWidgets.QPushButton("...")
        self.input_path_btn.setFixedWidth(30)

        self.output_path_le = QtWidgets.QLineEdit()
        self.output_path_btn = QtWidgets.QPushButton("...")
        self.output_path_btn.setFixedWidth(30)

        self.video_codec_combo = QtWidgets.QComboBox()
        self.video_codec_combo.addItem("h264", "libx264")

        self.quality_combo = QtWidgets.QComboBox()
        for quality_option in self.QUALITY_OPTIONS:
            self.quality_combo.addItem(quality_option[0], quality_option[1])
        self.quality_combo.setCurrentText(self.QUALITY_DEFAULT)

        self.preset_combo = QtWidgets.QComboBox()
        for preset in self.PRESETS:
            self.preset_combo.addItem(preset[0], preset[1])
        self.preset_combo.setCurrentText(self.PRESET_DEFAULT)

        self.audio_codec_combo = QtWidgets.QComboBox()
        self.audio_codec_combo.addItem("aac", "aac")

        self.transcode_btn = QtWidgets.QPushButton("Transcode")
        self.cancel_btn = QtWidgets.QPushButton("Cancel")

    def create_layout(self):

        input_grp = QtWidgets.QGroupBox("Input Path")
        input_grp_layout = QtWidgets.QHBoxLayout()
        input_grp_layout.addWidget(self.input_path_le)
        input_grp_layout.addWidget(self.input_path_btn)
        input_grp.setLayout(input_grp_layout)

        output_grp = QtWidgets.QGroupBox("Output Path")
        output_grp_layout = QtWidgets.QHBoxLayout()
        output_grp_layout.addWidget(self.output_path_le)
        output_grp_layout.addWidget(self.output_path_btn)
        output_grp.setLayout(output_grp_layout)

        video_options_grp = QtWidgets.QGroupBox("Video Options")
        video_options_grp_layout = QtWidgets.QFormLayout()
        video_options_grp.setLayout(video_options_grp_layout)

        video_codec_layout = QtWidgets.QHBoxLayout()
        video_codec_layout.addWidget(self.video_codec_combo)
        video_codec_layout.addStretch()
        video_options_grp_layout.addRow("Video Codec:", video_codec_layout)

        quality_layout = QtWidgets.QHBoxLayout()
        quality_layout.addWidget(self.quality_combo)
        quality_layout.addStretch()
        video_options_grp_layout.addRow("Quality:", quality_layout)

        preset_layout = QtWidgets.QHBoxLayout()
        preset_layout.addWidget(self.preset_combo)
        preset_layout.addStretch()
        video_options_grp_layout.addRow("Preset:", preset_layout)

        audio_options_grp = QtWidgets.QGroupBox("Audio Options")
        audio_options_grp_layout = QtWidgets.QFormLayout()
        audio_options_grp.setLayout(audio_options_grp_layout)

        audio_codec_layout = QtWidgets.QHBoxLayout()
        audio_codec_layout.addWidget(self.audio_codec_combo)
        audio_codec_layout.addStretch()
        audio_options_grp_layout.addRow("Audio Codec:", audio_codec_layout)

        options_layout = QtWidgets.QHBoxLayout()
        options_layout.addWidget(video_options_grp)
        options_layout.addWidget(audio_options_grp)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.transcode_btn)
        button_layout.addWidget(self.cancel_btn)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(input_grp)
        main_layout.addWidget(output_grp)
        main_layout.addLayout(options_layout)
        main_layout.addStretch()
        main_layout.addLayout(button_layout)

    def create_connections(self):
        self.input_path_btn.clicked.connect(self.set_input_path)
        self.output_path_btn.clicked.connect(self.set_output_path)

        self.transcode_btn.clicked.connect(self.transcode)
        self.cancel_btn.clicked.connect(self.close)

    def set_input_path(self):
        filters = "*;; *.mp4;; *.mov;;"
        selected_filter = "*;; *.mp4;; *.mov;"

        input_path, selected_filter = QtWidgets.QFileDialog.getOpenFileName(self, "Select an Input File", "", filters,
                                                                            selected_filter)
        if input_path:
            self.input_path_le.setText(input_path)

    def set_output_path(self):
        filters = "*.mp4;; *.mov"
        selected_filter = "*.mp4;; *.mov"

        output_path, selected_filter = QtWidgets.QFileDialog.getSaveFileName(self, "Save File As", "", filters,
                                                                             selected_filter)
        if output_path:
            self.output_path_le.setText(output_path)

    def transcode(self):

        input_path = self.input_path_le.text()
        if not input_path:
            QtWidgets.QMessageBox.critical(self, "Transcode Error", "Input path not set")
            return
        if not os.path.exists(input_path):
            QtWidgets.QMessageBox.critical(self, "Transcode Error", "Input path does not exist")
            return

        output_path = self.output_path_le.text()
        if not output_path:
            QtWidgets.QMessageBox.critical(self, "Transcode Error", "Output path not set")
            return

        video_codec = self.video_codec_combo.currentData()
        crf = self.quality_combo.currentData()
        preset = self.preset_combo.currentData()

        audio_codec = self.audio_codec_combo.currentData()

        args = [self.FFMPEG_PATH]  # executable path
        args.extend(["-hide_banner", "-y"])  # global options
        args.extend(["-i", input_path])  # input path
        args.extend(["-c:v", video_codec, "-crf", crf, "-preset", preset])  # video output options
        args.extend(["-c:a", audio_codec])  # audio output options
        args.append(output_path)  # output path

        subprocess.call(args)

        QtWidgets.QMessageBox.information(self, "Transcode Complete", "File transcode operation complete.")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    # dark_palette = QtGui.QPalette()
    # # dark_palette.setColor(QtGui.QPalette.Window, QtGui.QColor(45, 45, 45))
    # dark_palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(208, 208, 208))
    # dark_palette.setColor(QtGui.QPalette.Base, QtGui.QColor(25, 25, 25))
    # dark_palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(208, 208, 208))
    # dark_palette.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor(208, 208, 208))
    # dark_palette.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor(208, 208, 208))
    # dark_palette.setColor(QtGui.QPalette.Text, QtGui.QColor(208, 208, 208))
    # dark_palette.setColor(QtGui.QPalette.Button, QtGui.QColor(45, 45, 48))
    # dark_palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(208, 208, 208))
    # dark_palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)
    # dark_palette.setColor(QtGui.QPalette.Link, QtGui.QColor(42, 130, 218))
    # dark_palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(42, 130, 218))
    # dark_palette.setColor(QtGui.QPalette.Highlight, QtCore.Qt.black)
    # app.setPalette(dark_palette)

    window = TranscodeWindow()
    window.show()

    app.exec_()
