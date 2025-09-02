# -*- coding: utf-8 -*-

import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QWidget, QLabel, QLineEdit, QPushButton,
                             QTextEdit, QFormLayout, QMessageBox, QComboBox,
                             QKeySequenceEdit, QScrollArea)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence

from core.ai_handler import AIHandler
from core.shortcut_manager import ShortcutManager


class SettingsDialog(QDialog):
    def __init__(self, parent=None, work_dir=None):
        super().__init__(parent)
        self.parent_window = parent
        self.work_dir = work_dir
        self.ai_handler = AIHandler(work_dir)
        self.shortcut_manager = ShortcutManager(work_dir)
        
        self.setWindowTitle("设置")
        self.setModal(True)
        self.resize(600, 500)
        
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 外观设置标签页
        appearance_tab = self.create_appearance_tab()
        self.tab_widget.addTab(appearance_tab, "外观")
        
        # API设置标签页
        api_tab = self.create_api_tab()
        self.tab_widget.addTab(api_tab, "API设置")
        
        # 提示词设置标签页
        prompts_tab = self.create_prompts_tab()
        self.tab_widget.addTab(prompts_tab, "提示词设置")
        
        # 快捷键设置标签页
        shortcuts_tab = self.create_shortcuts_tab()
        self.tab_widget.addTab(shortcuts_tab, "快捷键")
        
        layout.addWidget(self.tab_widget)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_button = QPushButton("保存")
        save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def create_appearance_tab(self):
        """创建外观设置标签页"""
        widget = QWidget()
        layout = QFormLayout()
        
        # 主题选择
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["暗色主题", "亮色主题"])
        layout.addRow("主题:", self.theme_combo)
        
        widget.setLayout(layout)
        return widget
        
    def create_api_tab(self):
        """创建API设置标签页"""
        widget = QWidget()
        layout = QFormLayout()
        
        # API Key
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setPlaceholderText("请输入OpenAI API Key")
        layout.addRow("API Key:", self.api_key_edit)
        
        # Base URL
        self.base_url_edit = QLineEdit()
        self.base_url_edit.setPlaceholderText("https://api.openai.com/v1")
        layout.addRow("Base URL:", self.base_url_edit)
        
        # Model
        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText("gpt-3.5-turbo")
        layout.addRow("模型名称:", self.model_edit)
        
        # 添加说明
        info_label = QLabel(
            "说明：\n"
            "1. API Key: 您的OpenAI API密钥\n"
            "2. Base URL: API端点地址，默认为OpenAI官方地址\n"
            "3. 模型名称: 使用的模型，如gpt-3.5-turbo, gpt-4等"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; margin-top: 20px;")
        layout.addRow(info_label)
        
        widget.setLayout(layout)
        return widget
        
    def create_prompts_tab(self):
        """创建提示词设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 续写提示词
        layout.addWidget(QLabel("续写提示词:"))
        self.continue_prompt_edit = QTextEdit()
        self.continue_prompt_edit.setMaximumHeight(80)
        self.continue_prompt_edit.setPlaceholderText("使用 {context} 和 {setting} 作为占位符")
        layout.addWidget(self.continue_prompt_edit)
        
        # 扩写提示词
        layout.addWidget(QLabel("扩写提示词:"))
        self.expand_prompt_edit = QTextEdit()
        self.expand_prompt_edit.setMaximumHeight(80)
        self.expand_prompt_edit.setPlaceholderText("使用 {context} 和 {setting} 作为占位符")
        layout.addWidget(self.expand_prompt_edit)
        
        # 缩写提示词
        layout.addWidget(QLabel("缩写提示词:"))
        self.summarize_prompt_edit = QTextEdit()
        self.summarize_prompt_edit.setMaximumHeight(80)
        self.summarize_prompt_edit.setPlaceholderText("使用 {context} 和 {setting} 作为占位符")
        layout.addWidget(self.summarize_prompt_edit)
        
        # 自定义指令提示词
        layout.addWidget(QLabel("自定义指令提示词:"))
        self.custom_prompt_edit = QTextEdit()
        self.custom_prompt_edit.setMaximumHeight(80)
        self.custom_prompt_edit.setPlaceholderText("使用 {context}, {prompt} 和 {setting} 作为占位符")
        layout.addWidget(self.custom_prompt_edit)
        
        # 添加说明
        info_label = QLabel(
            "说明：\n"
            "在提示词中使用 {context}, {prompt}, {setting} 作为占位符。\n"
            "{context} 将被替换为上下文或选中文本。\n"
            "{prompt} 将被替换为自定义指令的输入内容。\n"
            "{setting} 将被替换为“设定”目录中所有文件的内容汇总。"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; margin-top: 20px;")
        layout.addWidget(info_label)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
        
    def create_shortcuts_tab(self):
        """创建快捷键设置标签页"""
        widget = QWidget()
        layout = QFormLayout()
        layout.setRowWrapPolicy(QFormLayout.WrapAllRows)
        
        self.shortcut_edits = {}
        
        # 定义快捷键名称和描述
        shortcut_map = {
            'open_folder': '打开文件夹',
            'save_file': '保存文件',
            'save_all_files': '保存所有文件',
            'exit_app': '退出程序',
            'undo': '撤销',
            'redo': '重做',
            'cut': '剪切',
            'copy': '复制',
            'paste': '粘贴',
            'ai_continue': 'AI续写',
            'ai_expand': 'AI扩写',
            'ai_summarize': 'AI缩写',
            'ai_custom': 'AI自定义指令',
            'toggle_chat': '切换聊天窗口'
        }
        
        for name, description in shortcut_map.items():
            key_edit = QKeySequenceEdit()
            layout.addRow(description, key_edit)
            self.shortcut_edits[name] = key_edit
            
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(widget)
        
        widget.setLayout(layout)
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll_area)
        
        container = QWidget()
        container.setLayout(main_layout)
        
        return container
        
    def load_settings(self):
        """加载设置"""
        # 外观设置
        theme = self.parent_window.settings.value("theme", "dark")
        if theme == "light":
            self.theme_combo.setCurrentIndex(1)
        else:
            self.theme_combo.setCurrentIndex(0)
            
        # API设置
        config = self.ai_handler.config
        self.api_key_edit.setText(config.get('api_key', ''))
        self.base_url_edit.setText(config.get('base_url', 'https://api.openai.com/v1'))
        self.model_edit.setText(config.get('model', 'gpt-3.5-turbo'))
        
        # 提示词设置
        prompts = config.get('prompts', {})
        self.continue_prompt_edit.setPlainText(
            prompts.get('continue', '## 设定\n{setting}\n请根据上文内容和小说设定，继续写作，保持风格和语气一致：\n\n{context}')
        )
        self.expand_prompt_edit.setPlainText(
            prompts.get('expand', '## 设定\n{setting}\n请将以下内容进行扩写，增加更多细节和描述，但保持原意不变：\n\n{context}')
        )
        self.summarize_prompt_edit.setPlainText(
            prompts.get('summarize', '请将以下内容进行缩写，保留核心信息，使其更加简洁：\n\n{context}')
        )
        self.custom_prompt_edit.setPlainText(
            prompts.get('custom', '{prompt}\n\n文本内容：\n{context}')
        )
        
        # 快捷键设置
        for name, key_edit in self.shortcut_edits.items():
            key_sequence = self.shortcut_manager.get_qkeysequence(name)
            key_edit.setKeySequence(key_sequence)
        
    def save_settings(self):
        """保存设置"""
        # 验证必填项
        if not self.api_key_edit.text().strip():
            QMessageBox.warning(self, "警告", "请输入API Key")
            return
            
        if not self.base_url_edit.text().strip():
            QMessageBox.warning(self, "警告", "请输入Base URL")
            return
            
        if not self.model_edit.text().strip():
            QMessageBox.warning(self, "警告", "请输入模型名称")
            return
            
        # 保存外观设置
        theme = "dark" if self.theme_combo.currentIndex() == 0 else "light"
        self.parent_window.settings.setValue("theme", theme)
        
        # 更新配置
        self.ai_handler.config['api_key'] = self.api_key_edit.text().strip()
        self.ai_handler.config['base_url'] = self.base_url_edit.text().strip()
        self.ai_handler.config['model'] = self.model_edit.text().strip()
        
        self.ai_handler.config['prompts'] = {
            'continue': self.continue_prompt_edit.toPlainText(),
            'expand': self.expand_prompt_edit.toPlainText(),
            'summarize': self.summarize_prompt_edit.toPlainText(),
            'custom': self.custom_prompt_edit.toPlainText()
        }
        
        # 保存快捷键设置
        for name, key_edit in self.shortcut_edits.items():
            self.shortcut_manager.set_shortcut(name, key_edit.keySequence().toString())
        self.shortcut_manager.save_shortcuts()
        
        # 保存配置
        self.ai_handler.save_config()
        
        QMessageBox.information(self, "成功", "设置已保存，部分设置需要重启生效")
        self.accept()
