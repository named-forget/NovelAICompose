# -*- coding: utf-8 -*-

import os
import json
from PyQt5.QtGui import QKeySequence


class ShortcutManager:
    """快捷键管理器"""
    def __init__(self, work_dir):
        self.work_dir = work_dir
        self.config_file = os.path.join(work_dir, 'shortcuts.json')
        self.shortcuts = self.load_shortcuts()
        
    def get_default_shortcuts(self):
        """获取默认快捷键"""
        return {
            'open_folder': 'Ctrl+O',
            'save_file': 'Ctrl+S',
            'save_all_files': 'Ctrl+Shift+S',
            'exit_app': 'Ctrl+Q',
            'undo': 'Ctrl+Z',
            'redo': 'Ctrl+Y',
            'cut': 'Ctrl+X',
            'copy': 'Ctrl+C',
            'paste': 'Ctrl+V',
            'ai_continue': 'Ctrl+Space',
            'ai_expand': 'Ctrl+E',
            'ai_summarize': 'Ctrl+K',
            'ai_custom': 'Ctrl+M',
            'toggle_chat': 'Ctrl+Shift+C'
        }
        
    def load_shortcuts(self):
        """加载快捷键配置"""
        default_shortcuts = self.get_default_shortcuts()
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_shortcuts = json.load(f)
                    # 合并配置
                    default_shortcuts.update(loaded_shortcuts)
            except Exception as e:
                print(f"加载快捷键配置失败: {e}")
                
        return default_shortcuts
        
    def save_shortcuts(self):
        """保存快捷键配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.shortcuts, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存快捷键配置失败: {e}")
            
    def get_shortcut(self, name):
        """获取快捷键"""
        return self.shortcuts.get(name, '')
        
    def set_shortcut(self, name, sequence):
        """设置快捷键"""
        self.shortcuts[name] = sequence
        
    def get_qkeysequence(self, name):
        """获取QKeySequence对象"""
        return QKeySequence(self.get_shortcut(name))
