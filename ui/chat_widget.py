# -*- coding: utf-8 -*-

import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
                             QPushButton, QCompleter, QListWidget,
                             QListWidgetItem, QStyledItemDelegate, QApplication)
from PyQt5.QtCore import Qt, pyqtSignal, QStringListModel
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QTextCursor

from core.ai_handler import AIHandler


class ChatInput(QTextEdit):
    """自定义文本输入框，用于处理Enter和Shift+Enter"""
    returnPressed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("输入消息... (Shift+Enter 换行)")
        self.setFixedHeight(100)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if QApplication.keyboardModifiers() == Qt.ShiftModifier:
                super().keyPressEvent(event)
            else:
                self.returnPressed.emit()
        else:
            super().keyPressEvent(event)


class ChatWidget(QWidget):
    """聊天窗口"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.ai_handler = AIHandler(parent.work_dir if parent else None)
        self.history = []
        self.is_ai_streaming = False
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 聊天记录显示
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        layout.addWidget(self.chat_history)
        
        # 输入框和发送按钮
        input_layout = QHBoxLayout()
        
        self.input_box = ChatInput()
        self.input_box.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_box)
        
        send_button = QPushButton("发送")
        send_button.clicked.connect(self.send_message)
        input_layout.addWidget(send_button)
        
        layout.addLayout(input_layout)
        self.setLayout(layout)
        
        # 设置@符号补全
        self.setup_completer()
        
    def setup_completer(self):
        """设置@符号补全"""
        self.completer = QCompleter(self)
        self.completer_model = QStringListModel()
        self.completer.setModel(self.completer_model)
        self.completer.setWidget(self.input_box)
        self.completer.activated.connect(self.insert_completion)
        
        self.input_box.textChanged.connect(self.on_text_changed)
        
    def on_text_changed(self):
        """输入框文本改变时的处理"""
        cursor = self.input_box.textCursor()
        text_until_cursor = self.input_box.toPlainText()[:cursor.position()]

        last_at = text_until_cursor.rfind('@')
        if last_at == -1:
            self.completer.popup().hide()
            return

        prefix = text_until_cursor[last_at + 1:]

        if ' ' in prefix or '\n' in prefix:
            self.completer.popup().hide()
            return
        
        # 更新补全列表
        self.update_completion_list(prefix)
        
        if self.completer.model().rowCount() > 0:
            # 显示补全
            self.completer.setCompletionPrefix(prefix)
            cr = self.input_box.cursorRect()
            self.completer.complete(cr)
        else:
            self.completer.popup().hide()

    def insert_completion(self, completion):
        """插入补全内容"""
        cursor = self.input_box.textCursor()
        text_until_cursor = self.input_box.toPlainText()[:cursor.position()]
        last_at = text_until_cursor.rfind('@')
        prefix_len = len(text_until_cursor) - (last_at + 1)

        cursor.movePosition(QTextCursor.PreviousCharacter, QTextCursor.KeepAnchor, prefix_len)
        cursor.insertText(completion)
        self.input_box.setTextCursor(cursor)
            
    def update_completion_list(self, prefix):
        """更新补全列表"""
        items = []
        
        # 添加特殊指令
        special_commands = ["选中内容", "正在编辑"]
        items.extend(special_commands)
        
        # 添加文件列表
        if self.parent_window and self.parent_window.file_tree.root_path:
            root_path = self.parent_window.file_tree.root_path
            for root, _, files in os.walk(root_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, root_path)
                    items.append(relative_path)
                    
        self.completer_model.setStringList(items)
        
    def send_message(self):
        """发送消息"""
        message = self.input_box.toPlainText().strip()
        if not message:
            return
            
        # 将用户消息添加到历史记录
        self.add_message("You", message)
        QApplication.processEvents()
        self.history.append({"role": "user", "content": message})
        self.input_box.clear()
        
        # 处理@符号
        context = self.process_at_mentions(message)
        
        # 准备发送给AI的消息
        ai_messages = self.history.copy()
        if context:
            ai_messages[-1]["content"] = f"{context}\n\n{message}"
            
        # 调用AI
        self.call_ai(ai_messages)
        
    def process_at_mentions(self, message):
        """处理@符号"""
        context = ""
        if '@' in message:
            parts = message.split('@')
            for part in parts[1:]:
                item = part.split(' ')[0]
                
                if item == "选中内容":
                    editor = self.parent_window.editor_tabs.currentWidget()
                    if editor and editor.textCursor().hasSelection():
                        context += f"--- 选中内容 ---\n{editor.textCursor().selectedText()}\n\n"
                        
                elif item == "正在编辑":
                    editor = self.parent_window.editor_tabs.currentWidget()
                    if editor:
                        context += f"--- 正在编辑的文件: {os.path.basename(editor.file_path)} ---\n{editor.toPlainText()}\n\n"
                        
                else:
                    # 尝试作为文件路径处理
                    if self.parent_window and self.parent_window.file_tree.root_path:
                        file_path = os.path.join(self.parent_window.file_tree.root_path, item)
                        if os.path.exists(file_path):
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    context += f"--- 文件内容: {item} ---\n{f.read()}\n\n"
                            except Exception as e:
                                print(f"读取文件失败: {e}")
                                
        return context
        
    def call_ai(self, messages):
        """调用AI"""
        try:
            self.chat_history.moveCursor(QTextCursor.End)
            self.chat_history.insertHtml("<br><b>AI:</b> ")
            self.is_ai_streaming = True
            response_text = ""
            for chunk in self.ai_handler.chat(messages):
                response_text += chunk
                self.update_ai_message(chunk)
                QApplication.processEvents()
                
            self.history.append({"role": "assistant", "content": response_text})
            self.chat_history.append("")
            
        except Exception as e:
            self.add_message("AI", f"错误: {str(e)}")
        finally:
            self.is_ai_streaming = False
            
    def add_message(self, sender, message):
        """添加消息到聊天记录"""
        self.chat_history.append(f"<b>{sender}:</b> {message}")
        
    def update_ai_message(self, message):
        """更新AI消息"""
        self.chat_history.moveCursor(QTextCursor.End)
        self.chat_history.insertPlainText(message)
        self.chat_history.ensureCursorVisible()
