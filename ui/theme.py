
APP_STYLE = """
QMainWindow {
    background-color: #090D16;
}

QWidget {
    color: #E8ECF5;
    font-family: "Segoe UI";
}

QFrame#Sidebar {
    background-color: #0D1320;
    border-right: 1px solid #202B3D;
}

QLabel#Brand {
    color: #A58BFF;
    font-size: 27px;
    font-weight: 800;
    letter-spacing: 3px;
}

QLabel#BrandSubtitle {
    color: #71809A;
    font-size: 9px;
    letter-spacing: 2px;
}

QPushButton#NavButton {
    background-color: transparent;
    color: #8995AA;
    border: none;
    border-radius: 9px;
    padding: 13px 15px;
    text-align: left;
    font-size: 13px;
}

QPushButton#NavButton:hover {
    background-color: #192237;
    color: #FFFFFF;
}

QPushButton#NavButton[active="true"] {
    background-color: #282044;
    color: #B6A3FF;
    border-left: 3px solid #9675FF;
    font-weight: bold;
}

QFrame#ContentArea {
    background-color: #090D16;
}

QFrame#DashboardCard {
    background-color: #111A2A;
    border: 1px solid #243149;
    border-radius: 13px;
}

QLabel#CardTitle {
    color: #8998B0;
    font-size: 11px;
    font-weight: bold;
}

QLabel#CardValue {
    color: #FFFFFF;
    font-size: 27px;
    font-weight: bold;
}

QLabel#PageTitle {
    color: #FFFFFF;
    font-size: 27px;
    font-weight: bold;
}

QLabel#MutedText {
    color: #8794AA;
    font-size: 12px;
}

QPushButton#QuickButton {
    background-color: #1C2840;
    color: #C6B8FF;
    border: 1px solid #354363;
    border-radius: 9px;
    padding: 12px;
    font-weight: bold;
}

QPushButton#QuickButton:hover {
    background-color: #30254D;
    border-color: #9675FF;
}

QScrollArea {
    border: none;
    background: transparent;
}
"""
