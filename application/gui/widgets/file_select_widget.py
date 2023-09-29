import os

from PyQt5.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QFileDialog,
    QPushButton,
    QLineEdit,
    QTreeView,
)

from application.common.constants import FileModes
from client import Client


class FileSelectWidget(QWidget):
    def __init__(self, client: Client, file_mode: FileModes, parent: QWidget) -> None:
        super().__init__(parent)

        self._parent = parent
        self._client = client
        self._file_mode: FileModes = file_mode
        self._layout = QHBoxLayout()

        self._selected_path: str = ""
        self._path_line_edit = QLineEdit()
        self._browse_button = QPushButton("Browse")

        dialog = QFileDialog()

        if self._file_mode == FileModes.DIRECTORY:
            dialog.setFileMode(QFileDialog.Directory)
            dialog.setOption(QFileDialog.ShowDirsOnly, True)
        elif self._file_mode == FileModes.FILE:
            dialog.setFileMode(QFileDialog.AnyFile)
            dialog.setOption(QFileDialog.ShowDirsOnly, False)

        self._file_select_dialog = dialog

        self._browse_button.clicked.connect(self.handle_button)

        selector_layout = QHBoxLayout()
        selector_layout.addWidget(self._path_line_edit)
        selector_layout.addWidget(self._browse_button)

        self._layout.addLayout(selector_layout)

        self.setLayout(self._layout)

    def get_line_edit(self) -> QLineEdit:
        return self._path_line_edit

    def handle_button(self) -> None:
        if self._file_mode == FileModes.DIRECTORY:
            path = self._file_select_dialog.getExistingDirectory(
                self, "Select Directory"
            )
        elif self._file_mode == FileModes.FILE:
            path, _ = self._file_select_dialog.getOpenFileName(
                self, "Select Path/File", ""
            )

        if path:
            self._path_line_edit.setText(path)