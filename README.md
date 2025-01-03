# 文件智能分类整理工具 (File Smart Organizer)

一个基于 Python 和 PyQt6 开发的智能文件分类整理工具，能够自动分析文件名，理解文件内容关系，并按照智能推断的类别进行文件整理。

## 项目简介

本工具旨在解决文件管理混乱、文件分类困难的问题。通过智能分析文件名称，自动推断文件的类别关系，实现文件的智能分类和整理，帮助用户建立清晰的文件组织结构。

### 主要特点

- 🧠 智能分析：自动分析文件名称，理解文件内容关系
- 📂 自动分类：根据分析结果自动创建分类目录并移动文件
- 🔄 可撤销操作：支持还原功能，可随时恢复原始文件结构
- 📊 分析报告：自动生成详细的分类分析报告
- 🪟 友好界面：简洁直观的图形用户界面
- 🔍 实时预览：整理前可预览分类结果
- ♻️ 清理功能：自动清理空目录和临时文件

## 效果展示

### 1. 待整理的混乱文件目录
<div align="center">
  <img src="https://github.com/Crossme0809/frenzy_repo/blob/main/file-smart-organizer/books_origin.jpg" alt="原始文件目录" width="800"/>
  <p><em>混乱的文件目录，需要整理</em></p>
</div>

### 2. 智能分析分类过程
<div align="center">
  <img src="https://github.com/Crossme0809/frenzy_repo/blob/main/file-smart-organizer/file_organizer..png" alt="智能分析界面" width="800"/>
  <p><em>文件智能分析和分类过程</em></p>
</div>

### 3. 整理完成后的效果
<div align="center">
  <img src="https://github.com/Crossme0809/frenzy_repo/blob/main/file-smart-organizer/books_organizer.png" alt="整理后的文件目录" width="800"/>
  <p><em>文件自动分类整理后的清晰结构</em></p>
</div>

## 功能介绍

1. **文件分析**
   - 智能分析文件名称和关键词
   - 自动推断文件类别关系
   - 生成分类建议

2. **自动整理**
   - 自动创建分类目录
   - 智能移动文件到对应目录
   - 自动清理空目录

3. **操作管理**
   - 支持预览分类结果
   - 可选择确认或重新生成
   - 支持还原原始结构

4. **报告生成**
   - 自动生成分类分析报告
   - 记录整理过程和结果
   - 保存分类方案供future参考

## 安装说明

### 环境要求
- Python 3.8 或更高版本
- PyQt6
- 其他依赖包

### 安装步骤

1. 克隆项目
```bash
git clone https://github.com/Crossme0809/file-smart-organizer.git
cd file-smart-organizer
```

2. 创建虚拟环境（推荐）
```python
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Linux/Mac
source venv/bin/activate
# Windows
venv\Scripts\activate
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

## 使用说明

### 启动程序
```bash
python organize_knowledge_gui.py
```

### 使用步骤

1. 点击"选择目录"按钮选择要整理的文件夹
2. 点击"开始整理"进行文件分析
3. 查看分析结果和分类建议
4. 点击"确认"执行整理，或"重新生成"重新分析
5. 如需还原，可点击"还原目录"

## 未来规划

### 1. 多目录支持
- [ ] 支持同时处理多个目录
- [ ] 跨目录文件关联分析
- [ ] 批量处理功能

### 2. 模型优化
- [ ] 自定义分类规则配置
- [ ] 支持多种分类策略
- [ ] 机器学习模型集成

### 3. 文档管理增强
- [ ] 导出目录结构清单
- [ ] 生成知识体系图谱
- [ ] 文件关系可视化

### 4. 分析能力提升
- [ ] 文件内容分析
- [ ] 图片识别分类
- [ ] 文档相似度分析

### 5. 用户体验优化
- [ ] 深色模式支持
- [ ] 自定义主题
- [ ] 快捷键支持
- [ ] 拖拽操作支持

### 6. 知识管理
- [ ] 知识标签系统
- [ ] 知识关系图谱
- [ ] 智能推荐系统

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进项目。

## 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。

## 联系方式

如有问题或建议，欢迎联系：

- 邮箱：crossme0809@gmail.com
- GitHub Issues

## 致谢

感谢所有贡献者对本项目的支持和帮助。