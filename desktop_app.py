import sys
import webbrowser
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QLabel
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, Qt

class GomokuDesktop(QMainWindow):
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.setWindowTitle("線上五子棋 - 桌面端")
        self.resize(550, 800)
        
        qr = self.frameGeometry()
        cp = QApplication.desktop().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_widget.setStyleSheet("background-color: #f2f2f7;")
        
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        top_bar = QWidget()
        top_bar.setFixedHeight(60)
        top_bar.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.9);
                border-bottom: 1px solid rgba(60, 60, 67, 0.18);
            }
        """)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(15, 0, 15, 0)

        title = QLabel("五子棋連線大廳")
        title.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            color: #1c1c1e;
            border: none;
            background: transparent;
        """)
        
        web_btn = QPushButton("開啟網頁版")
        web_btn.setCursor(Qt.PointingHandCursor)
        web_btn.setStyleSheet("""
            QPushButton {
                background-color: #007aff;
                color: white;
                border-radius: 15px;
                padding: 8px 15px;
                font-size: 14px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #005bb5;
            }
            QPushButton:pressed {
                background-color: #003d82;
            }
        """)
        web_btn.clicked.connect(self.open_browser)

        top_layout.addWidget(title)
        top_layout.addStretch()
        top_layout.addWidget(web_btn)

        self.browser = QWebEngineView()
        self.browser.load(QUrl(url))
        
        layout.addWidget(top_bar)
        layout.addWidget(self.browser)

    def open_browser(self):
        webbrowser.open(self.url)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    target_url = "http://127.0.0.1:5000"
    window = GomokuDesktop(target_url)
    window.show()
    sys.exit(app.exec_())
