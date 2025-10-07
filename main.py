import sys
from PyQt5 import QtWidgets
try:
    from qt_material import apply_stylesheet
except Exception:
    apply_stylesheet = None

from database import init_db
from mkl_interface import MKLInterface
from meridian_interface import MeridianInterface


def main():
    init_db()

    app = QtWidgets.QApplication(sys.argv)
    # Яркая тема интерфейса (если модуль qt_material установлен)
    if apply_stylesheet:
        apply_stylesheet(app, theme="light_cyan.xml")

    win = QtWidgets.QMainWindow()
    win.setWindowTitle("Система управления заказами")

    tabs = QtWidgets.QTabWidget()
    tabs.addTab(MKLInterface(), "Заказы МКЛ")
    tabs.addTab(MeridianInterface(), "Заказы Меридиан")

    win.setCentralWidget(tabs)
    win.resize(1100, 700)
    win.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()