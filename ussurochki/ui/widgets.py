from typing import Optional

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt, pyqtProperty
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QCheckBox,
    QDoubleSpinBox,
    QSpinBox,
    QPushButton,
    QStackedWidget,
    QGraphicsOpacityEffect,
)


class OptionalDoubleSpin(QWidget):
    def __init__(self, decimals=2, minimum=0.0, maximum=100.0, step=0.25, placeholder="пусто", parent=None):
        super().__init__(parent)
        self.chk = QCheckBox(placeholder)
        self.spin = QDoubleSpinBox()
        self.spin.setDecimals(decimals)
        self.spin.setRange(minimum, maximum)
        self.spin.setSingleStep(step)
        self.spin.setEnabled(False)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        lay.addWidget(self.chk)
        lay.addWidget(self.spin, 1)
        self.chk.toggled.connect(self.spin.setDisabled)
        self.chk.toggled.connect(lambda s: self.spin.setEnabled(not s))

    def value(self) -> Optional[float]:
        if self.chk.isChecked():
            return None
        return float(self.spin.value())

    def setValue(self, val: Optional[float]):
        if val is None:
            self.chk.setChecked(True)
            self.spin.setEnabled(False)
        else:
            self.chk.setChecked(False)
            self.spin.setEnabled(True)
            self.spin.setValue(float(val))


class OptionalIntSpin(QWidget):
    def __init__(self, minimum=0, maximum=180, step=1, placeholder="пусто", parent=None):
        super().__init__(parent)
        self.chk = QCheckBox(placeholder)
        self.spin = QSpinBox()
        self.spin.setRange(minimum, maximum)
        self.spin.setSingleStep(step)
        self.spin.setEnabled(False)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        lay.addWidget(self.chk)
        lay.addWidget(self.spin, 1)
        self.chk.toggled.connect(self.spin.setDisabled)
        self.chk.toggled.connect(lambda s: self.spin.setEnabled(not s))

    def value(self) -> Optional[int]:
        if self.chk.isChecked():
            return None
        return int(self.spin.value())

    def setValue(self, val: Optional[int]):
        if val is None:
            self.chk.setChecked(True)
            self.spin.setEnabled(False)
        else:
            self.chk.setChecked(False)
            self.spin.setEnabled(True)
            self.spin.setValue(int(val))


class BigNavButton(QPushButton):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(100)
        self.setStyleSheet("""
            QPushButton {
                font-size: 18pt;
                border-radius: 12px;
                padding: 16px 24px;
            }
        """)


class FadingStackedWidget(QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._anim = QPropertyAnimation(self, b"opacity", self)
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity_effect)

    def setCurrentIndex(self, index: int):
        self._fade_to(index)

    def setCurrentWidget(self, widget: QWidget):
        idx = self.indexOf(widget)
        self._fade_to(idx)

    def _fade_to(self, index: int):
        if index == self.currentIndex():
            return
        self._anim.stop()
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.finished.connect(lambda: self._switch(index))
        self._anim.start()

    def _switch(self, index: int):
        super().setCurrentIndex(index)
        self._anim.finished.disconnect()
        self._anim.stop()
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.start()

    def get_opacity(self) -> float:
        return self._opacity_effect.opacity()

    def set_opacity(self, value: float):
        self._opacity_effect.setOpacity(value)

    opacity = pyqtProperty(float, fget=get_opacity, fset=set_opacity)