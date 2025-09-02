# -*- coding: utf-8 -*-
import os
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def get_vscode_dark_style():
    """获取VSCode暗色主题样式表"""
    return open(resource_path("ui/style/dark.qss"), "r", encoding='utf8').read()


def get_vscode_light_style():
    """获取VSCode浅色主题样式表"""
    return  open(resource_path("ui/style/light.qss"), "r", encoding='utf8').read()


def get_vscode_style():
    """获取VSCode风格的样式表（兼容旧版本）"""
    return get_vscode_dark_style()
