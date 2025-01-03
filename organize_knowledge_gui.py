import os
import json
import shutil
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QTextEdit, QFileDialog,
                            QLabel, QMessageBox, QProgressDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QRectF
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QPainterPath 
from file_processor import FileProcessor
from loading_spinner import LoadingSpinner
from directory_snapshot import DirectorySnapshot
from config import Config  # 导入配置类

class WorkerThread(QThread):
    """后台工作线程，用于处理文件分析和整理"""
    update_signal = pyqtSignal(str)  # 用于更新UI的信号
    result_signal = pyqtSignal(tuple)  # 用于返回分析文本和分类结果的信号
    error_signal = pyqtSignal(str)    # 用于报告错误的信号
    
    def __init__(self, base_dir):
        super().__init__()
        self.base_dir = base_dir
        # 使用配置中的大模型参数
        self.processor = FileProcessor(
            api_key=Config.API_KEY,
            model_name=Config.MODEL_NAME,
            temperature=Config.TEMPERATURE
        )
    
    def log(self, message):
        """发送日志消息到UI"""
        self.update_signal.emit(message)
    
    def run(self):
        try:
            # 收集文件名
            file_names = []
            for root, _, files in os.walk(self.base_dir):
                for file in files:
                    # 不再过滤文件类型
                    file_names.append(os.path.join(root, file))
            
            if not file_names:
                self.error_signal.emit("目录为空")
                return
            
            self.log(f"\n找到 {len(file_names)} 个文件")
            for file in file_names:
                self.log(f"- {file}")
            
            # 获取分类结果
            analysis_text, category_mapping = self.processor.analyze_filenames(file_names)
            if category_mapping:
                self.result_signal.emit((analysis_text, category_mapping))
            else:
                self.error_signal.emit("未能获取有效的分类结果")
        
        except Exception as e:
            self.error_signal.emit(f"处理过程中出错：{str(e)}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 使用配置中的应用标题和窗口尺寸
        self.setWindowTitle(Config.APP_TITLE)
        self.setMinimumSize(Config.MIN_WINDOW_WIDTH, Config.MIN_WINDOW_HEIGHT)

        # 设置应用图标（添加错误检查和多个位置查找）
        icon_paths = [
            os.path.join(os.path.dirname(__file__), "assets", "app_icon.png"),  # 相对于脚本的assets目录
            os.path.join("assets", "app_icon.png"),  # 相对于当前工作目录的assets目录
            "assets/app_icon.png"  # 直接路径
        ]

        icon_loaded = False
        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                try:
                    # 创建圆角图标
                    pixmap = QPixmap(icon_path)
                    if not pixmap.isNull():
                        # 缩放到合适的大小
                        scaled_size = 64  # 减小图标大小
                        pixmap = pixmap.scaled(scaled_size, scaled_size, 
                                             Qt.AspectRatioMode.KeepAspectRatio, 
                                             Qt.TransformationMode.SmoothTransformation)
                        
                        # 创建圆角效果
                        rounded = QPixmap(pixmap.size())
                        rounded.fill(Qt.GlobalColor.transparent)
                        
                        painter = QPainter(rounded)
                        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                        
                        # 使用 QRectF 替代 QRect
                        path = QPainterPath()
                        rect = QRectF(rounded.rect())
                        corner_radius = 12.0  # 使用浮点数
                        path.addRoundedRect(rect, corner_radius, corner_radius)
                        
                        painter.setClipPath(path)
                        painter.drawPixmap(0, 0, pixmap)
                        painter.end()
                        
                        app_icon = QIcon(rounded)
                        self.setWindowIcon(app_icon)
                        QApplication.setWindowIcon(app_icon)
                        icon_loaded = True
                        print(f"成功加载图标：{icon_path}")
                        break
                except Exception as e:
                    print(f"加载图标 {icon_path} 时出错：{str(e)}")
        
        if not icon_loaded:
            print("警告：未能加载应用图标")
        
        self.current_dir = None
        self.category_mapping = None
        self.directory_snapshot = None  # 添加目录快照
        self.initUI()

        # 创建加载动画
        self.loading_spinner = LoadingSpinner(self, size=80, 
                                            color=Qt.GlobalColor.darkBlue)
        # 将加载动画居中显示
        self.loading_spinner.move(
            self.width() // 2 - self.loading_spinner.width() // 2,
            self.height() // 2 - self.loading_spinner.height() // 2
        )

        # 创建处理中提示标签
        self.processing_label = QLabel("正在分析文件...", self)
        self.processing_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.processing_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 0.7);
                color: white;
                padding: 15px 30px;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        self.processing_label.hide()
        self.loading_spinner.stop() # 隐藏加载动画

        # 初始加载目录文件
        self.file_list = []
    
    def initUI(self):
        # 主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # 顶部控制区域
        top_layout = QHBoxLayout()
        self.dir_label = QLabel("请选择目录")
        self.select_dir_btn = QPushButton("选择目录")
        self.select_dir_btn.clicked.connect(self.select_directory)
        self.start_btn = QPushButton("开始整理")
        self.start_btn.clicked.connect(self.start_processing)
        self.start_btn.setEnabled(False)
        
        top_layout.addWidget(self.dir_label)
        top_layout.addWidget(self.select_dir_btn)
        top_layout.addWidget(self.start_btn)
        layout.addLayout(top_layout)
        
        # 日志输出区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        # 底部按钮区域
        bottom_layout = QHBoxLayout()
        self.confirm_btn = QPushButton("确认")
        self.regenerate_btn = QPushButton("重新生成")
        self.cancel_btn = QPushButton("取消")
        
        self.confirm_btn.clicked.connect(self.confirm_changes)
        self.regenerate_btn.clicked.connect(self.regenerate)
        self.cancel_btn.clicked.connect(self.cancel_operation)
        
        self.confirm_btn.setEnabled(False)
        self.regenerate_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        
        # 在底部按钮区域添加还原按钮
        self.restore_btn = QPushButton("还原目录")
        self.restore_btn.clicked.connect(self.restore_directory)
        self.restore_btn.setEnabled(False)
        
        bottom_layout.addWidget(self.confirm_btn)
        bottom_layout.addWidget(self.regenerate_btn)
        bottom_layout.addWidget(self.cancel_btn)
        bottom_layout.addWidget(self.restore_btn)
        layout.addLayout(bottom_layout)
    
    def select_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择目录")
        if dir_path:
            self.current_dir = dir_path
            self.dir_label.setText(f"当前目录: {dir_path}")
            self.start_btn.setEnabled(True)
            
            # 创建目录快照
            self.directory_snapshot = DirectorySnapshot(dir_path)
            self.directory_snapshot.take_snapshot()
            if self.directory_snapshot.create_backup():
                self.restore_btn.setEnabled(True)
            
            # 加载并显示目录中的所有文件
            self.load_directory_files(dir_path)
    
    def load_directory_files(self, dir_path):
        """加载并显示目录中的所有文件"""
        self.log_text.clear()
        self.file_list = []
        
        for root, _, files in os.walk(dir_path):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, dir_path)
                self.file_list.append(rel_path)
        
        if self.file_list:
            self.log_text.append("当前目录下的文件：")
            for file in sorted(self.file_list):
                self.log_text.append(f"- {file}")
            self.log_text.append(f"\n共找到 {len(self.file_list)} 个文件")
        else:
            self.log_text.append("目录为空")
            self.start_btn.setEnabled(False)
    
    def restore_directory(self):
        """还原目录到初始状态"""
        if not self.directory_snapshot:
            return
        
        reply = QMessageBox.question(
            self, 
            "确认还原", 
            "确定要还原目录到初始状态吗？这将撤销所有的整理操作。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.directory_snapshot.restore():
                    self.load_directory_files(self.current_dir)
                    QMessageBox.information(self, "成功", "目录已还原到初始状态")
                else:
                    QMessageBox.critical(self, "错误", "还原目录失败")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"还原过程中出错：{str(e)}")
    
    def cleanup_backup(self):
        """清理备份文件"""
        if self.directory_snapshot:
            self.directory_snapshot.cleanup_backup()
    
    def closeEvent(self, event):
        """程序关闭时清理备份"""
        self.cleanup_backup()
        super().closeEvent(event)

    def resizeEvent(self, event):
        """窗口大小改变时重新定位加载动画和提示标签"""
        super().resizeEvent(event)
        
        # 重新定位加载动画
        if hasattr(self, 'loading_spinner'):
            self.loading_spinner.move(
                self.width() // 2 - self.loading_spinner.width() // 2,
                self.height() // 2 - self.loading_spinner.height() // 2
            )
        
        # 重新定位提示标签
        if hasattr(self, 'processing_label'):
            # 调整标签大小以适应内容
            self.processing_label.adjustSize()
            # 将标签放在窗口中央偏上的位置
            self.processing_label.move(
                self.width() // 2 - self.processing_label.width() // 2,
                self.height() // 3 - self.processing_label.height() // 2
            )

    def start_processing(self):
        if not self.current_dir:
            return
        
        self.log_text.clear()
        self.start_btn.setEnabled(False)
        self.select_dir_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.restore_btn.setEnabled(False)
        
        # 显示加载动画和提示
        self.loading_spinner.start()
        self.processing_label.show()
        
        self.worker = WorkerThread(self.current_dir)
        self.worker.update_signal.connect(self.update_log)
        self.worker.result_signal.connect(self.handle_results)
        self.worker.error_signal.connect(self.handle_error)
        self.worker.start()
    
    def update_log(self, message):
        self.log_text.append(message)
    
    def handle_results(self, results):
        try:
            # 隐藏加载动画和提示
            self.loading_spinner.stop()
            self.processing_label.hide()
            
            analysis_text, category_mapping = results
            self.category_mapping = category_mapping
            
            self.log_text.append("\n分析结果：")
            self.log_text.append(analysis_text)
            
            self.log_text.append("\n\n分类结果：")
            self.log_text.append(json.dumps(category_mapping, ensure_ascii=False, indent=2))
            
            self.confirm_btn.setEnabled(True)
            self.regenerate_btn.setEnabled(True)
            self.cancel_btn.setEnabled(True)
            self.restore_btn.setEnabled(False)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"处理结果时出错：{str(e)}")
            self.reset_ui()
    
    def handle_error(self, error_message):
        # 隐藏加载动画和提示
        self.loading_spinner.stop()
        self.processing_label.hide()

        QMessageBox.critical(self, "错误", error_message)
        self.reset_ui()
    
    def confirm_changes(self):
        if not self.category_mapping:
            QMessageBox.warning(self, "警告", "没有可用的分类结果")
            return
        
        try:
            # 移动文件
            self.move_files(self.category_mapping)

            # 等待一小段时间确保文件移动完成
            QApplication.processEvents()

            # 清理空目录
            self.cleanup_empty_dirs()

            # 保存分析报告
            self.save_analysis_report()
            self.restore_btn.setEnabled(True)
            
            QMessageBox.information(self, "成功", "文件整理完成！")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"处理过程中出错：{str(e)}")
            self.log_text.append(f"\n错误：{str(e)}")
        finally:
            self.reset_ui()
    
    def move_files(self, category_mapping):
        """移动文件到对应目录"""
        moved_files = set()
        for category, files in category_mapping.items():
            category_dir = os.path.join(self.current_dir, category)
            os.makedirs(category_dir, exist_ok=True)
            
            for file_name in files:
                if file_name in moved_files:
                    self.update_log(f"警告：文件'{file_name}'已经被移动过")
                    continue
                
                src_file = self.find_file(file_name)
                if src_file:
                    try:
                        shutil.move(src_file, os.path.join(category_dir, file_name))
                        moved_files.add(file_name)
                        self.update_log(f"已移动：'{file_name}' -> {category}")
                    except Exception as e:
                        self.update_log(f"移动文件'{file_name}'时出错：{str(e)}")
    
    def cleanup_empty_dirs(self):
        """清理所有空目录，包括删除隐藏文件"""
        # 从下往上遍历目录树，这样可以先处理最深的目录
        for root, dirs, files in os.walk(self.current_dir, topdown=False):
            # 跳过当前目录
            if root == self.current_dir:
                continue

            # 删除隐藏文件（如 .DS_Store）
            for item in os.listdir(root):
                item_path = os.path.join(root, item)
                if os.path.isfile(item_path) and item.startswith('.'):
                    try:
                        os.remove(item_path)
                        self.update_log(f"已删除隐藏文件：{os.path.relpath(item_path, self.current_dir)}")
                    except Exception as e:
                        self.update_log(f"删除隐藏文件失败：{os.path.relpath(item_path, self.current_dir)} - {str(e)}")

            # 检查目录是否为空
            if not os.listdir(root):
                try:
                    os.rmdir(root)
                    self.update_log(f"已删除空目录：{os.path.relpath(root, self.current_dir)}")
                except OSError as e:
                    self.update_log(f"删除目录失败：{os.path.relpath(root, self.current_dir)} - {str(e)}")
            else:
                self.update_log(f"目录不为空，跳过：{os.path.relpath(root, self.current_dir)}")
    def cleanup_analysis_reports(self):
        """清理目录中的旧分析报告"""
        if not self.current_dir:
            return
        
        try:
            # 查找所有分析报告文件
            report_files = []
            for file in os.listdir(self.current_dir):
                if file.startswith("file_analysis_report_") and file.endswith(".txt"):
                    report_path = os.path.join(self.current_dir, file)
                    report_files.append(report_path)
            
            # 删除找到的报告文件
            for report_file in report_files:
                try:
                    os.remove(report_file)
                    self.update_log(f"已删除旧的分析报告：{os.path.basename(report_file)}")
                except Exception as e:
                    self.update_log(f"删除报告文件失败：{os.path.basename(report_file)} - {str(e)}")
        
        except Exception as e:
            self.update_log(f"清理分析报告时出错：{str(e)}")

    def save_analysis_report(self):
        """保存分析报告"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = os.path.join(self.current_dir, f"file_analysis_report_{timestamp}.txt")
            
            with open(report_path, "w", encoding="utf-8") as f:
                f.write("文件分类分析报告\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"目录路径：{self.current_dir}\n\n")
                f.write("分类结果：\n")
                f.write(json.dumps(self.category_mapping, ensure_ascii=False, indent=2))
                f.write("\n\n处理日志：\n")
                f.write(self.log_text.toPlainText())
            
            self.update_log(f"\n分析报告已保存至：{report_path}")
        except Exception as e:
            self.update_log(f"\n保存分析报告时出错：{str(e)}")
            raise
    
    def find_file(self, file_name):
        """在目录中查找文件"""
        for root, _, files in os.walk(self.current_dir):
            if file_name in files:
                return os.path.join(root, file_name)
        return None
    
    def regenerate(self):
        """重新生成分类"""
        if not self.current_dir:
            return
        
        # 清理旧的分析报告
        self.cleanup_analysis_reports()
        
        # 重置分类结果
        self.category_mapping = None
        
        # 开始新的处理
        self.start_processing()
    
    def cancel_operation(self):
        """取消操作"""
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.terminate()
            self.loading_spinner.stop()
            self.processing_label.hide()
        self.reset_ui()
    
    def reset_ui(self):
        """重置UI状态"""
        self.start_btn.setEnabled(True)
        self.select_dir_btn.setEnabled(True)
        self.confirm_btn.setEnabled(False)
        self.regenerate_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.category_mapping = None

def main():
    try:
        app = QApplication([])
        window = MainWindow()
        window.show()
        app.exec()
    except Exception as e:
        QMessageBox.critical(None, "严重错误", f"程序运行出错：{str(e)}")


if __name__ == "__main__":
    main()