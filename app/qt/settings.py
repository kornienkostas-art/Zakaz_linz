from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QSpinBox,
    QFileDialog,
    QMessageBox,
    QFormLayout,
    QApplication,
)

# Settings page allows changing UI-related options and app behavior.
# It relies on callbacks provided by the main window to read/write settings and apply changes live.


class SettingsPage(QWidget):
    def __init__(
        self,
        get_settings: Callable[[], dict],
        save_settings: Callable[[dict], None],
        apply_font: Callable[[str, int], None],
        set_tray_enabled: Callable[[bool], None],
        toggle_autostart: Callable[[bool], bool],
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._get_settings = get_settings
        self._save_settings = save_settings
        self._apply_font_cb = apply_font
        self._set_tray_enabled_cb = set_tray_enabled
        self._toggle_autostart_cb = toggle_autostart

        self._init_ui()
        self._load_to_controls()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Настройки")
        title.setStyleSheet("font-weight:600; font-size:16pt; color:#0F172A;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        # Font family
        self.font_family = QLineEdit()
        form.addRow("Шрифт (семейство)", self.font_family)

        # Base font size (pt)
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 24)
        form.addRow("Размер шрифта (pt)", self.font_size)

        # Export folder
        exp_layout = QHBoxLayout()
        self.export_folder = QLineEdit()
        self.export_folder.setReadOnly(True)
        btn_choose_export = QPushButton("Выбрать…")
        btn_choose_export.clicked.connect(self._choose_export_folder)
        exp_layout.addWidget(self.export_folder, 1)
        exp_layout.addWidget(btn_choose_export)
        form.addRow("Папка экспорта", exp_layout)

        # Tray and autostart
        self.tray_enabled = QCheckBox("Включить системный трей")
        self.minimize_to_tray = QCheckBox("Сворачивать в трей при закрытии")
        self.start_in_tray = QCheckBox("Запускать свернутым в трей")
        self.autostart_enabled = QCheckBox("Автозапуск при входе в Windows")

        form.addRow(self.tray_enabled)
        form.addRow(self.minimize_to_tray)
        form.addRow(self.start_in_tray)
        form.addRow(self.autostart_enabled)

        layout.addLayout(form)

        # Actions
        actions = QHBoxLayout()
        btn_apply = QPushButton("Применить")
        btn_apply.clicked.connect(self._apply)
        btn_save = QPushButton("Сохранить")
        btn_save.clicked.connect(self._save)
        actions.addWidget(btn_apply)
        actions.addWidget(btn_save)
        layout.addLayout(actions)
        layout.addStretch(1)

    def _load_to_controls(self):
        s = self._get_settings()
        self.font_family.setText(s.get("font_family", "Segoe UI"))
        self.font_size.setValue(int(s.get("font_size_base_pt", 12)))
        self.export_folder.setText(s.get("export_path", ""))

        self.tray_enabled.setChecked(bool(s.get("tray_enabled", True)))
        self.minimize_to_tray.setChecked(bool(s.get("minimize_to_tray", True)))
        self.start_in_tray.setChecked(bool(s.get("start_in_tray", False)))
        self.autostart_enabled.setChecked(bool(s.get("autostart_enabled", True)))

    def _choose_export_folder(self):
        start_dir = self.export_folder.text() or ""
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку экспорта", start_dir)
        if folder:
            self.export_folder.setText(folder)

    def _apply(self):
        # Apply font live
        ff = self.font_family.text().strip() or "Segoe UI"
        fs = int(self.font_size.value())
        try:
            self._apply_font_cb(ff, fs)
            # Also update application's default font immediately
            QApplication.instance().setFont(QFont(ff, pointSize=fs))
        except Exception:
            QMessageBox.warning(self, "Шрифт", "Не удалось применить шрифт/размер.")

        # Tray enabled live toggle
        tray_on = self.tray_enabled.isChecked()
        try:
            self._set_tray_enabled_cb(tray_on)
        except Exception:
            QMessageBox.warning(self, "Трей", "Не удалось применить настройку трея.")

        # Autostart toggle via registry
        auto_on = self.autostart_enabled.isChecked()
        ok = self._toggle_autostart_cb(auto_on)
        if not ok:
            QMessageBox.warning(self, "Автозапуск", "Не удалось применить автозапуск.")

        # Minimize/start-in-tray do not require live actions, they affect next interactions.

        # Update status
        QMessageBox.information(self, "Применение", "Настройки применены.")

    def _save(self):
        s = self._get_settings()
        s["font_family"] = self.font_family.text().strip() or "Segoe UI"
        s["font_size_base_pt"] = int(self.font_size.value())
        s["export_path"] = self.export_folder.text().strip() or s.get("export_path", "")

        s["tray_enabled"] = bool(self.tray_enabled.isChecked())
        s["minimize_to_tray"] = bool(self.minimize_to_tray.isChecked())
        s["start_in_tray"] = bool(self.start_in_tray.isChecked())
        s["autostart_enabled"] = bool(self.autostart_enabled.isChecked())

        try:
            self._save_settings(s)
            QMessageBox.information(self, "Сохранение", "Настройки сохранены.")
        except Exception:
            QMessageBox.warning(self, "Сохранение", "Не удалось сохранить настройки.")