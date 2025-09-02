# -*- coding: utf-8 -*-

import os
import json
from PyQt5.QtWidgets import (QMainWindow, QSplitter, QVBoxLayout, QWidget,
                             QMenuBar, QMenu, QAction, QFileDialog, QTabWidget,
                             QMessageBox, QDockWidget, QToolBar)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QIcon

from .file_tree import FileTreeWidget
from .editor_tabs import EditorTabs
from .settings_dialog import SettingsDialog
from .styles import get_vscode_dark_style, get_vscode_light_style
from .chat_widget import ChatWidget
from .status_bar import StatusBar
from core.state_manager import StateManager
from core.shortcut_manager import ShortcutManager


class MainWindow(QMainWindow):
    def __init__(self, work_dir):
        super().__init__()
        self.work_dir = work_dir
        self.state_manager = StateManager(work_dir)
        self.settings = QSettings("NovelAI", "NovelAIComposer")
        self.shortcut_manager = ShortcutManager(work_dir)
        
        self.init_ui()
        self.load_state()
        
    def init_ui(self):
        self.setWindowTitle("Novel AI Composer")
        self.setWindowIcon(QIcon("logo.ico"))
        self.setGeometry(100, 100, 1200, 800)
        
        # 应用主题
        self.apply_theme()
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主分割器
        self.main_splitter = QSplitter(Qt.Horizontal)

        # 目录树
        self.file_tree = FileTreeWidget(self)
        self.main_splitter.addWidget(self.file_tree)

        # 编辑器
        self.editor_tabs = EditorTabs(self)
        self.main_splitter.addWidget(self.editor_tabs)
        
        # 对话框
        self.chat_widget = ChatWidget(self)
        self.main_splitter.addWidget(self.chat_widget)

        # 设置初始分割比例
        self.main_splitter.setSizes([200, 600, 400])

        # 创建左侧导航栏
        self.create_nav_bar()
        
        # 设置布局
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.main_splitter)
        central_widget.setLayout(layout)
        
        # 状态栏
        self.status_bar = StatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        
        # 连接信号
        self.file_tree.file_opened.connect(self.open_file)
        self.editor_tabs.tab_closed.connect(self.on_tab_closed)

    def create_nav_bar(self):
        """创建左侧导航栏"""
        self.nav_bar = QToolBar("Navigation")
        self.nav_bar.setMovable(False)
        self.addToolBar(Qt.LeftToolBarArea, self.nav_bar)

        # 文件树切换按钮
        self.toggle_file_tree_action = QAction(QIcon(), "文件", self)
        self.toggle_file_tree_action.setCheckable(True)
        self.toggle_file_tree_action.setChecked(True)
        self.toggle_file_tree_action.triggered.connect(self.toggle_file_tree)
        self.nav_bar.addAction(self.toggle_file_tree_action)

    def toggle_file_tree(self):
        """切换文件树的可见性"""
        if self.file_tree.isVisible():
            self.file_tree.hide()
        else:
            self.file_tree.show()
        
    def apply_theme(self):
        """应用主题"""
        theme = self.settings.value("theme", "dark")
        if theme == "light":
            self.setStyleSheet(get_vscode_light_style())
        else:
            self.setStyleSheet(get_vscode_dark_style())
            
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件(&F)')
        
        open_folder_action = QAction('打开文件夹(&O)', self)
        open_folder_action.setShortcut(self.shortcut_manager.get_qkeysequence('open_folder'))
        open_folder_action.triggered.connect(self.open_folder)
        file_menu.addAction(open_folder_action)
        
        file_menu.addSeparator()
        
        save_action = QAction('保存(&S)', self)
        save_action.setShortcut(self.shortcut_manager.get_qkeysequence('save_file'))
        save_action.triggered.connect(self.save_current_file)
        file_menu.addAction(save_action)
        
        save_all_action = QAction('保存所有(&A)', self)
        save_all_action.setShortcut(self.shortcut_manager.get_qkeysequence('save_all_files'))
        save_all_action.triggered.connect(self.save_all_files)
        file_menu.addAction(save_all_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('退出(&X)', self)
        exit_action.setShortcut(self.shortcut_manager.get_qkeysequence('exit_app'))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu('编辑(&E)')
        
        undo_action = QAction('撤销(&U)', self)
        undo_action.setShortcut(self.shortcut_manager.get_qkeysequence('undo'))
        undo_action.triggered.connect(lambda: self.editor_tabs.current_editor_action('undo'))
        edit_menu.addAction(undo_action)
        
        redo_action = QAction('重做(&R)', self)
        redo_action.setShortcut(self.shortcut_manager.get_qkeysequence('redo'))
        redo_action.triggered.connect(lambda: self.editor_tabs.current_editor_action('redo'))
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        cut_action = QAction('剪切(&T)', self)
        cut_action.setShortcut(self.shortcut_manager.get_qkeysequence('cut'))
        cut_action.triggered.connect(lambda: self.editor_tabs.current_editor_action('cut'))
        edit_menu.addAction(cut_action)
        
        copy_action = QAction('复制(&C)', self)
        copy_action.setShortcut(self.shortcut_manager.get_qkeysequence('copy'))
        copy_action.triggered.connect(lambda: self.editor_tabs.current_editor_action('copy'))
        edit_menu.addAction(copy_action)
        
        paste_action = QAction('粘贴(&P)', self)
        paste_action.setShortcut(self.shortcut_manager.get_qkeysequence('paste'))
        paste_action.triggered.connect(lambda: self.editor_tabs.current_editor_action('paste'))
        edit_menu.addAction(paste_action)
        
        # 视图菜单
        view_menu = menubar.addMenu('视图(&V)')
        
        toggle_chat_action = QAction('切换聊天窗口', self)
        toggle_chat_action.setShortcut(self.shortcut_manager.get_qkeysequence('toggle_chat'))
        toggle_chat_action.triggered.connect(self.toggle_chat_widget)
        view_menu.addAction(toggle_chat_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu('工具(&T)')
        
        settings_action = QAction('设置(&S)', self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)

        # 帮助菜单
        help_menu = menubar.addMenu('帮助(&H)')
        about_action = QAction('关于(&A)', self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
        
    def show_about_dialog(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于",
                          '''Novel AI Composer 是一款专为小说家和内容创作者打造的智能写作编辑器。它拥有媲美VSCode的现代化界面和流畅的多标签编辑体验，同时深度集成了强大的人工智能（AI）辅助功能。

无论您是需要灵感续写故事、丰富情节细节（扩写），还是精炼语言（缩写），只需轻轻一点，AI即可成为您的创作伙伴。软件还提供便捷的文件管理、自动保存和个性化设置，让您能完全沉浸在创作的世界里，高效、专注地将脑海中的构思变为精彩的文字\n'''
                          "作者：忘忧一一梦\n"
                          "github地址：ssh://cat.me3h.top:6611/NovelAiCompose")

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择工作区文件夹")
        if folder:
            self.file_tree.set_root_path(folder)
            self.status_bar.showMessage(f"已打开工作区: {folder}")
            
    def open_file(self, file_path):
        """打开文件到编辑器"""
        self.editor_tabs.open_file(file_path)
        
    def save_current_file(self):
        """保存当前文件"""
        self.editor_tabs.save_current_file()
        
    def save_all_files(self):
        """保存所有文件"""
        self.editor_tabs.save_all_files()
        
    def on_tab_closed(self, index):
        """标签页关闭时的处理"""
        pass
        
    def show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self, self.work_dir)
        dialog.exec_()
        
    def toggle_chat_widget(self):
        """切换聊天窗口显示"""
        if self.chat_widget.isVisible():
            self.chat_widget.hide()
        else:
            self.chat_widget.show()
            
    def save_state(self):
        """保存程序状态"""
        state = {
            'window_geometry': {
                'x': self.x(),
                'y': self.y(),
                'width': self.width(),
                'height': self.height()
            },
            'splitter_sizes': self.main_splitter.sizes(),
            'chat_visible': self.chat_widget.isVisible(),
            'workspace': self.file_tree.root_path,
            'open_files': self.editor_tabs.get_open_files(),
            'active_file': self.editor_tabs.get_active_file()
        }
        self.state_manager.save_state(state)
        
    def load_state(self):
        """加载程序状态"""
        state = self.state_manager.load_state()
        if state:
            # 恢复窗口位置和大小
            if 'window_geometry' in state:
                geo = state['window_geometry']
                self.setGeometry(geo['x'], geo['y'], geo['width'], geo['height'])
                
            # 恢复分割器位置
            if 'splitter_sizes' in state and len(state['splitter_sizes']) == self.main_splitter.count():
                self.main_splitter.setSizes(state['splitter_sizes'])
                
            # 恢复聊天窗口可见性
            if 'chat_visible' in state and state['chat_visible']:
                self.chat_widget.show()
                
            # 恢复工作区
            if 'workspace' in state and state['workspace']:
                self.file_tree.set_root_path(state['workspace'])
                
            # 恢复打开的文件
            if 'open_files' in state:
                for file_path in state['open_files']:
                    if os.path.exists(file_path):
                        self.editor_tabs.open_file(file_path)
                        
            # 恢复活动文件
            if 'active_file' in state:
                self.editor_tabs.set_active_file(state['active_file'])
                
    def closeEvent(self, event):
        """关闭事件处理"""
        # 保存所有未保存的文件
        if not self.editor_tabs.save_all_files():
            event.ignore()
            return
            
        # 保存程序状态
        self.save_state()
        event.accept()
