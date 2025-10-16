import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QFileDialog, QVBoxLayout, QWidget,
    QHBoxLayout, QCheckBox, QScrollArea, QMessageBox, QLineEdit, QFormLayout, QFrame
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt


class ImageEnhancerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图像增强应用 v3.2（多图支持）")
        self.setGeometry(200, 100, 2560, 1600)

        self.original_images = []  # ✅ 支持多张图片
        self.results = {}

        # ======= 左右布局 =======
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        # --- 左侧：原图显示 ---
        self.label_original = QLabel("原图区域")
        self.label_original.setAlignment(Qt.AlignCenter)
        self.label_original.setStyleSheet("border: 1px solid gray; background-color: #fafafa;")

        self.btn_open = QPushButton("打开图片（可多选）")
        self.btn_open.clicked.connect(self.open_image)

        left_layout.addWidget(self.label_original, stretch=5)
        left_layout.addWidget(self.btn_open, stretch=1)

        # --- 右侧：紧凑多选增强 + 参数输入 ---
        self.form_layout = QFormLayout()
        self.form_layout.setLabelAlignment(Qt.AlignLeft)
        self.form_layout.setFormAlignment(Qt.AlignTop)
        self.form_layout.setVerticalSpacing(3)
        self.form_layout.setHorizontalSpacing(5)

        # 复选框 + 参数输入框
        self.options = {
            "灰度化": (QCheckBox("灰度化"), None),
            "直方图均衡化": (QCheckBox("直方图均衡化"), None),
            "锐化": (QCheckBox("锐化"), None),
            "均值滤波": (QCheckBox("均值滤波"), QLineEdit("3")),
            "中值滤波": (QCheckBox("中值滤波"), QLineEdit("3")),
            "高斯模糊": (QCheckBox("高斯模糊"), QLineEdit("5")),
            "边缘检测": (QCheckBox("边缘检测"), None),
            "去噪": (QCheckBox("去噪"), None),
            "腐蚀": (QCheckBox("腐蚀"), QLineEdit("3")),
            "膨胀": (QCheckBox("膨胀"), QLineEdit("3")),
        }

        for name, (cb, param) in self.options.items():
            cb.setFixedHeight(20)
            cb.setStyleSheet("font-size: 10pt")
            row = QHBoxLayout()
            row.addWidget(cb)
            if param:
                param.setFixedWidth(40)
                row.addWidget(QLabel("参数:"))
                row.addWidget(param)
            wrapper = QWidget()
            wrapper.setLayout(row)
            self.form_layout.addRow(wrapper)

        # --- 操作按钮 ---
        self.btn_process = QPushButton("执行增强")
        self.btn_process.clicked.connect(self.apply_selected_enhancements)
        self.btn_save = QPushButton("保存全部结果")
        self.btn_save.clicked.connect(self.save_all_results)

        # --- 滚动结果显示 ---
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout()
        self.scroll_widget.setLayout(self.scroll_layout)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_widget)

        # --- 整合右侧布局 ---
        right_layout.addLayout(self.form_layout, stretch=2)
        right_layout.addWidget(self.btn_process)
        right_layout.addWidget(self.btn_save)
        right_layout.addWidget(self.scroll_area, stretch=5)

        # --- 合并左右布局 ---
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 3)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    # 打开图片（支持多选）
    def open_image(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "选择图片", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if not paths:
            return

        self.original_images = [cv2.imread(p) for p in paths if p]
        self.clear_results()

        # 显示第一张图或提示多图
        if len(self.original_images) == 1:
            self.show_image(self.label_original, self.original_images[0])
        else:
            self.label_original.setText(f"已选择 {len(self.original_images)} 张图片")
            self.label_original.setStyleSheet("border: 1px solid gray; background-color: #f0f0f0; font-weight: bold;")

    # 清空右侧结果区
    def clear_results(self):
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.takeAt(i).widget()
            if widget:
                widget.deleteLater()
        self.results = {}

    # 显示图片
    def show_image(self, label, cv_img):
        rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        q_img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        label.setPixmap(QPixmap.fromImage(q_img).scaled(
            label.width(), label.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))

    # 应用选中的增强方式（多图支持）
    def apply_selected_enhancements(self):
        if not self.original_images:
            QMessageBox.warning(self, "提示", "请先打开图片！")
            return

        self.clear_results()

        for idx, img in enumerate(self.original_images):
            for name, (cb, param) in self.options.items():
                if cb.isChecked():
                    value = int(param.text()) if param and param.text().isdigit() else None
                    result = self.apply_filter(img.copy(), name, value)
                    key = f"{name}_img{idx+1}"
                    self.results[key] = result
                    self.add_result_preview(f"{name}（第{idx+1}张）", result)

    # 添加结果预览
    def add_result_preview(self, name, img):
        frame = QFrame()
        layout = QVBoxLayout()
        label = QLabel(name)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-weight: bold;")
        img_label = QLabel()
        img_label.setAlignment(Qt.AlignCenter)
        img_label.setFixedSize(300, 300)
        img_label.setStyleSheet("border: 1px solid gray;")
        self.show_image(img_label, img)
        layout.addWidget(label)
        layout.addWidget(img_label)
        frame.setLayout(layout)
        self.scroll_layout.addWidget(frame)

    # 图像处理逻辑
    def apply_filter(self, img, name, param):
        try:
            if name == "灰度化":
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            elif name == "直方图均衡化":
                img_yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
                img_yuv[:, :, 0] = cv2.equalizeHist(img_yuv[:, :, 0])
                img = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)
            elif name == "锐化":
                kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
                img = cv2.filter2D(img, -1, kernel)
            elif name == "均值滤波":
                k = param if param else 3
                img = cv2.blur(img, (k, k))
            elif name == "中值滤波":
                k = param if param else 3
                img = cv2.medianBlur(img, k)
            elif name == "高斯模糊":
                k = param if param else 5
                img = cv2.GaussianBlur(img, (k, k), 0)
            elif name == "边缘检测":
                img = cv2.Canny(img, 100, 200)
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            elif name == "去噪":
                img = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
            elif name == "腐蚀":
                k = param if param else 3
                kernel = np.ones((k, k), np.uint8)
                img = cv2.erode(img, kernel, iterations=1)
            elif name == "膨胀":
                k = param if param else 3
                kernel = np.ones((k, k), np.uint8)
                img = cv2.dilate(img, kernel, iterations=1)
        except Exception as e:
            print(f"处理 {name} 时出错：{e}")
        return img

    # 保存所有结果
    def save_all_results(self):
        if not self.results:
            QMessageBox.information(self, "提示", "没有结果可以保存。")
            return
        folder = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if not folder:
            return
        for name, img in self.results.items():
            cv2.imwrite(f"{folder}/{name}.png", img)
        QMessageBox.information(self, "完成", f"已保存 {len(self.results)} 张图片。")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageEnhancerApp()
    window.show()
    sys.exit(app.exec_())
