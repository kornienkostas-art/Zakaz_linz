import os

from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QGroupBox,
    QLineEdit,
)

from ..db import Database
from ..utils import ThemeManager, ensure_app_data_dir, backup_database


class SettingsPage(QWidget):
    def __init__(self, db: Database, settings: QSettings, parent=None):
        super().__init__(parent)
        self.db = db
        self.settings = settings

        lay = QVBoxLayout(self)

        gb_theme = QGroupBox("Тема интерфейса")
        l1 = QHBoxLayout(gb_theme)
        self.cmb_theme = QComboBox()
        self.cmb_theme.addItems(["light", "dark"])
        cur = self.settings.value("theme", "dark")
        idx = self.cmb_theme.findText(cur)
        if idx >= 0:
            self.cmb_theme.setCurrentIndex(idx)
        btn_apply = QPushButton("Применить")
        btn_apply.clicked.connect(self.apply_theme)
        l1.addWidget(QLabel("Тема:"))
        l1.addWidget(self.cmb_theme)
        l1.addStretch(1)
        l1.addWidget(btn_apply)
        lay.addWidget(gb_theme)

        gb_export = QGroupBox("Экспорт")
        l2 = QHBoxLayout(gb_export)
        self.ed_export = QLineEdit(self.settings.value("export_dir", "exports"))
        btn_browse = QPushButton("Выбрать…")
        btn_browse.clicked.connect(self.choose_export_dir)
        l2.addWidget(QLabel("Папка для экспорта:"))
        l2.addWidget(self.ed_export, 1)
        l2.addWidget(btn_browse)
        lay.addWidget(gb_export)

        gb_backup = QGroupBox("Резервное копирование БД")
        l3 = QHBoxLayout(gb_backup)
        btn_backup = QPushButton("Создать резервную копию")
        btn_backup.clicked.connect(self.do_backup)
        l3.addWidget(btn_backup)
        lay.addWidget(gb_backup)

        lay.addStretch(1)

    def apply_theme(self):
        theme = self.cmb_theme.currentText()
        self.settings.setValue("theme", theme)
        from PyQt6.QtWidgets import QApplication
        ThemeManager.apply(QApplication.instance(), theme)

    def choose_export_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Выберите папку для экспорта", self.ed_export.text() or "exports")
        if not path:
            return
        self.ed_export.setText(path)
        self.settings.setValue("export_dir", path)

    def do_backup(self):
        dest = QFileDialog.getExistingDirectory(self, "Папка для резервной копии", "backups")
        if not dest:
            return
        db_path = self.db.path
        path = backup_database(db_path, dest)
        QMessageBox.information(self, "Резервная копия", f"Файл сохранён:\\n{path}")