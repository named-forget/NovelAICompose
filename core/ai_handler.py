# -*- coding: utf-8 -*-

import os
import json
import requests
from PyQt5.QtCore import QObject, pyqtSignal, QThread




class AIHandler:
    """AI处理器"""
    def __init__(self, work_dir):
        self.work_dir = work_dir
        self.config = self.load_config()
        
    def load_config(self):
        """加载配置"""
        default_config = {
            'api_key': '',
            'base_url': 'https://api.openai.com/v1',
            'model': 'gpt-3.5-turbo',
            'prompts': {
                'continue': '设定参考：\n{setting}\n\n请根据上文内容，继续写作，保持风格和语气一致：\n\n{context}',
                'expand': '设定参考：\n{setting}\n\n请将以下内容进行扩写，增加更多细节和描述，但保持原意不变：\n\n{context}',
                'summarize': '设定参考：\n{setting}\n\n请将以下内容进行缩写，保留核心信息，使其更加简洁：\n\n{context}',
                'custom': '设定参考：\n{setting}\n\n{prompt}\n\n文本内容：\n{context}'
            }
        }
        
        if self.work_dir:
            config_path = os.path.join(self.work_dir, 'ai_config.json')
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        loaded_config = json.load(f)
                        # 合并配置
                        for key in default_config:
                            if key in loaded_config:
                                if isinstance(default_config[key], dict):
                                    default_config[key].update(loaded_config[key])
                                else:
                                    default_config[key] = loaded_config[key]
                except Exception as e:
                    print(f"加载AI配置失败: {e}")
                    
        return default_config
        
    def save_config(self):
        """保存配置"""
        if self.work_dir:
            config_path = os.path.join(self.work_dir, 'ai_config.json')
            try:
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"保存AI配置失败: {e}")
                
    def get_setting_content(self):
        """获取“设定”目录下的所有文本内容"""
        if not self.work_dir:
            return ""

        categories_path = os.path.join(self.work_dir, 'directory_categories.json')
        if not os.path.exists(categories_path):
            return ""

        try:
            with open(categories_path, 'r', encoding='utf-8') as f:
                categories = json.load(f)
        except Exception as e:
            print(f"加载目录分类失败: {e}")
            return ""

        setting_dirs = [path for path, category in categories.items() if category == '设定']

        all_content = []
        for setting_dir in setting_dirs:
            if os.path.isdir(setting_dir):
                for filename in sorted(os.listdir(setting_dir)):
                    file_path = os.path.join(setting_dir, filename)
                    if os.path.isfile(file_path) and filename.endswith(('.txt', '.md')):
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                all_content.append(f.read())
                        except Exception as e:
                            print(f"读取设定文件失败: {file_path}, {e}")

        return "\n\n".join(all_content)

    def get_continue_prompt(self, context):
        """获取续写提示词"""
        setting_content = self.get_setting_content()
        return self.config['prompts']['continue'].format(context=context, setting=setting_content)
        
    def get_expand_prompt(self, context):
        """获取扩写提示词"""
        setting_content = self.get_setting_content()
        return self.config['prompts']['expand'].format(context=context, setting=setting_content)
        
    def get_summarize_prompt(self, context):
        """获取缩写提示词"""
        setting_content = self.get_setting_content()
        return self.config['prompts']['summarize'].format(context=context, setting=setting_content)
        
    def get_custom_prompt(self, context, prompt):
        """获取自定义提示词"""
        setting_content = self.get_setting_content()
        return self.config['prompts']['custom'].format(context=context, prompt=prompt, setting=setting_content)
        
    def generate_stream(self, prompt):
        """流式生成文本"""
        if not self.config.get('api_key'):
            raise ValueError("请先配置API Key")
            
        headers = {
            'Authorization': f"Bearer {self.config['api_key']}",
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': self.config['model'],
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'stream': True,
            'temperature': 0.7,
            'max_tokens': 1000
        }
        
        url = f"{self.config['base_url']}/chat/completions"
        
        try:
            response = requests.post(url, headers=headers, json=data, stream=True)
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        line = line[6:]
                        if line == '[DONE]':
                            break
                            
                        try:
                            chunk_data = json.loads(line)
                            if 'choices' in chunk_data and chunk_data['choices']:
                                delta = chunk_data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
                            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API请求失败: {str(e)}")
            
    def chat(self, messages):
        """聊天接口"""
        if not self.config.get('api_key'):
            raise ValueError("请先配置API Key")
            
        headers = {
            'Authorization': f"Bearer {self.config['api_key']}",
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': self.config['model'],
            'messages': messages,
            'stream': True,
            'temperature': 0.7
        }
        
        url = f"{self.config['base_url']}/chat/completions"
        
        try:
            response = requests.post(url, headers=headers, json=data, stream=True)
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        line = line[6:]
                        if line == '[DONE]':
                            break
                            
                        try:
                            chunk_data = json.loads(line)
                            if 'choices' in chunk_data and chunk_data['choices']:
                                delta = chunk_data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
                            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API请求失败: {str(e)}")


class AIWorker(QObject):
    """AI工作线程"""
    chunk_received = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, ai_handler:AIHandler, action, context):
        super().__init__()
        self.ai_handler = ai_handler
        self.action = action
        self.context = context
        self.custom_prompt = None
        self._stop_requested = False
        
    def stop(self):
        """请求停止生成"""
        self._stop_requested = True
        
    def run(self):
        """执行AI生成"""
        try:
            # 根据动作类型构建提示词
            if self.action == 'continue':
                prompt = self.ai_handler.get_continue_prompt(self.context)
            elif self.action == 'expand':
                prompt = self.ai_handler.get_expand_prompt(self.context)
            elif self.action == 'summarize':
                prompt = self.ai_handler.get_summarize_prompt(self.context)
            elif self.action == 'custom':
                prompt = self.ai_handler.get_custom_prompt(self.context, self.custom_prompt)
            else:
                self.error.emit(f"未知的动作类型: {self.action}")
                return
            print(prompt)    
            # 调用OpenAI API
            for chunk in self.ai_handler.generate_stream(prompt):
                if self._stop_requested:
                    break
                self.chunk_received.emit(chunk)
                
            self.finished.emit()
            
        except Exception as e:
            self.error.emit(str(e))
