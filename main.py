import sys
from PyQt5 import QtWidgets
from qt_material import apply_stylesheet

from database import init_db
from mkl_interface import MKLInterface
from meridian_interface import MeridianInterface


def main():
    init_db()

    app = QtWidgets.QApplication(sys.argv)
    apply_stylesheet(app, theme="light_blue.xml")

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