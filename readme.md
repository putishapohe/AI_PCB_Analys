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
