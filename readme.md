# Contour Analyzer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)]()

**Contour Analyzer** is a lightweight desktop application for contour detection, manual editing, and measurement on images. It uses OpenCV for image processing and Tkinter for GUI. Perfect for engineers, researchers, and hobbyists who need to quickly extract and analyze object boundaries from PCB photos, mechanical parts, or any contour-rich images.

---

## ✨ Key Features

- **Image Loading & Processing**  
  Load JPG, PNG, BMP images. Adjust threshold, kernel size, contour retrieval mode (external / tree).

- **Region of Interest (ROI)**  
  Select custom ROI with rectangle. Choose processing algorithm: global threshold, adaptive threshold, or GrabCut segmentation.

- **Contour Detection**  
  Real-time or on-demand contour detection. Display contours with customizable color, thickness, and ID labels.

- **Manual Editing**  
  Draw new contours (polyline, rectangle, circle). Delete contours via box selection. Change individual contour colors.

- **Measurement Tools**  
  Calibrate scale (mm/pixel) by drawing a known distance or entering scale manually. Measure distances between any two points, display results in mm.

- **Area Analysis**  
  Automatic calculation of pixel area and real-world area for each detected contour. Export results to CSV.

- **Interactive Canvas**  
  Pan, zoom with mouse. Real-time updates. Collapsible result panel.

- **Save & Export**  
  Save annotated image. Export contour data (area, ID) to CSV.

---

## 🛠️ Tech Stack

| Category          | Libraries / Tools               |
| ----------------- | ------------------------------- |
| GUI               | Tkinter, ttk                    |
| Image Processing  | OpenCV (cv2)                    |
| Data Export       | CSV, openpyxl (optional)        |
| Image Conversion  | PIL (Pillow)                    |
| Concurrency       | threading, queue                |

---

## 📥 Installation & Usage

### Requirements
- Python 3.8 or higher
- pip

### Install Dependencies

```bash
pip install opencv-python pillow numpy
Run the Application
bash
python contour_analyzer.py
```

** 💡 It is recommended to use a virtual environment. **


## 🎯 Typical Use Cases
###
- PCB trace and component contour analysis

- Dimensional inspection of mechanical parts

- Educational tool for image processing (contours, thresholding)

- Quality control in small-scale manufacturing

- Research on object boundary extraction

## 📄 Author & Version
- Author: Federico

- Location: Shanghai

- Version: ECTV 2.3

- Last Update: 2025-10-27

## 📝 Change Log (V2.3)
- Added resize and hide functionality for the contour analysis result window

- Moved file operations to the image processing settings tab

- Added version and update info at the bottom

- Added contour color editing feature

- Added manual calibration input for scale factor

- UI changes: reduced right panel width by 30%, added measurement tab

## 📌 License
- MIT © Federico

## 🙌 Contributing
- Issues and pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.# AI_PCB_Analys

- ---------------------------------------------------------------------------------------------------------------------------------------------
# 轮廓分析工具 (Contour Analyzer)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)]()

**Contour Analyzer** 是一款轻量级桌面图像轮廓检测与测量工具，基于 Python + Tkinter + OpenCV 构建。适用于 PCB 照片、机械零件图像等场景中的轮廓提取、手动编辑、尺寸测量和面积统计分析。


---

## ✨ 主要功能

- **图像加载与处理**  
  支持 JPG、PNG、BMP 格式。可调整二值化阈值、去噪核大小、轮廓检索模式（外部轮廓 / 全部层级）。

- **感兴趣区域 (ROI)**  
  支持矩形框选 ROI，并选择处理算法：全局阈值、自适应阈值、GrabCut 分割。

- **轮廓检测**  
  实时或按需检测轮廓。可自定义轮廓颜色、线宽、是否显示编号。

- **手动编辑**  
  手绘轮廓（多点连线、矩形、圆形）。框选删除轮廓。支持修改单个轮廓颜色。

- **测量工具**  
  标定比例尺（mm/像素）：通过绘制已知距离或手动输入。测量任意两点间距离，结果以毫米显示。

- **面积分析**  
  自动计算每个轮廓的像素面积和实际面积。结果可导出为 CSV 文件。

- **交互式画布**  
  鼠标拖拽平移、滚轮缩放。实时更新显示。结果面板可折叠。

- **保存与导出**  
  保存带标注的图像。导出轮廓数据（面积、ID）到 CSV。

---

## 🛠️ 技术栈

| 类别           | 库/工具                       |
| -------------- | ----------------------------- |
| GUI 界面       | Tkinter, ttk                  |
| 图像处理       | OpenCV (cv2)                  |
| 数据导出       | CSV, openpyxl                 |
| 图像格式转换   | PIL (Pillow)                  |
| 并发处理       | threading, queue              |

---

## 📥 安装与使用

### 环境要求
- Python 3.8 或更高版本
- pip 包管理器

### 安装依赖

```bash
pip install opencv-python pillow numpy
```

运行程序
```bash
python contour_analyzer.py
```
** 💡 建议使用虚拟环境运行。

## 🎯 应用场景
- PCB 走线与元器件轮廓分析

- 机械零件尺寸检测

- 图像处理教学（轮廓、阈值分割）

- 小型制造中的质量检验

- 物体边界提取相关研究

## 📄 作者与版本
- 作者：Federico

- 所在地：上海

- 版本：ECTV 2.3

- 最后更新：2025-10-27

## 📝 更新日志 (V2.3)
- 新增功能：轮廓分析结果窗口大小调节和隐藏功能

- 将文件操作添加到图像处理设置页

- 底部添加版本和更新时间信息

- 添加轮廓颜色编辑功能

- 增加手动输入校准比例

- UI 变更：将右侧功能栏缩小 30%，添加尺寸测量页

## 📌 许可证
- MIT © Federico

## 🤝 贡献
- 欢迎提交 Issue 和 Pull Request。若有较大改动，请先开 Issue 讨论。
