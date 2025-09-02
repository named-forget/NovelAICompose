# -*- coding: utf-8 -*-

import os
from PyQt5.QtWidgets import (QPlainTextEdit, QMenu, QAction, QWidget,
                             QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTextEdit, QInputDialog, QLineEdit)
from PyQt5.QtCore import Qt, QPoint, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QTextCursor, QFont, QTextCharFormat, QColor

from core.ai_handler import AIHandler, AIWorker


class FloatingMenu(QWidget):
    """浮动菜单"""
    expand_clicked = pyqtSignal()
    summarize_clicked = pyqtSignal()
    custom_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        
        # 创建布局
        layout = QHBoxLayout()
        layout.setObjectName("FloatingMenu")
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        
        # 创建按钮
        expand_btn = QPushButton("扩写")
        expand_btn.clicked.connect(self.expand_clicked.emit)
        layout.addWidget(expand_btn)
        
        summarize_btn = QPushButton("缩写")
        summarize_btn.clicked.connect(self.summarize_clicked.emit)
        layout.addWidget(summarize_btn)
        
        custom_btn = QPushButton("自定义指令")
        custom_btn.clicked.connect(self.custom_clicked.emit)
        layout.addWidget(custom_btn)
        
        self.setLayout(layout)
        
    def show_at_position(self, pos):
        """在指定位置显示"""
        self.move(pos)
        self.show()
        self.raise_()


class TextEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.file_path = None
        self.auto_save_timer = QTimer()
        self.floating_menu = FloatingMenu(self)
        
        self.continue_button = QPushButton("续写", self)
        self.continue_button.setObjectName("ContinueButton")
        self.continue_button.hide()
        self.continue_button.clicked.connect(lambda: self.ai_action('continue'))
        
        self.ai_handler = AIHandler(parent.work_dir if parent else None)
        self.ai_worker = None
        self.ai_thread = None
        
        self.continue_writing_timer = QTimer(self)
        self.continue_writing_timer.setSingleShot(True)
        self.continue_writing_timer.setInterval(2000)  # 2秒
        
        # 设置编辑器属性
        self.setFont(QFont("Consolas", 11))
        self.setTabStopWidth(40)
        
        # 设置自动保存
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.setInterval(1000)  # 1秒后自动保存
        
        # 连接信号
        self.textChanged.connect(self.on_text_changed)
        self.continue_writing_timer.timeout.connect(self.show_continue_button)
        self.selectionChanged.connect(self.on_selection_changed)
        self.floating_menu.expand_clicked.connect(lambda: self.ai_action('expand'))
        self.floating_menu.summarize_clicked.connect(lambda: self.ai_action('summarize'))
        self.floating_menu.custom_clicked.connect(lambda: self.ai_action('custom'))
        
        # AI生成位置标记
        self.ai_insert_position = None
        
        # 设置快捷键
        self.setup_shortcuts()
        
    def setup_shortcuts(self):
        """设置快捷键"""
        if not self.parent_window:
            return
        
        shortcut_manager = self.parent_window.shortcut_manager
        
        continue_action = QAction(self)
        continue_action.setShortcut(shortcut_manager.get_qkeysequence('ai_continue'))
        continue_action.triggered.connect(lambda: self.ai_action('continue'))
        self.addAction(continue_action)
            
    def focusOutEvent(self, event):
        """失去焦点时自动保存"""
        super().focusOutEvent(event)
        if self.document().isModified() and self.file_path:
            self.auto_save_timer.start()
            
    def focusInEvent(self, event):
        """获得焦点时停止自动保存计时器"""
        super().focusInEvent(event)
        self.auto_save_timer.stop()
        self.floating_menu.hide()
        self.continue_button.hide()
        
    def save_file(self):
        """保存当前文件"""
        if self.file_path and self.document().isModified():
            try:
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    f.write(self.toPlainText())
                self.document().setModified(False)
                
                # 更新标签页标题
                if self.parent_window:
                    tabs = self.parent_window.editor_tabs
                    index = tabs.indexOf(self)
                    if index != -1:
                        tabs.setTabText(index, os.path.basename(self.file_path))
                        
            except Exception as e:
                print(f"保存文件失败: {e}")

    def auto_save(self):
        """自动保存"""
        self.auto_save_timer.stop()
        self.save_file()
                
    def on_text_changed(self):
        """文本改变时重置续写计时器"""
        self.continue_button.hide()
        self.continue_writing_timer.start()

    def show_continue_button(self):
        """显示续写按钮"""
        if self.toPlainText().strip() == "":
            return
            
        cursor = self.textCursor()
        cursor_rect = self.cursorRect(cursor)
        
        pos = cursor_rect.bottomRight()
        self.continue_button.move(pos.x(), pos.y() + 5)
        self.continue_button.show()
        self.continue_button.raise_()
        
    def on_selection_changed(self):
        """选择文本改变时的处理"""
        cursor = self.textCursor()
        if cursor.hasSelection():
            # 获取选中文本的位置
            cursor_rect = self.cursorRect(cursor)
            global_pos = self.mapToGlobal(cursor_rect.bottomRight())
            
            # 调整位置，避免遮挡文本
            global_pos.setY(global_pos.y() + 5)
            
            # 显示浮动菜单
            self.floating_menu.show_at_position(global_pos)
        else:
            self.floating_menu.hide()
            
    def ai_action(self, action):
        """执行AI动作"""
        cursor = self.textCursor()
        
        if action == 'continue':
            self.continue_button.hide()
            # 续写：获取所有文本作为上下文
            context = self.toPlainText()
            
            # 移动到文档末尾
            cursor.movePosition(QTextCursor.End)
            self.ai_insert_position = cursor.position()
            
        elif action in ['expand', 'summarize', 'custom']:
            # 扩写/缩写/自定义：获取选中的文本
            if not cursor.hasSelection():
                return
                
            context = cursor.selectedText()
            self.ai_insert_position = cursor.position()
            
            # 如果是自定义指令，弹出输入框
            if action == 'custom':
                prompt, ok = QInputDialog.getText(
                    self, "自定义指令", 
                    "请输入指令（将应用于选中的文本）:",
                    QLineEdit.Normal
                )
                if not ok or not prompt:
                    return
                # 保存自定义指令
                self.custom_prompt = prompt
                
            # 删除选中的文本（将被AI生成的内容替换）
            cursor.removeSelectedText()
            
        # 隐藏浮动菜单
        self.floating_menu.hide()
        
        # 设置光标到插入位置
        cursor.setPosition(self.ai_insert_position)
        self.setTextCursor(cursor)
        
        # 更新状态栏
        if self.parent_window:
            self.parent_window.status_bar.show_ai_progress()
        
        # 创建并启动AI工作线程
        self.ai_thread = QThread()
        self.ai_worker = AIWorker(self.ai_handler, action, context)
        if action == 'custom':
            self.ai_worker.custom_prompt = self.custom_prompt
        self.ai_worker.moveToThread(self.ai_thread)
        
        # 连接信号
        self.ai_thread.started.connect(self.ai_worker.run)
        self.ai_worker.chunk_received.connect(self.on_ai_chunk_received)
        self.ai_worker.finished.connect(self.on_ai_finished)
        self.ai_worker.error.connect(self.on_ai_error)
        
        # 启动线程
        self.ai_thread.start()
        
    def on_ai_chunk_received(self, chunk):
        """接收AI生成的文本块"""
        cursor = self.textCursor()
        cursor.setPosition(self.ai_insert_position)
        
        # 插入文本
        cursor.insertText(chunk)
        
        # 更新插入位置
        self.ai_insert_position = cursor.position()
        
        # 确保文本可见
        self.setTextCursor(cursor)
        self.ensureCursorVisible()
        
        # 更新状态栏字符数
        if self.parent_window:
            self.parent_window.status_bar.update_char_count(len(chunk))
        
    def on_ai_finished(self):
        """AI生成完成"""
        if self.ai_thread:
            self.ai_thread.quit()
            self.ai_thread.wait()
            self.ai_thread = None
        self.ai_worker = None
        
        # 隐藏状态栏进度
        if self.parent_window:
            self.parent_window.status_bar.hide_ai_progress()
        
    def on_ai_error(self, error_msg):
        """AI生成错误"""
        print(f"AI生成错误: {error_msg}")
        self.on_ai_finished()
        
        # 在状态栏显示错误
        if self.parent_window:
            self.parent_window.status_bar.showMessage(f"AI生成失败: {error_msg}", 5000)
            
    def stop_ai_generation(self):
        """停止AI生成"""
        if self.ai_worker:
            self.ai_worker.stop()
            
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        super().mousePressEvent(event)
        # 点击时隐藏浮动菜单
        if not self.floating_menu.geometry().contains(event.globalPos()):
            self.floating_menu.hide()
        if not self.continue_button.geometry().contains(event.pos()):
            self.continue_button.hide()
