import sys
import os
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QThread, Qt, pyqtSignal
import serial
import serial.tools.list_ports

# v 7.0

'''     環境設定     '''
title_name = "computer-A"   # 視窗標題
window_size = (850, 650)    # width, height
icon_path = os.path.join(os.path.dirname(__file__), "icon.png")     #先抓當前檔案的路徑,再加上icon
background_path=os.path.join(os.path.dirname(__file__), "background.jpg")  #背景圖片
background_path_fixed = background_path.replace("\\", "/")  #斜線翻轉
serial_baud=115200
index_name="呱呱呱呱呱" #首頁標題

class SerialReaderThread(QThread):
    data_received = pyqtSignal(str)  # 發送訊息到主介面

    def __init__(self, serial_port):
        super().__init__()
        #self.port = port
        self.running = True
        self.serial_connection = serial_port

    def run(self):
        try:
            # 打開串列埠
            #self.serial_connection = serial.Serial(self.port, serial_baud)
            print(self.serial_connection)
            while self.running:
                if self.serial_connection.in_waiting > 0:  # 確認有資料可讀
                    try:
                        data = self.serial_connection.readline().decode('utf-8', errors='ignore').strip()
                        if data:  # 避免空行干擾
                            self.data_received.emit(data)
                    except Exception as e:
                        self.data_received.emit(f"Error reading data: {str(e)}")
        except Exception as e:
            self.data_received.emit(f"Error: {str(e)}")
        finally:
            if self.serial_connection:
                self.serial_connection.close()

    def stop(self):
        self.running = False
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.connect_check=False
        self.username=""
        self.setObjectName("MainWindow")
        self.setWindowTitle(title_name)
        self.resize(window_size[0], window_size[1])
        self.clear_window()

        # 設定背景圖片
        self.setStyleSheet(f"""
            QMainWindow {{
                background-image: url({background_path_fixed});
                background-position: center;
                background-repeat: none;
            }}
        """)

        # icon圖像設定
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print("Icon file not found!")
        
        # 初始化序列埠
        self.serial_port = None

        # 建立中央 Widget
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        
        # 建立主布局
        main_layout = QtWidgets.QVBoxLayout(central_widget)

        # 建立標題區域
        title_container = QtWidgets.QWidget()
        title_layout = QtWidgets.QVBoxLayout(title_container)

        # 首頁標題
        title_label = QtWidgets.QLabel(index_name)
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 36px;
                font-weight: bold;
                color: #333333;
                margin-bottom: 10px;
                font-family: "Microsoft YaHei", "微軟正黑體";
            }
        """)

        # 提示文字
        hint_label = QtWidgets.QLabel("請選擇模式")
        hint_label.setAlignment(QtCore.Qt.AlignCenter)
        hint_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                color: #666666;
                font-family: "Microsoft YaHei", "微軟正黑體";
            }
        """)

        # 建立序列埠控制區域
        port_control = QtWidgets.QHBoxLayout()
        
        # 建立序列埠選擇下拉選單
        self.port_combo = QtWidgets.QComboBox()
        self.update_ports()
        port_label = QtWidgets.QLabel("序列埠選擇:")
        port_label.setStyleSheet("""
            QLabel {
                font-size: 20px;  /* 放大字體 */
                font-weight: bold;  /* 粗體 */
                color: #333333;
                font-family: "Microsoft YaHei", "微軟正黑體";  /* 設置字體 */
            }
        """)
        port_control.addWidget(port_label)
        port_control.setAlignment(QtCore.Qt.AlignCenter)
        port_control.addWidget(self.port_combo)
        
        # 建立連接按鈕
        self.connect_button = QtWidgets.QPushButton("連接")
        self.connect_button.setFixedSize(100, 40)
        self.connect_button.setStyleSheet("""
            QPushButton {
                border-radius: 20px;
                background-color: #4CAF50;
                color: white;
                border: none;
                font-family: "Microsoft YaHei", "微軟正黑體";
                font-size: 16px
            }
            QPushButton:hover {
                background-color: #008000;
            }
        """)
        self.connect_button.clicked.connect(self.toggle_connection)
        port_control.addWidget(self.connect_button)

    #刷新序列埠
        self.refresh_button = QtWidgets.QPushButton("刷新")
        self.refresh_button.setFixedSize(100, 40)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                border-radius: 20px;
                background-color: #c0c0c0;
                color: white;
                border: none;
                font-family: "Microsoft YaHei", "微軟正黑體";
                font-size: 16px
            }
            QPushButton:hover {
                background-color: #808080;
            }
        """)
        self.refresh_button.clicked.connect(self.refresh_ports)
        print("已刷新")
        port_control.addWidget(self.refresh_button)


    # 建立名字輸入區
        login_layout = QtWidgets.QHBoxLayout()

    # 提示字
        name_label = QtWidgets.QLabel("輸入名字：")
        name_label.setFixedSize(100,40)  # 設置固定高度
        name_label.setStyleSheet("""
            QLabel {
                font-size: 20px;  /* 放大字體 */
                font-weight: bold;  /* 粗體 */
                color: #333333;
                font-family: "Microsoft YaHei", "微軟正黑體";  /* 設置字體 */
            }
        """)

    #名字輸入框
        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setFixedSize(195, 45)
        self.name_input.setStyleSheet("""
            QLineEdit {
                font-size: 16px;
                font-family: "Microsoft YaHei", "微軟正黑體";
                padding: 5px;
                border-radius: 10px;
                border: 2px solid #ccc;
                padding: 5px;
                font-size: 16px;
            }
        """)

    #登入按鈕
        self.login_button = QtWidgets.QPushButton("登入")
        self.login_button.setFixedSize(95, 40)
        self.login_button.setStyleSheet("""
            QPushButton {
                border-radius: 20px;
                background-color: #00bfff;
                color: white;
                border: none;
                font-family: "Microsoft YaHei", "微軟正黑體";
                font-size: 16px
            }
            QPushButton:hover {
                background-color: #1e90ff;
            }
        """)
        #self.login_button.setEnabled(False)  # 預設按鈕為禁用
        self.login_button.clicked.connect(self.text_input_selected)
        self.login_button.clicked.connect(self.start_listening)
        
        login_layout.addWidget(name_label)
        login_layout.addWidget(self.name_input)
        login_layout.addWidget(self.login_button)
        login_layout.setAlignment(Qt.AlignCenter)

        # 將標題和提示文字加入標題布局
        title_layout.addWidget(title_label)
        title_layout.addWidget(hint_label)
        main_layout.addWidget(title_container)
        main_layout.addLayout(port_control)
        main_layout.addLayout(login_layout)
        main_layout.addStretch()  # 添加彈性空間，使標題置於上方

        self.serial_thread = None

# 首頁
    def home_index_selected(self):
        central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)
        self.clear_window()

        main_layout = QtWidgets.QVBoxLayout(central_widget)

        # 設定背景圖片
        self.setStyleSheet(f"""
            QMainWindow {{
                background-image: url({background_path_fixed});
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
                background-size: cover;
            }}
        """)

        # 標題
        title_container = QtWidgets.QWidget()
        title_layout = QtWidgets.QVBoxLayout(title_container)
        
        title_label = QtWidgets.QLabel(index_name)
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 36px;
                font-weight: bold;
                color: #333333;
                margin-bottom: 10px;
                font-family: "Microsoft YaHei", "微軟正黑體";
            }
        """)
        
        hint_label = QtWidgets.QLabel("請選擇模式")
        hint_label.setAlignment(QtCore.Qt.AlignCenter)
        hint_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                color: #666666;
                font-family: "Microsoft YaHei", "微軟正黑體";
            }
        """)
        
        # 建立序列埠控制區域
        port_control = QtWidgets.QHBoxLayout()
        
        # 建立序列埠選擇下拉選單
        self.port_combo = QtWidgets.QComboBox()
        self.update_ports()
        port_label = QtWidgets.QLabel("序列埠選擇:")
        port_label.setStyleSheet("""
            QLabel {
                font-size: 20px;  /* 放大字體 */
                font-weight: bold;  /* 粗體 */
                color: #333333;
                font-family: "Microsoft YaHei", "微軟正黑體";  /* 設置字體 */
            }
        """)
        port_control.addWidget(port_label)
        port_control.setAlignment(QtCore.Qt.AlignCenter)
        port_control.addWidget(self.port_combo)
        
        # 建立連接按鈕
        if self.connect_check:
            self.connect_button = QtWidgets.QPushButton("斷開")
            self.connect_button.setFixedSize(100, 40)
            self.connect_button.setStyleSheet("""
                QPushButton {
                    border-radius: 20px;
                    background-color: #ff0000;
                    color: white;
                    border: none;
                    font-family: "Microsoft YaHei", "微軟正黑體";
                    font-size: 16px
                }
                QPushButton:hover {
                    background-color: #dc143c;
                }
            """)
        else:
            self.connect_button = QtWidgets.QPushButton("連接")
            self.connect_button.setFixedSize(100, 40)
            self.connect_button.setStyleSheet("""
                QPushButton {
                    border-radius: 20px;
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    font-family: "Microsoft YaHei", "微軟正黑體";
                    font-size: 16px
                }
                QPushButton:hover {
                    background-color: #008000;
                }
            """)
        self.connect_button.clicked.connect(self.toggle_connection)
        port_control.addWidget(self.connect_button)

    #刷新序列埠
        self.refresh_button = QtWidgets.QPushButton("刷新")
        self.refresh_button.setFixedSize(100, 40)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                border-radius: 20px;
                background-color: #c0c0c0;
                color: white;
                border: none;
                font-family: "Microsoft YaHei", "微軟正黑體";
                font-size: 16px
            }
            QPushButton:hover {
                background-color: #808080;
            }
        """)
        self.refresh_button.clicked.connect(self.refresh_ports)
        print("已刷新")
        port_control.addWidget(self.refresh_button)

    # 建立名字輸入區
        login_layout = QtWidgets.QHBoxLayout()

    # 提示字
        name_label = QtWidgets.QLabel("輸入名字：")
        name_label.setFixedSize(100,40)  # 設置固定高度
        name_label.setStyleSheet("""
            QLabel {
                font-size: 20px;  /* 放大字體 */
                font-weight: bold;  /* 粗體 */
                color: #333333;
                font-family: "Microsoft YaHei", "微軟正黑體";  /* 設置字體 */
            }
        """)

    #名字輸入框
        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setFixedSize(195, 45)
        self.name_input.setStyleSheet("""
            QLineEdit {
                font-size: 16px;
                font-family: "Microsoft YaHei", "微軟正黑體";
                padding: 5px;
                border-radius: 10px;
                border: 2px solid #ccc;
                padding: 5px;
                font-size: 16px;
            }
        """)

    #登入按鈕
        self.login_button = QtWidgets.QPushButton("登入")
        self.login_button.setFixedSize(95, 40)
        self.login_button.setStyleSheet("""
            QPushButton {
                border-radius: 20px;
                background-color: #00bfff;
                color: white;
                border: none;
                font-family: "Microsoft YaHei", "微軟正黑體";
                font-size: 16px
            }
            QPushButton:hover {
                background-color: #1e90ff;
            }
        """)
        #self.login_button.setEnabled(False)  # 預設按鈕為禁用
        self.login_button.clicked.connect(self.text_input_selected)
        
        login_layout.addWidget(name_label)
        login_layout.addWidget(self.name_input)
        login_layout.addWidget(self.login_button)
        login_layout.setAlignment(Qt.AlignCenter)

        title_layout.addWidget(title_label)
        title_layout.addWidget(hint_label)
        main_layout.addWidget(title_container)
        main_layout.addLayout(port_control)
        main_layout.addLayout(login_layout)
        main_layout.addStretch()
    '''
# 文字選單區
    def text_input_selected(self):
        self.username = self.name_input.text()
        clear_window()
        central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QtWidgets.QHBoxLayout(central_widget)
        main_layout.setSpacing(20)

        # 左側容器
        left_container = QtWidgets.QWidget()
        left_container.setMinimumWidth(int(window_size[0] * 0.6))
        left_container.setMaximumWidth(int(window_size[0] * 0.75))
        left_layout = QtWidgets.QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 建立並保存傳送和接收區域的引用
        self.send_area = self.create_section_with_return(left_layout, "傳送區", "請輸入內容...")
        self.receive_area = self.create_section_with_return(left_layout, "接收區", "等待接收...")
        
        main_layout.addWidget(left_container)
        
        # 右側容器
        right_container = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 120, 0, 0)  # 調整上方邊距以對齊傳送區
        
        # 送出按鈕
        send_button = QtWidgets.QPushButton("送出")
        send_button.setFixedSize(150, 60)
        send_button.setStyleSheet("""
            QPushButton {
                border-radius: 30px;
                background-color: #4CAF50;
                color: white;
                border: none;
                font-size: 16px;
                font-family: "Microsoft YaHei", "微軟正黑體";  /* 新增字體設定 */
            }
            QPushButton:hover {
                background-color: #008000;
            }
        """)
        send_button.clicked.connect(self.send_message)
        
        right_layout.addWidget(send_button, 0, QtCore.Qt.AlignTop)  # 使用 AlignTop 確保按鈕在頂部
        main_layout.addWidget(right_container)

        # 清除訊息
        clear_button = QtWidgets.QPushButton("清除")
        clear_button.setFixedSize(150, 60)
        clear_button.setStyleSheet("""
            QPushButton {
                border-radius: 30px;
                background-color: #c0c0c0;
                color: white;
                border: none;
                font-size: 16px;
                font-family: "Microsoft YaHei", "微軟正黑體";  /* 新增字體設定 */
            }
            QPushButton:hover {
                background-color: #808080;
            }
        """)
        clear_button.clicked.connect(self.clear_message)
        
        right_layout.addWidget(clear_button, 1, QtCore.Qt.AlignTop)  # 使用 AlignTop 確保按鈕在頂部
        main_layout.addWidget(right_container)

# 建立區塊並返回文字編輯框的引用
    def create_section_with_return(self, parent_layout, label_text, placeholder):
        section_layout = QtWidgets.QVBoxLayout()
        
        label = QtWidgets.QLabel(label_text)
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #333333;
                font-family: "Microsoft YaHei", "微軟正黑體";
            }
        """)
        
        text_edit = QtWidgets.QTextEdit()
        text_edit.setPlaceholderText(placeholder)
        text_edit.setStyleSheet("""
            QTextEdit {
                border-radius: 10px;
                border: 2px solid #ccc;
                padding: 5px;
                font-size: 16px;
            }
        """)
        
        section_layout.addWidget(label)
        section_layout.addWidget(text_edit)
        parent_layout.addLayout(section_layout)
        
        return text_edit
    '''

# 文字區改版
    def text_input_selected(self):
        self.clear_window()
        self.username = self.name_input.text()
    # 主窗口的Widget
        central_widget = QtWidgets.QLabel()
        central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QtWidgets.QVBoxLayout(central_widget)

    # 新增選單欄
        menu_bar = self.menuBar()
        view_menu = QtWidgets.QMenu("功能", self)
        menu_bar.addMenu(view_menu)

        # 新增「滑到底部」按鈕
        scroll_to_bottom_action = view_menu.addAction("滑到底部")
        scroll_to_bottom_action.triggered.connect(self.scroll_to_bottom)

    # 用戶名稱區域
        username_label = QtWidgets.QLabel(f"用戶名稱: {self.username}")
        username_label.setAlignment(Qt.AlignLeft)
        username_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #333333;
                font-family: "Microsoft YaHei", "微軟正黑體";
            }
        """)
        main_layout.addWidget(username_label)

    # 聊天顯示區域
        self.chat_area = QtWidgets.QScrollArea(self)
        self.chat_area.setWidgetResizable(True)
        self.chat_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.chat_area.setStyleSheet("""
            QScrollArea {
                border: 2px solid #ccc;
                border-radius: 10px;
                background: white;
            }
        """)

    # 聊天內容
        self.chat_content = QtWidgets.QWidget()
        self.chat_content_layout = QtWidgets.QVBoxLayout()
        self.chat_content.setLayout(self.chat_content_layout)
        self.chat_area.setWidget(self.chat_content)
        main_layout.addWidget(self.chat_area)

    # 底部輸入和按鈕區域
        input_layout = QtWidgets.QHBoxLayout()

    # 輸入框
        self.input_field = QtWidgets.QLineEdit(self)
        self.input_field.setPlaceholderText("輸入訊息...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                border: 2px solid #ccc;
                border-radius: 10px;
                padding: 5px;
                font-size: 16px;
            }
        """)

    # 文件欄位
        self.file_label = QtWidgets.QLabel("未選擇檔案")
        self.file_label.setStyleSheet("""
            QLabel {
                border: 2px solid #ccc;
                border-radius: 10px;
                padding: 5px;
                font-size: 16px;
                min-width: 150px;
                font-family: "Microsoft YaHei", "微軟正黑體";
            }
        """)
        self.file_label.setAlignment(Qt.AlignCenter)

    # 瀏覽按鈕
        browse_button = QtWidgets.QPushButton("瀏覽")
        browse_button.setFixedSize(100, 40)
        browse_button.clicked.connect(self.open_file_dialog)
        browse_button.setStyleSheet("""
            QPushButton {
                border-radius: 17px;
                background-color: #4CAF50;
                color: white;
                border: none;
                font-size: 16px;
                font-family: "Microsoft YaHei", "微軟正黑體";
            }
            QPushButton:hover {
                background-color: #008000;
            }
        """)

    # 傳送按鈕
        send_button = QtWidgets.QPushButton("傳送")
        send_button.setFixedSize(100, 40)
        send_button.clicked.connect(self.send_message)
        send_button.setStyleSheet("""
            QPushButton {
                border-radius: 17px;
                background-color: #4CAF50;
                color: white;
                border: none;
                font-size: 16px;
                font-family: "Microsoft YaHei", "微軟正黑體";
            }
            QPushButton:hover {
                background-color: #008000;
            }
        """)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.file_label)
        input_layout.addWidget(browse_button)
        input_layout.addWidget(send_button)
        main_layout.addLayout(input_layout)
        central_widget.setLayout(main_layout)

    # 設定布局的邊距和間距
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

#選擇檔案
    def open_file_dialog(self):
        options = QtWidgets.QFileDialog.Options()
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "選擇文件", "", "All Files (*);;Text Files (*.txt)", options=options)
        if file_path:
            self.on_file_selected(file_path)

    def on_file_selected(self, file_path):
        file_name = os.path.basename(file_path)
        self.file_label.setText(file_name)

#傳送訊息
    def send_message(self):
        # 送文字訊息
        message = self.input_field.text()
        if message.strip():
            try:
                #message+="\n"
                self.serial_port.write(message.encode('UTF-8'))
                self.show_message(message, is_self=True)
                print(f"送出訊息-> {message}")
                self.input_field.clear()
            except Exception as e:
                print(f"Error sending message: {e}")
        # 送檔案
        if hasattr(self, 'file_label') and self.file_label.text() != "未選擇檔案":
            try:
                file_path = self.file_label.text()
                # 讀取檔案內容
                with open(file_path, 'rb') as file:
                    file_data = file.read()
                    # 傳送檔案名稱和大小訊息
                    file_info = f"FILE:{os.path.basename(file_path)}:{len(file_data)}"
                    self.serial_port.write(file_info.encode('UTF-8') + b'\n')
                    # 傳送檔案內容
                    self.serial_port.write(file_data)
                    # 顯示在聊天視窗
                    self.show_message(f"已傳送檔案: {os.path.basename(file_path)}", is_self=True)
                    print(f"檔案傳送成功: {file_path}")
                    # 清除檔案選擇
                    self.file_label.setText("未選擇檔案")
            except Exception as e:
                print(f"檔案傳送錯誤: {e}")
                QtWidgets.QMessageBox.warning(self, "錯誤", f"檔案傳送失敗: {str(e)}")

# 接收訊息
    def start_listening(self):
        #self.serial_port = self.port_selector.currentText()
        if hasattr(self, 'serial_port') and self.serial_port.is_open:
            self.serial_thread = SerialReaderThread(self.serial_port)
            self.serial_thread.data_received.connect(self.receive_message)
            self.serial_thread.start()
        else:
            print("Serial port not connected")

    def receive_message(self, message):
        # 接收到的訊息顯示在左側
        self.show_message(message, is_self=False)

    def create_message_label(self, text, is_self=True):
        # 建立訊息標籤
        message_label = QtWidgets.QLabel(text)
        message_label.setWordWrap(True)  # 啟用自動換行
        message_label.setMaximumWidth(500)  # 最大寬度設為500
        
        # 使用 sizeHint 取得文字實際所需寬度
        label_width = message_label.fontMetrics().boundingRect(text).width() + 40  # 加上padding
        
        # 如果文字寬度小於500，則使用實際寬度
        if label_width < 500:
            message_label.setMinimumWidth(min(label_width, 500))
        else:
            message_label.setMinimumWidth(100)  # 設定最小寬度避免過窄
        
        # 設定文字換行策略
        message_label.setTextFormat(Qt.AutoText)
        message_label.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        
        # 設定樣式
        style = """
            QLabel {
                background-color: #%s;
                border-radius: 10px;
                padding: 15px;
                margin: 5px;
                word-wrap: break-word;
                white-space: pre-wrap;
                line-height: 1.2;
                font-size: 14px;
            }
        """ % ("DCF8C6" if is_self else "FFFFFF")
        
        message_label.setStyleSheet(style)
        message_label.adjustSize()
        
        # 建立水平布局
        message_layout = QtWidgets.QHBoxLayout()
        message_layout.setContentsMargins(0, 0, 0, 0)
        
        if is_self:
            message_layout.addStretch()
            message_layout.addWidget(message_label)
        else:
            message_layout.addWidget(message_label)
            message_layout.addStretch()
        
        return message_layout

    def show_message(self, text, is_self=True):
        # 將訊息加入聊天區域
        message_layout = self.create_message_label(text, is_self)
        self.chat_content_layout.addLayout(message_layout)

    #聊天室到底部
    def scroll_to_bottom(self):
        self.chat_area.verticalScrollBar().setValue(self.chat_area.verticalScrollBar().maximum())

    '''
# 送訊息
    def send_message(self):
        message = self.send_area.toPlainText()
        if message:
            try:
                #message+="\n"
                self.serial_port.write(message.encode('UTF-8'))
                print(f"送出訊息-> {message}")
                #self.receive_area.setText(message)
                self.send_area.clear()
            except Exception as e:
                print(f"Error sending message: {e}")

# 清除訊息
    def clear_message(self):
        self.receive_area.clear()

# 接收訊息
    def start_listening(self):
        #self.serial_port = self.port_selector.currentText()
        if hasattr(self, 'serial_port') and self.serial_port.is_open:
            self.serial_thread = SerialReaderThread(self.serial_port)
            self.serial_thread.data_received.connect(self.display_data)
            self.serial_thread.start()
        else:
            print("Serial port not connected")

# 顯示資料
    def display_data(self, data):
            self.receive_area.append(data)
            print(f"接收訊息-> {data}")
    '''

# 檔案選單區
    def file_input_selected(self):
        self.clear_window()
        print("選擇檔案輸入模式")
        # 清除現有的中央元件
        old_widget = self.centralWidget()
        if (old_widget):
            old_widget.deleteLater()
        
        # 建立新的中央元件
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        
        # 建立主布局
        main_layout = QtWidgets.QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 檔案選擇區域
        file_section = QtWidgets.QGroupBox("檔案選擇")
        file_layout = QtWidgets.QHBoxLayout()
        file_section.setLayout(file_layout)
        
        # 檔案路徑顯示
        self.file_path = QtWidgets.QLineEdit()
        self.file_path.setReadOnly(True)
        self.file_path.setPlaceholderText("請選擇圖片...")
        self.file_path.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border-radius: 5px;
                border: 1px solid #ccc;
                font-size: 14px;
            }
        """)
        
        # 瀏覽按鈕
        browse_button = QtWidgets.QPushButton("瀏覽")
        browse_button.setFixedSize(100, 40)
        browse_button.setStyleSheet("""
            QPushButton {
                border-radius: 20px;
                background-color: #4CAF50;
                color: white;
                border: none;
                font-size: 14px
            }
        """)
        browse_button.clicked.connect(self.browse_image)
        
        # 圖片預覽區域
        self.image_preview = QtWidgets.QLabel()
        self.image_preview.setFixedSize(400, 300)
        self.image_preview.setAlignment(QtCore.Qt.AlignCenter)
        self.image_preview.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                border-radius: 10px;
                background-color: #f9f9f9;
            }
        """)
        
        # 添加到布局
        file_layout.addWidget(self.file_path)
        file_layout.addWidget(browse_button)
        main_layout.addWidget(file_section)
        main_layout.addWidget(self.image_preview)
        main_layout.addStretch()

# 瀏覽圖片
    def browse_image(self):
        # 設定支援的圖片格式
        image_formats = "圖片檔案 (*.png *.jpg *.jpeg *.bmp *.gif)"
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "選擇圖片",
            "",
            image_formats
        )
        if file_name:
            self.file_path.setText(file_name)
            # 載入並顯示圖片預覽
            pixmap = QtGui.QPixmap(file_name)
            # 保持圖片比例並適應預覽區域大小
            scaled_pixmap = pixmap.scaled(
                self.image_preview.size(),
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation
            )
            self.image_preview.setPixmap(scaled_pixmap)

# 更新可用序列埠列表
    def update_ports(self):
        self.port_combo.clear()
        ports = [port.device for port in serial.tools.list_ports.comports()]
        # 設置下拉選單樣式
        self.port_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #ccc;
                border-radius: 10px;
                padding: 5px;
                min-width: 150px;
                height: 30px;
                font-size: 16px;
                font-family: "Microsoft YaHei", "微軟正黑體";
                background-color: white;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #ccc;
                border-radius: 5px;
                selection-background-color: #4CAF50;
                selection-color: white;
            }
        """)
        
        # 如果沒有可用序列埠，添加提示文字
        if not ports:
            self.port_combo.addItem("未找到可用序列埠")
            print("未找到可用序列埠")
        else:
            self.port_combo.addItems(ports)
            print("可用序列埠列表:", ports)

#刷新串列埠清單
    def refresh_ports(self):
            
            self.port_combo.clear()
            ports = serial.tools.list_ports.comports()
            for port in ports:
                self.port_combo.addItem(port.device)

# 切換序列埠連接狀態
    def toggle_connection(self):
        if self.serial_port is None:  # 未連接狀態
            try:
                selected_port = self.port_combo.currentText()
                self.serial_port = serial.Serial(selected_port,serial_baud)
                #self.serial_port=selected_port
                self.connect_button.setText("斷開")
                self.connect_button.setStyleSheet("""
                    QPushButton {
                        border-radius: 20px;
                        background-color: #ff0000;
                        color: white;
                        border: none;
                        font-family: "Microsoft YaHei", "微軟正黑體";
                        font-size: 16px
                    }
                    QPushButton:hover {
                        background-color: #dc143c;
                    }
                """)
                self.port_combo.setEnabled(False)
                print("我連上的酷東西", selected_port)
                self.connect_check=True
                print(self.serial_port,serial_baud)
                #ser = serial.Serial(serial_port, serial_baud)

            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "錯誤", f"無法連接到序列埠: {str(e)}")
                self.serial_port = None
        else:  # 已連接狀態
            self.serial_port.close()
            self.serial_port = None
            self.connect_button.setText("連接")
            self.connect_button.setStyleSheet("""
                    QPushButton {
                        border-radius: 20px;
                        background-color: #4CAF50;
                        color: white;
                        border: none;
                        font-family: "Microsoft YaHei", "微軟正黑體";
                        font-size: 16px
                    }
                """)
            self.port_combo.setEnabled(True)
            self.connect_check=False
            print("已斷開序列埠連接")

#清除視窗
    def clear_window(self):
        self.setStyleSheet("")
        self.menuBar().clear()
        # 建立選單列
        menubar = self.menuBar()
        input_menu = menubar.addMenu('頁面選擇')
        
        # 首頁
        home_index_action = QtWidgets.QAction('回首頁', self)
        home_index_action.triggered.connect(self.home_index_selected)

        # 文字輸入
        text_input_action = QtWidgets.QAction('文字輸入', self)
        text_input_action.triggered.connect(self.text_input_selected)
        
        # 檔案輸入
        file_input_action = QtWidgets.QAction('檔案輸入', self)
        file_input_action.triggered.connect(self.file_input_selected)
        
        # 將動作加入選單
        input_menu.addAction(home_index_action)
        input_menu.addSeparator()   # 分隔線
        input_menu.addAction(text_input_action)
        input_menu.addAction(file_input_action)



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())