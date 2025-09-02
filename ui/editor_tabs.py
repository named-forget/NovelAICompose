# -*- coding: utf-8 -*-

import os
from PyQt5.QtWidgets import (QTabWidget, QMessageBox, QWidget, QVBoxLayout)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon

from .text_editor import TextEditor


class EditorTabs(QTabWidget):
    tab_closed = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.editors = {}  # file_path -> editor
        
        # 设置标签页属性
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDocumentMode(True)
        
        # 连接信号
        self.tabCloseRequested.connect(self.close_tab)
        self.currentChanged.connect(self.on_tab_changed)
        
        # 创建空白页面
        self.show_welcome_page()
        
    def show_welcome_page(self):
        """显示欢迎页面"""
        welcome_widget = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        from PyQt5.QtWidgets import QLabel
        label = QLabel("欢迎使用 Novel AI Composer\n\n打开文件夹开始编辑")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 16px; color: #666;")
        layout.addWidget(label)
        
        welcome_widget.setLayout(layout)
        self.addTab(welcome_widget, "欢迎")
        
    def open_file(self, file_path):
        """打开文件"""
        # 检查文件是否已经打开
        if file_path in self.editors:
            # 切换到已打开的标签
            for i in range(self.count()):
                if self.widget(i) == self.editors[file_path]:
                    self.setCurrentIndex(i)
                    return
                    
        # 移除欢迎页面
        if self.count() == 1 and isinstance(self.widget(0), QWidget) and self.tabText(0) == "欢迎":
            self.removeTab(0)
            
        # 创建新的编辑器
        editor = TextEditor(self.parent_window)
        editor.file_path = file_path
        
        # 读取文件内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            editor.setPlainText(content)
            editor.document().setModified(False)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开文件: {str(e)}")
            return
            
        # 添加到标签页
        file_name = os.path.basename(file_path)
        index = self.addTab(editor, file_name)
        self.setCurrentIndex(index)
        
        # 保存编辑器引用
        self.editors[file_path] = editor
        
        # 连接修改信号
        editor.textChanged.connect(lambda: self.on_text_changed(editor))
        
    def close_tab(self, index):
        """关闭标签页"""
        widget = self.widget(index)
        
        # 如果是欢迎页面，直接关闭
        if isinstance(widget, QWidget) and self.tabText(index) == "欢迎":
            self.removeTab(index)
            return
            
        # 如果是编辑器，检查是否需要保存
        if isinstance(widget, TextEditor):
            if widget.document().isModified():
                reply = QMessageBox.question(
                    self, "保存文件",
                    f"文件 '{os.path.basename(widget.file_path)}' 已修改，是否保存?",
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
                )
                
                if reply == QMessageBox.Save:
                    self.save_file(widget)
                elif reply == QMessageBox.Cancel:
                    return
                    
            # 从字典中移除
            if widget.file_path in self.editors:
                del self.editors[widget.file_path]
                
        self.removeTab(index)
        self.tab_closed.emit(index)
        
        # 如果没有标签页了，显示欢迎页面
        if self.count() == 0:
            self.show_welcome_page()
            
    def save_file(self, editor):
        """保存文件"""
        try:
            with open(editor.file_path, 'w', encoding='utf-8') as f:
                f.write(editor.toPlainText())
            editor.document().setModified(False)
            
            # 更新标签页标题
            index = self.indexOf(editor)
            if index != -1:
                self.setTabText(index, os.path.basename(editor.file_path))
                
            return True
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存文件失败: {str(e)}")
            return False
            
    def save_current_file(self):
        """保存当前文件"""
        current_widget = self.currentWidget()
        if isinstance(current_widget, TextEditor):
            return self.save_file(current_widget)
        return True
        
    def save_all_files(self):
        """保存所有文件"""
        for editor in self.editors.values():
            if editor.document().isModified():
                if not self.save_file(editor):
                    return False
        return True
        
    def on_text_changed(self, editor):
        """文本改变时的处理"""
        index = self.indexOf(editor)
        if index != -1:
            file_name = os.path.basename(editor.file_path)
            if editor.document().isModified():
                self.setTabText(index, f"{file_name} *")
            else:
                self.setTabText(index, file_name)
                
    def on_tab_changed(self, index):
        """标签页切换时的处理"""
        widget = self.widget(index)
        if isinstance(widget, TextEditor):
            widget.setFocus()
            
    def current_editor_action(self, action):
        """当前编辑器执行动作"""
        current_widget = self.currentWidget()
        if isinstance(current_widget, TextEditor):
            if action == 'undo':
                current_widget.undo()
            elif action == 'redo':
                current_widget.redo()
            elif action == 'cut':
                current_widget.cut()
            elif action == 'copy':
                current_widget.copy()
            elif action == 'paste':
                current_widget.paste()
                
    def get_open_files(self):
        """获取所有打开的文件路径"""
        return list(self.editors.keys())
        
    def get_active_file(self):
        """获取当前活动的文件路径"""
        current_widget = self.currentWidget()
        if isinstance(current_widget, TextEditor):
            return current_widget.file_path
        return None
        
    def set_active_file(self, file_path):
        """设置活动文件"""
        if file_path in self.editors:
            editor = self.editors[file_path]
            index = self.indexOf(editor)
            if index != -1:
                self.setCurrentIndex(index)
