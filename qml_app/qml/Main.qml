import QtQuick 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

ApplicationWindow {
    id: win
    visible: true
    width: 1200
    height: 720
    title: "UssurochkiRF — QML Prototype"

    // Colors
    property color bg: "#f7fafc"
    property color panel: "#ffffff"
    property color border: "#e2e8f0"
    property color text: "#0f172a"
    property color muted: "#64748b"
    property color primary: "#2563eb"
    property color amber: "#f59e0b"
    property color red: "#ef4444"
    property color green: "#10b981"

    Rectangle {
        anchors.fill: parent
        color: bg

        RowLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 16

            // Sidebar
            Rectangle {
                id: sidebar
                color: panel
                border.color: border
                radius: 12
                Layout.preferredWidth: 260
                Layout.fillHeight: true

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 10

                    RowLayout {
                        spacing: 8
                        Rectangle {
                            width: 44; height: 44; radius: 12
                            color: "#fff"
                            border.color: border
                            Text {
                                anchors.centerIn: parent
                                text: "Лого"
                                color: muted
                                font.bold: true
                            }
                        }
                        ColumnLayout {
                            Label { text: "УссурОЧки.рф"; font.bold: true }
                            Label { text: "PySide6 + QML"; color: muted; font.pixelSize: 12 }
                        }
                    }

                    Rectangle { height: 1; color: border; Layout.fillWidth: true }

                    // Nav buttons (placeholders)
                    Button { text: "Главное меню"; Layout.fillWidth: true }
                    Button { text: "Заказ МКЛ"; Layout.fillWidth: true }
                    Button { text: "Заказ Меридиан"; Layout.fillWidth: true }
                    Button { text: "Настройки"; Layout.fillWidth: true }

                    Item { Layout.fillHeight: true }
                    Label { text: "QML Prototype"; color: muted; font.pixelSize: 11 }
                }
            }

            // Main area
            ColumnLayout {
                spacing: 12
                Layout.fillWidth: true
                Layout.fillHeight: true

                // Header
                Rectangle {
                    color: panel
                    border.color: border
                    radius: 12
                    Layout.fillWidth: true
                    height: 72

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 12
                        ColumnLayout {
                            Layout.fillWidth: true
                            Label { text: "Заказ МКЛ"; font.bold: true; font.pixelSize: 22 }
                            Label { text: "Список заказов • QML Table"; color: muted }
                        }
                        Button {
                            text: "Новый заказ"
                            onClicked: newOrderDialog.open()
                        }
                        Button {
                            text: "Обновить"
                            onClicked: mklModel.refresh()
                        }
                    }
                }

                // Content panel
                Rectangle {
                    color: panel
                    border.color: border
                    radius: 12
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 8

                        // Table header
                        RowLayout {
                            spacing: 8
                            Repeater {
                                model: [
                                    "ФИО","Телефон","Товар","Sph","Cyl","Ax","BC",
                                    "Кол-во","Статус","Дата","Комментарий"
                                ]
                                delegate: Rectangle {
                                    color: "#f1f5f9"
                                    border.color: border
                                    radius: 6
                                    Layout.fillWidth: index === 0
                                    width: index === 0 ? 220 : 120
                                    height: 34
                                    Label {
                                        anchors.centerIn: parent
                                        text: modelData
                                        font.bold: true
                                        color: "#334155"
                                    }
                                }
                            }
                        }

                        // Table body
                        ScrollView {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true

                            ListView {
                                id: list
                                clip: true
                                model: mklModel
                                spacing: 6

                                delegate: RowLayout {
                                    spacing: 8
                                    // FIO
                                    Rectangle {
                                        color: "#fff"
                                        border.color: border
                                        radius: 6
                                        Layout.fillWidth: true
                                        width: 220
                                        height: 34
                                        Label { anchors.centerIn: parent; text: fio }
                                    }
                                    // phone
                                    Rectangle {
                                        color: "#fff"; border.color: border; radius: 6; width: 140; height: 34
                                        Label { anchors.centerIn: parent; text: phone }
                                    }
                                    // product
                                    Rectangle {
                                        color: "#fff"; border.color: border; radius: 6; width: 180; height: 34
                                        Label { anchors.centerIn: parent; text: product }
                                    }
                                    // sph
                                    Rectangle {
                                        color: "#fff"; border.color: border; radius: 6; width: 70; height: 34
                                        Label { anchors.centerIn: parent; text: sph }
                                    }
                                    // cyl
                                    Rectangle {
                                        color: "#fff"; border.color: border; radius: 6; width: 70; height: 34
                                        Label { anchors.centerIn: parent; text: cyl }
                                    }
                                    // ax
                                    Rectangle {
                                        color: "#fff"; border.color: border; radius: 6; width: 70; height: 34
                                        Label { anchors.centerIn: parent; text: ax }
                                    }
                                    // bc
                                    Rectangle {
                                        color: "#fff"; border.color: border; radius: 6; width: 70; height: 34
                                        Label { anchors.centerIn: parent; text: bc }
                                    }
                                    // qty
                                    Rectangle {
                                        color: "#fff"; border.color: border; radius: 6; width: 90; height: 34
                                        Label { anchors.centerIn: parent; text: qty }
                                    }
                                    // status
                                    Rectangle {
                                        color: "#FEF3C7"; border.color: "#FDE68A"; radius: 999; width: 120; height: 34
                                        Label { anchors.centerIn: parent; text: status; font.bold: true; color: "#92400E" }
                                    }
                                    // date
                                    Rectangle {
                                        color: "#fff"; border.color: border; radius: 6; width: 150; height: 34
                                        Label { anchors.centerIn: parent; text: date }
                                    }
                                    // comment flag
                                    Rectangle {
                                        color: commentFlag === "ЕСТЬ" ? "#FEE2E2" : "#D1FAE5"
                                        border.color: commentFlag === "ЕСТЬ" ? "#FECACA" : "#A7F3D0"
                                        radius: 999; width: 110; height: 34
                                        Label {
                                            anchors.centerIn: parent
                                            text: commentFlag
                                            font.bold: true
                                            color: commentFlag === "ЕСТЬ" ? "#7F1D1D" : "#065F46"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    Dialog {
        id: newOrderDialog
        modal: true
        title: "Новый заказ МКЛ"
        standardButtons: Dialog.Ok | Dialog.Cancel

        onAccepted: {
            mklModel.addOrderWithComment(
                fioField.text, phoneField.text, productField.text, qtyField.text,
                sphField.text, cylField.text, axField.text, bcField.text, commentField.text
            )
        }

        contentItem: ColumnLayout {
            spacing: 8
            padding: 12

            RowLayout {
                spacing: 8
                TextField { id: fioField; placeholderText: "ФИО"; Layout.fillWidth: true }
                TextField { id: phoneField; placeholderText: "Телефон"; width: 160 }
            }
            RowLayout {
                spacing: 8
                TextField { id: productField; placeholderText: "Товар"; Layout.fillWidth: true }
                TextField { id: qtyField; placeholderText: "Кол-во"; width: 100; text: "1" }
            }
            RowLayout {
                spacing: 8
                TextField { id: sphField; placeholderText: "Sph"; width: 120 }
                TextField { id: cylField; placeholderText: "Cyl"; width: 120 }
                TextField { id: axField; placeholderText: "Ax"; width: 120 }
                TextField { id: bcField; placeholderText: "BC"; width: 120 }
            }
            TextArea { id: commentField; placeholderText: "Комментарий"; Layout.fillWidth: true; Layout.preferredHeight: 100 }
        }
    }
}