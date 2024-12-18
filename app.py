import sys
import cv2
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QFileDialog, 
                             QCheckBox, QStackedWidget, QGridLayout)
from PyQt5.QtGui import QImage, QPixmap, QFont
from PyQt5.QtCore import Qt, QTimer
from detect import detect_barcode
from decode import decode_barcode

TITLE = ['Gradient Subtraction', 'Thresholding', 'Morphology', 'Erode/Dilate']
KEY = ['gradient-sub', 'threshed', 'morphology', 'erode/dilate']


class CameraSection(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setup_camera()

    def initUI(self):
        layout = QHBoxLayout()

        # Bên trái: Hiển thị video
        self.video_label = QLabel()
        self.video_label.setMinimumSize(640, 480)

        # Bên phải: Khu vực thông tin
        right_section = QVBoxLayout()

        # Tiêu đề
        self.title_label = QLabel("EAN-13:")
        self.title_label.setFont(QFont('Arial', 16))
        right_section.addWidget(self.title_label)

        # 4 ảnh nhỏ
        self.image_labels = []
        self.image_captions = []
        image_grid = QGridLayout()
        captions = ['Gradient Subtraction', 'Thresholding', 'Morphology', 'Erode/Dilate']
        
        for i in range(2):
            for j in range(2):
                img_label = QLabel()
                img_label.setFixedSize(150, 150)
                img_label.setStyleSheet("border: 1px solid black;")
                
                caption_label = QLabel(captions[i*2 + j])
                caption_label.setAlignment(Qt.AlignCenter)
                
                image_grid.addWidget(img_label, i*2, j)
                image_grid.addWidget(caption_label, i*2+1, j)
                
                self.image_labels.append(img_label)
                self.image_captions.append(caption_label)

        right_section.addLayout(image_grid)

        # Checkbox
        self.checkbox = QCheckBox("Hiển thị detect box")
        right_section.addWidget(self.checkbox)

        layout.addWidget(self.video_label)
        layout.addLayout(right_section)

        self.setLayout(layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

    def setup_camera(self):
        self.capture = cv2.VideoCapture(0)
        self.timer.start(30)  # Cập nhật mỗi 30ms

    def update_frame(self):
        ret, frame = self.capture.read()
        if ret:
            
            box, detail = detect_barcode(frame)
            
            if box is not None:
                if self.checkbox.isChecked():
                    # Draw the bounding box around the barcode
                    cv2.drawContours(frame, [box], -1, (0, 255, 0), 2)
                    
                    self.update_images([detail[key] for key in KEY])
                    
                x, y, w, h = cv2.boundingRect(box)
                
                if x > 0 and y > 0 and x+w < frame.shape[1] and y+h < frame.shape[0]:
                    cropped_img = frame[y:y+h, x:x+w]
                    ean13, is_valid, thresh = decode_barcode(cropped_img)

                    if is_valid:
                        # Draw the bounding box around the barcode
                        cv2.drawContours(frame, [box], -1, (0, 255, 0), 2)
                        
                        self.update_title(f"EAN-13: {ean13}")
                        
                        if not self.checkbox.isChecked():
                            self.update_images([detail[key] for key in KEY])
                        
                        # Put the decoded EAN-13 code text above the bounding box
                        cv2.putText(frame, ean13, (x, y - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_frame.data, w, h,
                              bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            self.video_label.setPixmap(
                pixmap.scaled(640, 480, Qt.KeepAspectRatio))

    def update_title(self, title):
        self.title_label.setText(title)

    def update_images(self, images):
        for i in range(min(4, len(images))):
            rgb_image = cv2.cvtColor(images[i], cv2.COLOR_GRAY2RGB)
            
            # Tạo QImage từ numpy array
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # Tạo Pixmap và scale
            pixmap = QPixmap.fromImage(qt_image)
            self.image_labels[i].setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio))


class FileSection(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.image_label = QLabel("Chọn File Ảnh")
        self.image_label.setAlignment(Qt.AlignCenter)

        select_button = QPushButton("Chọn File")
        select_button.clicked.connect(self.select_file)

        layout.addWidget(self.image_label)
        layout.addWidget(select_button)

        self.setLayout(layout)

    def select_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Chọn ảnh", "", "Image Files (*.png *.jpg *.jpeg *.gif)")
        if filename:
            img = cv2.imread(filename)
            
            box, detail = detect_barcode(img)
            
            if box is not None:
                x, y, w, h = cv2.boundingRect(box)
                
                if x > 0 and y > 0 and x+w < img.shape[1] and y+h < img.shape[0]:
                    cropped_img = img[y:y+h, x:x+w]
                    ean13, is_valid, thresh = decode_barcode(cropped_img)

                    if is_valid:
                        # Draw the bounding box around the barcode
                        cv2.drawContours(img, [box], -1, (0, 255, 0), 5)
                        
                        # Put the decoded EAN-13 code text above the bounding box
                        cv2.putText(img, ean13, (x, y - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 5)
                        
                        self.image_label.setText(f"EAN-13: {ean13}")
                        
            rgb_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h,
                              bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            self.image_label.setPixmap(
                pixmap.scaled(640, 480, Qt.KeepAspectRatio))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Barcode Scanner')
        self.setGeometry(100, 100, 1000, 600)

        central_widget = QWidget()
        main_layout = QVBoxLayout()

        # Nút chọn chế độ
        mode_layout = QHBoxLayout()
        camera_btn = QPushButton("Mở Camera")
        file_btn = QPushButton("Chọn File")

        mode_layout.addWidget(camera_btn)
        mode_layout.addWidget(file_btn)

        main_layout.addLayout(mode_layout)

        # Stacked widget để chuyển giữa các chế độ
        self.stacked_widget = QStackedWidget()
        self.camera_section = CameraSection()
        self.file_section = FileSection()

        self.stacked_widget.addWidget(self.camera_section)
        self.stacked_widget.addWidget(self.file_section)

        main_layout.addWidget(self.stacked_widget)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Kết nối sự kiện
        camera_btn.clicked.connect(
            lambda: self.stacked_widget.setCurrentIndex(0))
        file_btn.clicked.connect(
            lambda: self.stacked_widget.setCurrentIndex(1))


def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
