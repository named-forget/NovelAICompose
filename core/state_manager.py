# -*- coding: utf-8 -*-

import os
import json


class StateManager:
    """状态管理器"""
    def __init__(self, work_dir):
        self.work_dir = work_dir
        self.state_file = os.path.join(work_dir, 'app_state.json')
        
    def save_state(self, state):
        """保存应用状态"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存状态失败: {e}")
            
    def load_state(self):
        """加载应用状态"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载状态失败: {e}")
        return None
        
    def clear_state(self):
        """清除应用状态"""
        if os.path.exists(self.state_file):
            try:
                os.remove(self.state_file)
            except Exception as e:
                print(f"清除状态失败: {e}")
