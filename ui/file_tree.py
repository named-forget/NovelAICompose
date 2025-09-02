# -*- coding: utf-8 -*-

import os
import json
from PyQt5.QtWidgets import (QTreeView, QFileSystemModel, QMenu, QAction,
                             QInputDialog, QMessageBox, QStyledItemDelegate,
                             QStyleOptionViewItem)
from PyQt5.QtCore import Qt, pyqtSignal, QModelIndex
from PyQt5.QtGui import QFont, QColor, QPalette, QPainter
from PyQt5.QtWidgets import QFileSystemModel
from PyQt5.QtCore import Qt
import os

class CustomFileSystemModel(QFileSystemModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._root_title = None  # 手动设定根列标题（可选）

    def setRootTitle(self, title: str):
        self._root_title = title
        # 通知视图刷新表头
        self.headerDataChanged.emit(Qt.Horizontal, 0, 0)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0:
                # 优先使用手动设置的标题，否则用根路径的最后一级名称
                if self._root_title:
                    return self._root_title
                base = os.path.basename(self.rootPath().rstrip(os.sep))
                return base or self.rootPath()
            elif section == 1:
                return "大小"
            elif section == 2:
                return "类型"
            elif section == 3:
                return "修改日期"
        return super().headerData(section, orientation, role)
    
class DirectoryDelegate(QStyledItemDelegate):
    """自定义委托，用于显示目录类别"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.category_colors = {
            '正文': QColor(100, 200, 100),
            '设定': QColor(100, 150, 200),
            '草稿': QColor(200, 150, 100)
        }
        
    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        
        # 获取文件路径
        model = index.model()
        file_path = model.filePath(index)
        
        # 检查是否是目录并且有类别标记
        if os.path.isdir(file_path):
            category = self.parent().get_directory_category(file_path)
            if category:
                # 绘制类别标签
                painter.save()
                
                # 计算标签位置
                rect = option.rect
                label_rect = rect.adjusted(rect.width() - 60, 2, -5, -rect.height() + 18)
                
                # 绘制背景
                painter.setPen(Qt.NoPen)
                painter.setBrush(self.category_colors.get(category, QColor(150, 150, 150)))
                painter.drawRoundedRect(label_rect, 3, 3)
                
                # 绘制文字
                painter.setPen(Qt.white)
                font = QFont()
                font.setPointSize(8)
                painter.setFont(font)
                painter.drawText(label_rect, Qt.AlignCenter, category)
                
                painter.restore()


class FileTreeWidget(QTreeView):
    file_opened = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.root_path = None
        self.directory_categories = {}
        
        # 设置文件系统模型
        self.model = CustomFileSystemModel()
        self.model.setRootPath("")
        self.setModel(self.model)
        
        # 设置自定义委托
        self.delegate = DirectoryDelegate(self)
        self.setItemDelegate(self.delegate)
        
        # 设置视图属性
        self.setHeaderHidden(False)
        self.setAnimated(True)
        self.setIndentation(20)
        self.setSortingEnabled(True)
        
        # 隐藏不需要的列
        self.hideColumn(1)  # Size
        self.hideColumn(2)  # Type
        self.hideColumn(3)  # Date Modified
        
        # 连接信号
        self.doubleClicked.connect(self.on_double_click)
        
        # 加载目录类别配置
        self.load_directory_categories()
        self.header().setContextMenuPolicy(Qt.CustomContextMenu)
        self.header().customContextMenuRequested.connect(self._show_root_menu_from_header)

    def _show_root_menu_from_header(self, pos):
        if not self.root_path:
            return
        event_pos = self.header().mapToGlobal(pos)
        self._show_dir_menu(self.root_path, is_root=True, global_pos=event_pos)


    def _show_dir_menu(self, file_path, is_root, global_pos):
        menu = QMenu(self)
        ...  # 你原来的菜单构建逻辑
        menu.exec_(global_pos)

    def set_root_path(self, path):
        """设置根路径"""
        self.root_path = path
        index = self.model.setRootPath(path)
        self.setRootIndex(index)
        # 不要再用 setHeaderData（对 QFileSystemModel 无效）
        if isinstance(self.model, CustomFileSystemModel):
            self.model.setRootTitle(os.path.basename(path) or path)
        
    def on_double_click(self, index):
        """双击事件处理"""
        file_path = self.model.filePath(index)
        if os.path.isfile(file_path):
            self.file_opened.emit(file_path)
            
    def contextMenuEvent(self, event):
        """右键菜单事件"""
        index = self.indexAt(event.pos())
        file_path = ""
        is_root = False
        
        if index.isValid():
            file_path = self.model.filePath(index)
        else:
            # 如果点击的是空白区域，则视为对根目录操作
            file_path = self.root_path
            is_root = True

        if not file_path:
            return

        menu = QMenu(self)
        
        if os.path.isdir(file_path):
            # 目录菜单
            new_file_action = QAction("新建文件", self)
            new_file_action.triggered.connect(lambda: self.new_file(file_path))
            menu.addAction(new_file_action)
            
            new_folder_action = QAction("新建文件夹", self)
            new_folder_action.triggered.connect(lambda: self.new_folder(file_path))
            menu.addAction(new_folder_action)
            
            menu.addSeparator()
            
            # 目录类别标记菜单
            category_menu = menu.addMenu("标记类别")
            
            for category in ["正文", "设定", "草稿"]:
                action = QAction(category, self)
                action.setCheckable(True)
                action.setChecked(self.get_directory_category(file_path) == category)
                action.triggered.connect(lambda checked, c=category: self.set_directory_category(file_path, c))
                category_menu.addAction(action)
                
            clear_category_action = QAction("清除标记", self)
            clear_category_action.triggered.connect(lambda: self.clear_directory_category(file_path))
            category_menu.addSeparator()
            category_menu.addAction(clear_category_action)
            
            menu.addSeparator()
            
            rename_action = QAction("重命名", self)
            rename_action.triggered.connect(lambda: self.rename_item(file_path))
            if is_root:
                rename_action.setEnabled(False)
            menu.addAction(rename_action)

            delete_action = QAction("删除", self)
            delete_action.triggered.connect(lambda: self.delete_item(file_path))
            if is_root:
                delete_action.setEnabled(False)
            menu.addAction(delete_action)
            
        else:
            # 文件菜单
            open_action = QAction("打开", self)
            open_action.triggered.connect(lambda: self.file_opened.emit(file_path))
            menu.addAction(open_action)
            
            menu.addSeparator()
            
            rename_action = QAction("重命名", self)
            rename_action.triggered.connect(lambda: self.rename_item(file_path))
            menu.addAction(rename_action)
            
            delete_action = QAction("删除", self)
            delete_action.triggered.connect(lambda: self.delete_item(file_path))
            menu.addAction(delete_action)
            
        menu.exec_(event.globalPos())
        
    def new_file(self, directory):
        """新建文件"""
        name, ok = QInputDialog.getText(self, "新建文件", "文件名:")
        if ok and name:
            file_path = os.path.join(directory, name)
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("")
                self.file_opened.emit(file_path)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建文件失败: {str(e)}")
                
    def new_folder(self, directory):
        """新建文件夹"""
        name, ok = QInputDialog.getText(self, "新建文件夹", "文件夹名:")
        if ok and name:
            folder_path = os.path.join(directory, name)
            try:
                os.makedirs(folder_path)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建文件夹失败: {str(e)}")
                
    def rename_item(self, path):
        """重命名文件或文件夹"""
        old_name = os.path.basename(path)
        new_name, ok = QInputDialog.getText(self, "重命名", "新名称:", text=old_name)
        if ok and new_name and new_name != old_name:
            new_path = os.path.join(os.path.dirname(path), new_name)
            try:
                os.rename(path, new_path)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"重命名失败: {str(e)}")
                
    def delete_item(self, path):
        """删除文件或文件夹"""
        reply = QMessageBox.question(self, "确认删除", 
                                   f"确定要删除 '{os.path.basename(path)}' 吗?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                if os.path.isdir(path):
                    import shutil
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")
                
    def get_directory_category(self, path):
        """获取目录类别"""
        return self.directory_categories.get(path)
        
    def set_directory_category(self, path, category):
        """设置目录类别"""
        self.directory_categories[path] = category
        self.save_directory_categories()
        self.viewport().update()
        
    def clear_directory_category(self, path):
        """清除目录类别"""
        if path in self.directory_categories:
            del self.directory_categories[path]
            self.save_directory_categories()
            self.viewport().update()
            
    def save_directory_categories(self):
        """保存目录类别配置"""
        if self.parent_window:
            config_path = os.path.join(self.parent_window.work_dir, 'directory_categories.json')
            try:
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.directory_categories, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"保存目录类别配置失败: {e}")
                
    def load_directory_categories(self):
        """加载目录类别配置"""
        if self.parent_window:
            config_path = os.path.join(self.parent_window.work_dir, 'directory_categories.json')
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        self.directory_categories = json.load(f)
                except Exception as e:
                    print(f"加载目录类别配置失败: {e}")
                    self.directory_categories = {}
