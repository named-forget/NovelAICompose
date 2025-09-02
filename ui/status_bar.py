# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QStatusBar, QLabel, QPushButton, QWidget,
                             QHBoxLayout)
from PyQt5.QtCore import Qt


class StatusBar(QStatusBar):
    """自定义状态栏"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        
        # AI进度显示
        self.ai_progress_widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.char_count_label = QLabel("生成字符数: 0")
        layout.addWidget(self.char_count_label)
        
        self.stop_button = QPushButton("终止")
        self.stop_button.clicked.connect(self.stop_ai_generation)
        layout.addWidget(self.stop_button)
        
        self.ai_progress_widget.setLayout(layout)
        
        self.addPermanentWidget(self.ai_progress_widget)
        self.ai_progress_widget.hide()
        
        self.char_count = 0
        
    def show_ai_progress(self):
        """显示AI进度"""
        self.char_count = 0
        self.char_count_label.setText("生成字符数: 0")
        self.ai_progress_widget.show()
        
    def hide_ai_progress(self):
        """隐藏AI进度"""
        self.ai_progress_widget.hide()
        
    def update_char_count(self, count):
        """更新字符数"""
        self.char_count += count
        self.char_count_label.setText(f"生成字符数: {self.char_count}")
        
    def stop_ai_generation(self):
        """停止AI生成"""
        if self.parent_window:
            editor = self.parent_window.editor_tabs.currentWidget()
            if editor:
                editor.stop_ai_generation()
