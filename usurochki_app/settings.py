import os
import json
from typing import Dict, Any

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
)

DEFAULT_SETTINGS = {
    "theme": "dark",  # dark | light
    "export_dir": os.path.expanduser("~/Desktop"),
}


class SettingsManager:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
        self.path = os.path.join(self.base_dir, "settings.json")
        self.data: Dict[str, Any] = DEFAULT_SETTINGS.copy()
        self.load()

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.data.update(json.load(f))
            except Exception:
                # игнорируем ошибки чтения, используем дефолт
                pass

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("Не удалось сохранить настройки:", e)

    def get_theme(self) -> str:
        return self.data.get("theme", "dark")

    def set_theme(self, theme: str):
        self.data["theme"] = theme
        self.save()

    def get_export_dir(self) -> str:
        return self.data.get("export_dir", DEFAULT_SETTINGS["export_dir"])

    def set_export_dir(self, path: str):
        self.data["export_dir"] = path
        self.save()


class SettingsWindow(QWidget):
    def __init__(self, settings: SettingsManager, on_theme_changed):
        super().__init__()
        self.settings = settings
        self.on_theme_changed = on_theme_changed
        self.setWindowTitle("Настройки — УссурОЧки.рф")

        layout = QVBoxLayout(self)

        # Тема
        layout.addWidget(QLabel("Тема интерфейса"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        self.theme_combo.setCurrentText(self.settings.get_theme())
        layout.addWidget(self.theme_combo)

        # Экспорт
        export_layout = QHBoxLayout()
        export_layout.addWidget(QLabel("Папка экспорта файлов"))
        self.export_label = QLabel(self.settings.get_export_dir())
        btn_choose = QPushButton("Выбрать...")
        export_layout.addWidget(self.export_label)
        export_layout.addWidget(btn_choose)
        layout.addLayout(export_layout)

        # Резервное копирование БД
        btn_backup = QPushButton("Сделать резервную копию БД")
        layout.addWidget(btn_backup)

        # Сохранить
        btn_save = QPushButton("Сохранить настройки")
        layout.addWidget(btn_save)

        # Сигналы
        btn_choose.clicked.connect(self._choose_export_dir)
        btn_backup.clicked.connect(self._backup_db)
        btn_save.clicked.connect(self._save)

    def _choose_export_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Выберите папку для экспорта", self.settings.get_export_dir())
        if path:
            self.export_label.setText(path)

    def _backup_db(self):
        # копируем файл БД в выбранную папку экспорта
        src_db = os.path.join(self.settings.base_dir, "usurochki.sqlite")
        if not os.path.exists(src_db):
            QMessageBox.warning(self, "Ошибка", "Файл БД не найден.")
            return
        dst_dir = self.settings.get_export_dir()
        os.makedirs(dst_dir, exist_ok=True)
        dst_path = os.path.join(dst_dir, "usurochki_backup.sqlite")
        try:
            import shutil
            shutil.copy2(src_db, dst_path)
            QMessageBox.information(self, "Резервное копирование", f"Файл сохранён: {dst_path}")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось создать копию: {e}")

    def _save(self):
        theme = self.theme_combo.currentText()
        self.settings.set_theme(theme)
        export_dir = self.export_label.text()
        if export_dir and os.path.isdir(export_dir):
            self.settings.set_export_dir(export_dir)
        if self.on_theme_changed:
            self.on_theme_changed(theme)
        QMessageBox.information(self, "Настройки", "Настройки сохранены.")