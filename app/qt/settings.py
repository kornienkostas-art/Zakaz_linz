from typing import Callable, Optional, List

from PySide6.QtCore import Qt, QTime
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
    QGroupBox,
    QTimeEdit,
    QComboBox,
    QSizePolicy,
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

        # Days of week checkboxes for notifications
        self._day_checks: List[QCheckBox] = []

        self._init_ui()
        self._load_to_controls()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        title = QLabel("Настройки")
        title.setStyleSheet("font-weight:600; font-size:16pt; color:#0F172A;")
        layout.addWidget(title)

        # --- UI/Behavior form ---
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight)
        form.setFormAlignment(Qt.AlignTop)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        # Font family
        self.font_family = QLineEdit()
        self.font_family.setPlaceholderText("Segoe UI")
        self.font_family.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        form.addRow("Шрифт (семейство)", self.font_family)

        # Base font size (pt)
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 24)
        self.font_size.setFixedWidth(100)
        form.addRow("Размер шрифта (pt)", self.font_size)

        # Export folder
        exp_layout = QHBoxLayout()
        exp_layout.setSpacing(8)
        self.export_folder = QLineEdit()
        self.export_folder.setReadOnly(True)
        self.export_folder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
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

        # --- Notifications group (Meridian + MKL) ---
        notif_group = QGroupBox("Уведомления")
        notif_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        notif_layout = QVBoxLayout(notif_group)
        notif_layout.setSpacing(12)
        notif_layout.setContentsMargins(12, 12, 12, 12)

        # Meridian notifications
        mer_box = QGroupBox("Меридиан")
        mer_form = QFormLayout(mer_box)
        mer_form.setSpacing(8)
        mer_form.setLabelAlignment(Qt.AlignRight)

        self.notify_enabled = QCheckBox("Включить уведомления «Меридиан»")
        mer_form.addRow(self.notify_enabled)

        days_row = QHBoxLayout()
        day_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        self._day_checks = [QCheckBox(name) for name in day_names]
        for cb in self._day_checks:
            days_row.addWidget(cb)
        mer_form.addRow(QLabel("Дни недели"), days_row)

        self.notify_time = QTimeEdit()
        self.notify_time.setDisplayFormat("HH:mm")
        self.notify_time.setFixedWidth(120)
        mer_form.addRow("Время", self.notify_time)

        notif_layout.addWidget(mer_box)

        # MKL notifications
        mkl_box = QGroupBox("МКЛ")
        mkl_form = QFormLayout(mkl_box)
        mkl_form.setSpacing(8)
        mkl_form.setLabelAlignment(Qt.AlignRight)

        self.mkl_notify_enabled = QCheckBox("Включить уведомления МКЛ (просроченные)")
        mkl_form.addRow(self.mkl_notify_enabled)

        self.mkl_notify_after_days = QSpinBox()
        self.mkl_notify_after_days.setRange(0, 365)
        self.mkl_notify_after_days.setFixedWidth(120)
        mkl_form.addRow("Порог (дней)", self.mkl_notify_after_days)

        self.mkl_notify_time = QTimeEdit()
        self.mkl_notify_time.setDisplayFormat("HH:mm")
        self.mkl_notify_time.setFixedWidth(120)
        mkl_form.addRow("Время", self.mkl_notify_time)

        notif_layout.addWidget(mkl_box)

        # Sound settings
        sound_box = QGroupBox("Звук уведомлений")
        sound_form = QFormLayout(sound_box)
        sound_form.setSpacing(8)
        sound_form.setLabelAlignment(Qt.AlignRight)

        self.notify_sound_enabled = QCheckBox("Включить звук")
        sound_form.addRow(self.notify_sound_enabled)

        self.notify_sound_mode = QComboBox()
        self.notify_sound_mode.addItems(["alias", "file"])
        self.notify_sound_mode.setFixedWidth(140)
        sound_form.addRow("Режим", self.notify_sound_mode)

        self.notify_sound_alias = QLineEdit()
        self.notify_sound_alias.setPlaceholderText("SystemAsterisk")
        sound_form.addRow("Алиас (Windows)", self.notify_sound_alias)

        snd_layout = QHBoxLayout()
        snd_layout.setSpacing(8)
        self.notify_sound_file = QLineEdit()
        self.notify_sound_file.setReadOnly(True)
        self.notify_sound_file.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn_choose_sound = QPushButton("Выбрать WAV…")
        btn_choose_sound.clicked.connect(self._choose_sound_file)
        snd_layout.addWidget(self.notify_sound_file, 1)
        snd_layout.addWidget(btn_choose_sound)
        sound_form.addRow("Файл (WAV)", snd_layout)

        notif_layout.addWidget(sound_box)

        layout.addWidget(notif_group)

        # Actions
        actions = QHBoxLayout()
        actions.setSpacing(8)
        btn_apply = QPushButton("Применить")
        btn_apply.clicked.connect(self._apply)
        btn_save = QPushButton("Сохранить")
        btn_save.clicked.connect(self._save)
        actions.addStretch(1)
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

        # Notifications (Meridian)
        self.notify_enabled.setChecked(bool(s.get("notify_enabled", False)))
        days = s.get("notify_days") or []
        for i, cb in enumerate(self._day_checks):
            cb.setChecked(i in days)
        hh_mm = (s.get("notify_time", "09:00") or "09:00").split(":")
        try:
            hh = int(hh_mm[0]); mm = int(hh_mm[1])
        except Exception:
            hh, mm = 9, 0
        self.notify_time.setTime(QTime(hh, mm))

        # Notifications (MKL)
        self.mkl_notify_enabled.setChecked(bool(s.get("mkl_notify_enabled", False)))
        self.mkl_notify_after_days.setValue(int(s.get("mkl_notify_after_days", 3)))
        hh_mm = (s.get("mkl_notify_time", "09:00") or "09:00").split(":")
        try:
            hh = int(hh_mm[0]); mm = int(hh_mm[1])
        except Exception:
            hh, mm = 9, 0
        self.mkl_notify_time.setTime(QTime(hh, mm))

        # Sound
        self.notify_sound_enabled.setChecked(bool(s.get("notify_sound_enabled", True)))
        self.notify_sound_mode.setCurrentText((s.get("notify_sound_mode") or "alias"))
        self.notify_sound_alias.setText(s.get("notify_sound_alias", "SystemAsterisk"))
        self.notify_sound_file.setText(s.get("notify_sound_file", ""))

    def _choose_export_folder(self):
        start_dir = self.export_folder.text() or ""
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку экспорта", start_dir)
        if folder:
            self.export_folder.setText(folder)

    def _choose_sound_file(self):
        fname = QFileDialog.getOpenFileName(self, "Выберите WAV-файл", "", "WAV files (*.wav)")[0]
        if fname:
            self.notify_sound_file.setText(fname)
            self.notify_sound_mode.setCurrentText("file")

    def _apply(self):
        # Apply font live
        ff = self.font_family.text().strip() or "Segoe UI"
        fs = int(self.font_size.value())
        try:
            self._apply_font_cb(ff, fs)
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

        QMessageBox.information(self, "Применено", "Настройки применены.")

    def _save(self):
        s = self._get_settings()
        s["font_family"] = self.font_family.text().strip() or "Segoe UI"
        s["font_size_base_pt"] = int(self.font_size.value())
        s["export_path"] = self.export_folder.text().strip() or s.get("export_path", "")

        s["tray_enabled"] = bool(self.tray_enabled.isChecked())
        s["minimize_to_tray"] = bool(self.minimize_to_tray.isChecked())
        s["start_in_tray"] = bool(self.start_in_tray.isChecked())
        s["autostart_enabled"] = bool(self.autostart_enabled.isChecked())

        # Notifications (Meridian)
        s["notify_enabled"] = bool(self.notify_enabled.isChecked())
        days = [i for i, cb in enumerate(self._day_checks) if cb.isChecked()]
        s["notify_days"] = days
        t = self.notify_time.time()
        s["notify_time"] = f"{t.hour():02d}:{t.minute():02d}"

        # Notifications (MKL)
        s["mkl_notify_enabled"] = bool(self.mkl_notify_enabled.isChecked())
        s["mkl_notify_after_days"] = int(self.mkl_notify_after_days.value())
        t2 = self.mkl_notify_time.time()
        s["mkl_notify_time"] = f"{t2.hour():02d}:{t2.minute():02d}"

        # Sound
        s["notify_sound_enabled"] = bool(self.notify_sound_enabled.isChecked())
        s["notify_sound_mode"] = self.notify_sound_mode.currentText()
        s["notify_sound_alias"] = self.notify_sound_alias.text().strip() or "SystemAsterisk"
        s["notify_sound_file"] = self.notify_sound_file.text().strip()

        try:
            self._save_settings(s)
            QMessageBox.information(self, "Сохранено", "Настройки сохранены.")
        except Exception:
            QMessageBox.warning(self, "Сохранение", "Не удалось сохранить настройки.")