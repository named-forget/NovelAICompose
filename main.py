#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QSettings
from ui.main_window import MainWindow

# 获取工作目录
if getattr(sys, 'frozen', False):
    work_dir = os.path.dirname(sys.executable)
else:
    work_dir = os.getcwd().replace('\\', '/')

def main():
    # 启用高DPI支持
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setApplicationName("Novel AI Composer")
    app.setOrganizationName("NovelAI")
    
    # 设置应用样式
    settings = QSettings("NovelAI", "NovelAIComposer")
    theme = settings.value("theme", "dark")
    if theme == "light":
        from ui.styles import get_vscode_light_style
        app.setStyleSheet(get_vscode_light_style())
    else:
        from ui.styles import get_vscode_dark_style
        app.setStyleSheet(get_vscode_dark_style())
    
    # 创建主窗口
    window = MainWindow(work_dir)
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
