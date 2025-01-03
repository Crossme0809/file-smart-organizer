import os
import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

@dataclass
class FileInfo:
    path: str
    is_dir: bool
    original_path: str

class DirectorySnapshot:
    def __init__(self, root_path: str):
        self.root_path = root_path
        self.snapshot_time = datetime.now()
        self.files: Dict[str, FileInfo] = {}
        self.backup_path: Optional[str] = None
        
    def take_snapshot(self):
        """记录目录的当前状态"""
        self.files.clear()
        for root, dirs, files in os.walk(self.root_path):
            # 记录目录
            for dir_name in dirs:
                full_path = os.path.join(root, dir_name)
                rel_path = os.path.relpath(full_path, self.root_path)
                self.files[rel_path] = FileInfo(
                    path=rel_path,
                    is_dir=True,
                    original_path=full_path
                )
            
            # 记录文件
            for file_name in files:
                full_path = os.path.join(root, file_name)
                rel_path = os.path.relpath(full_path, self.root_path)
                self.files[rel_path] = FileInfo(
                    path=rel_path,
                    is_dir=False,
                    original_path=full_path
                )
    
    def create_backup(self):
        """创建目录的物理备份"""
        timestamp = self.snapshot_time.strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(os.path.dirname(self.root_path), f".backup_{timestamp}")
        
        try:
            # 复制整个目录结构
            shutil.copytree(self.root_path, backup_dir)
            self.backup_path = backup_dir
            return True
        except Exception as e:
            print(f"创建备份失败：{str(e)}")
            return False
    
    def restore(self) -> bool:
        """还原到初始状态"""
        if not self.backup_path or not os.path.exists(self.backup_path):
            return False
        
        try:
            # 删除当前目录的所有内容
            for item in os.listdir(self.root_path):
                item_path = os.path.join(self.root_path, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            
            # 从备份中复制所有内容
            for item in os.listdir(self.backup_path):
                src_path = os.path.join(self.backup_path, item)
                dst_path = os.path.join(self.root_path, item)
                if os.path.isfile(src_path):
                    shutil.copy2(src_path, dst_path)
                else:
                    shutil.copytree(src_path, dst_path)
            
            return True
        except Exception as e:
            print(f"还原失败：{str(e)}")
            return False
    
    def cleanup_backup(self):
        """清理备份目录"""
        if self.backup_path and os.path.exists(self.backup_path):
            try:
                shutil.rmtree(self.backup_path)
                return True
            except Exception:
                return False
        return False