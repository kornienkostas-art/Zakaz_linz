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

    // View state
    property string currentView: "mkl"

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

                    Button { text: "Заказ МКЛ"; Layout.fillWidth: true; onClicked: currentView = "mkl" }
                    Button { text: "Заказ Меридиан"; Layout.fillWidth: true; onClicked: currentView = "meridian" }
                    Button { text: "Настройки"; Layout.fillWidth: true; enabled: false }

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
                            Label {
                                text: currentView === "mkl" ? "Заказ МКЛ" : "Заказ Меридиан"
                                font.bold: true; font.pixelSize: 22
                            }
                            Label {
                                text: currentView === "mkl" ? "Список заказов • QML Table" : "Список заказов и статусы"
                                color: muted
                            }
                        }
                        // Right header buttons
                        Button {
                            visible: currentView === "mkl"
                            text: "Новый заказ"
                            onClicked: newOrderDialog.open()
                        }
                        Button {
                            visible: currentView === "mkl"
                            text: "Обновить"
                            onClicked: mklModel.refresh()
                        }
                        Button {
                            visible: currentView === "meridian"
                            text: "Новый заказ"
                            onClicked: merNewDialog.open()
                        }
                        Button {
                            visible: currentView === "meridian"
                            text: "Обновить"
                            onClicked: merModel.refresh()
                        }
                    }
                }

                // Content area with two views
                StackLayout {
                    id: stack
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    currentIndex: currentView === "mkl" ? 0 : 1

                    // MKL View
                    Rectangle {
                        color: panel
                        border.color: border
                        radius: 12

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 8

                            RowLayout {
                                spacing: 8
                                Button {
                                    text: "Редактировать"
                                    enabled: mklList.currentIndex >= 0
                                    onClicked: {
                                        const idx = mklList.currentIndex
                                        if (idx < 0) return
                                        const idVal = mklModel.data(mklModel.index(idx,0), mklModel.roleNames().id)
                                        const o = mklModel.getOrder(idVal)
                                        if (!o) return
                                        // Prefill
                                        editId.text = idVal
                                        efio.text = o.fio || ""
                                        ephone.text = o.phone || ""
                                        eprod.text = o.product || ""
                                        eqty.text = String(o.qty || "")
                                        esph.text = o.sph || ""
                                        ecyl.text = o.cyl || ""
                                        eax.text = o.ax || ""
                                        ebc.text = o.bc || ""
                                        ecomment.text = o.comment || ""
                                        editDialog.open()
                                    }
                                }
                                Button {
                                    text: "Удалить"
                                    enabled: mklList.currentIndex >= 0
                                    onClicked: {
                                        const idx = mklList.currentIndex
                                        if (idx < 0) return
                                        const idVal = mklModel.data(mklModel.index(idx,0), mklModel.roleNames().id)
                                        mklModel.deleteOrder(idVal)
                                    }
                                }
                            }

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
                                    id: mklList
                                    clip: true
                                    model: mklModel
                                    spacing: 6
                                    currentIndex: -1
                                    highlight: Rectangle { color: "transparent" }
                                    delegate: MouseArea {
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onClicked: mklList.currentIndex = index

                                        RowLayout {
                                            anchors.fill: parent
                                            spacing: 8
                                            // FIO
                                            Rectangle {
                                                color: mklList.currentIndex === index ? "#e0ecff" : "#fff"
                                                border.color: border
                                                radius: 6
                                                Layout.fillWidth: true
                                                width: 220
                                                height: 34
                                                Label { anchors.centerIn: parent; text: fio }
                                            }
                                            // phone
                                            Rectangle {
                                                color: mklList.currentIndex === index ? "#e0ecff" : "#fff"
                                                border.color: border; radius: 6; width: 140; height: 34
                                                Label { anchors.centerIn: parent; text: phone }
                                            }
                                            // product
                                            Rectangle {
                                                color: mklList.currentIndex === index ? "#e0ecff" : "#fff"
                                                border.color: border; radius: 6; width: 180; height: 34
                                                Label { anchors.centerIn: parent; text: product }
                                            }
                                            // sph
                                            Rectangle {
                                                color: mklList.currentIndex === index ? "#e0ecff" : "#fff"
                                                border.color: border; radius: 6; width: 70; height: 34
                                                Label { anchors.centerIn: parent; text: sph }
                                            }
                                            // cyl
                                            Rectangle {
                                                color: mklList.currentIndex === index ? "#e0ecff" : "#fff"
                                                border.color: border; radius: 6; width: 70; height: 34
                                                Label { anchors.centerIn: parent; text: cyl }
                                            }
                                            // ax
                                            Rectangle {
                                                color: mklList.currentIndex === index ? "#e0ecff" : "#fff"
                                                border.color: border; radius: 6; width: 70; height: 34
                                                Label { anchors.centerIn: parent; text: ax }
                                            }
                                            // bc
                                            Rectangle {
                                                color: mklList.currentIndex === index ? "#e0ecff" : "#fff"
                                                border.color: border; radius: 6; width: 70; height: 34
                                                Label { anchors.centerIn: parent; text: bc }
                                            }
                                            // qty
                                            Rectangle {
                                                color: mklList.currentIndex === index ? "#e0ecff" : "#fff"
                                                border.color: border; radius: 6; width: 90; height: 34
                                                Label { anchors.centerIn: parent; text: qty }
                                            }
                                            // status
                                            Rectangle {
                                                color: "#FEF3C7"; border.color: "#FDE68A"; radius: 999; width: 120; height: 34
                                                Label { anchors.centerIn: parent; text: status; font.bold: true; color: "#92400E" }
                                            }
                                            // date
                                            Rectangle {
                                                color: mklList.currentIndex === index ? "#e0ecff" : "#fff"
                                                border.color: border; radius: 6; width: 150; height: 34
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

                    // Meridian View
                    Rectangle {
                        color: panel
                        border.color: border
                        radius: 12

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 8

                            RowLayout {
                                spacing: 8
                                Button {
                                    text: "Удалить"
                                    enabled: merList.currentIndex >= 0
                                    onClicked: {
                                        const idx = merList.currentIndex
                                        if (idx < 0) return
                                        const idVal = merModel.data(merModel.index(idx,0), merModel.roleNames().id)
                                        merModel.deleteOrder(idVal)
                                    }
                                }
                                Button {
                                    text: "Сменить статус"
                                    enabled: merList.currentIndex >= 0
                                    onClicked: statusDialog.open()
                                }
                            }

                            // Table header
                            RowLayout {
                                spacing: 8
                                Repeater {
                                    model: [ "Название заказа", "Позиций", "Статус", "Дата" ]
                                    delegate: Rectangle {
                                        color: "#f1f5f9"
                                        border.color: border
                                        radius: 6
                                        Layout.fillWidth: index === 0
                                        width: [260,100,140,160][index]
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
                                    id: merList
                                    clip: true
                                    model: merModel
                                    spacing: 6
                                    currentIndex: -1

                                    delegate: MouseArea {
                                        anchors.fill: parent
                                        onClicked: merList.currentIndex = index

                                        RowLayout {
                                            anchors.fill: parent
                                            spacing: 8

                                            Rectangle {
                                                color: merList.currentIndex === index ? "#e0ecff" : "#fff"
                                                border.color: border; radius: 6; width: 260; height: 34
                                                Label { anchors.centerIn: parent; text: title }
                                            }
                                            Rectangle {
                                                color: merList.currentIndex === index ? "#e0ecff" : "#fff"
                                                border.color: border; radius: 6; width: 100; height: 34
                                                Label { anchors.centerIn: parent; text: itemsCount }
                                            }
                                            Rectangle {
                                                color: "#FEF3C7"; border.color: "#FDE68A"; radius: 999; width: 140; height: 34
                                                Label { anchors.centerIn: parent; text: status; font.bold: true; color: "#92400E" }
                                            }
                                            Rectangle {
                                                color: merList.currentIndex === index ? "#e0ecff" : "#fff"
                                                border.color: border; radius: 6; width: 160; height: 34
                                                Label { anchors.centerIn: parent; text: date }
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
    }

    // MKL dialogs
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

    Dialog {
        id: editDialog
        modal: true
        title: "Редактирование заказа МКЛ"
        standardButtons: Dialog.Ok | Dialog.Cancel

        onAccepted: {
            mklModel.updateOrder(parseInt(editId.text),
                                 efio.text, ephone.text, eprod.text, eqty.text,
                                 esph.text, ecyl.text, eax.text, ebc.text, ecomment.text)
        }

        contentItem: ColumnLayout {
            spacing: 8
            padding: 12

            TextField { id: editId; visible: false }
            RowLayout {
                spacing: 8
                TextField { id: efio; placeholderText: "ФИО"; Layout.fillWidth: true }
                TextField { id: ephone; placeholderText: "Телефон"; width: 160 }
            }
            RowLayout {
                spacing: 8
                TextField { id: eprod; placeholderText: "Товар"; Layout.fillWidth: true }
                TextField { id: eqty; placeholderText: "Кол-во"; width: 100 }
            }
            RowLayout {
                spacing: 8
                TextField { id: esph; placeholderText: "Sph"; width: 120 }
                TextField { id: ecyl; placeholderText: "Cyl"; width: 120 }
                TextField { id: eax; placeholderText: "Ax"; width: 120 }
                TextField { id: ebc; placeholderText: "BC"; width: 120 }
            }
            TextArea { id: ecomment; placeholderText: "Комментарий"; Layout.fillWidth: true; Layout.preferredHeight: 100 }
        }
    }

    // Meridian dialogs
    Dialog {
        id: merNewDialog
        modal: true
        title: "Новый заказ Меридиан"
        standardButtons: Dialog.Ok | Dialog.Cancel
        onAccepted: merModel.addOrder(merTitle.text)

        contentItem: ColumnLayout {
            spacing: 8
            padding: 12
            TextField { id: merTitle; placeholderText: "Название заказа"; Layout.fillWidth: true }
            Label { text: "Позиции добавим на следующем шаге"; color: muted }
        }
    }

    Dialog {
        id: statusDialog
        modal: true
        title: "Сменить статус"
        standardButtons: Dialog.Ok | Dialog.Cancel
        onAccepted: {
            const idx = merList.currentIndex
            if (idx < 0) return
            const idVal = merModel.data(merModel.index(idx,0), merModel.roleNames().id)
            merModel.updateStatus(idVal, statusCombo.currentText)
        }

        contentItem: ColumnLayout {
            spacing: 8
            padding: 12
            ComboBox {
                id: statusCombo
                model: [ "Не заказан", "Заказан" ]
                currentIndex: 0
                Layout.preferredWidth: 200
            }
        }
    }
}