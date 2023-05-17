import sys
from PySide2 import QtCore
from PySide2 import QtWidgets


class StandaloneWindow(QtWidgets.QMainWindow):

    FILE_FILTERS = "Text Files (*.txt);;All Files (*.*)"
    selected_filter = "All Files (*.*)"


    def __init__(self):
        super(StandaloneWindow, self).__init__(parent=None)

        self.setWindowTitle("QFileSystemWatcher Example")
        self.setMinimumSize(360, 300)

        self.file_info = QtCore.QFileInfo()

        self.file_system_watcher = QtCore.QFileSystemWatcher()

        self.create_menu()
        self.create_widgets()
        self.create_layout()
        self.create_connections()
        
    def create_menu(self):
        self.file_open_action = QtWidgets.QAction("Open...")

        file_menu = QtWidgets.QMenu("File")
        file_menu.addAction(self.file_open_action)
        
        menu_bar = QtWidgets.QMenuBar()
        menu_bar.addMenu(file_menu)

        self.setMenuBar(menu_bar)

    def create_widgets(self):
        self.plain_text_edit = QtWidgets.QPlainTextEdit()
        self.plain_text_edit.setReadOnly(True)

        self.file_count_label = QtWidgets.QLabel()
        self.update_file_count()

    def create_layout(self):
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QtWidgets.QVBoxLayout(central_widget)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.addWidget(self.plain_text_edit)
        main_layout.addWidget(self.file_count_label)

    def create_connections(self):
        self.file_open_action.triggered.connect(self.open_file)

        self.file_system_watcher.fileChanged.connect(self.update_file)
        self.file_system_watcher.directoryChanged.connect(self.update_file_count)

    def open_file(self):
        file_path, self.selected_filter = QtWidgets.QFileDialog.getOpenFileName(self, "Select a File", "", self.FILE_FILTERS, self.selected_filter)
        if file_path:
            self.file_info.setFile(file_path)
            
        self.update_file()
        self.update_file_count()
        self.update_watched_paths()

    def update_file(self):
        text = ""

        if self.file_info.exists():
            file_path = self.file_info.absoluteFilePath()

            f = QtCore.QFile(file_path)
            if f.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text):
                text_stream = QtCore.QTextStream(f)
                text = text_stream.readAll()
            else:
                text = "<< ERROR: Failed to open file >>"

        self.plain_text_edit.setPlainText(text)

    def update_file_count(self):
        if self.file_info.exists():
            directory = self.file_info.dir()
            directory.setFilter(QtCore.QDir.Files | QtCore.QDir.NoSymLinks)
            file_count = directory.count()
        else:
            file_count = 0

        self.file_count_label.setText("Files in Folder: {0}".format(file_count))

    def update_watched_paths(self):
        watched_files = self.file_system_watcher.files()
        if len(watched_files) > 0:
            self.file_system_watcher.removePaths(watched_files)

        watched_directories = self.file_system_watcher.directories()
        if len(watched_directories) > 0:
            self.file_system_watcher.removePaths(watched_directories)

        if self.file_info.exists():
            self.file_system_watcher.addPath(self.file_info.absoluteFilePath())
            self.file_system_watcher.addPath(self.file_info.dir().absolutePath())


if __name__ == "__main__":
    # Create the main Qt application
    app = QtWidgets.QApplication(sys.argv)

    window = StandaloneWindow()
    window.show()

    # Enter Qt main loop (start event handling)
    app.exec_()



