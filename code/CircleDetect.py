# 图像尺寸 2448×2048
# 圆半径20像素点
# 988,880  1145,882     
# 989,1387 1138,1385
import cv2
import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib
import shutil

# 设置matplotlib默认字体为Noto Sans CJK系列，确保中文正常显示
#matplotlib.rcParams['font.family'] = 'Noto Sans CJK JP'

# 读取灰度图片 - 修改为相对路径
base_dir = os.path.join('data', 'pic', '20250616194552', '2-1')
# 创建结果保存目录（先删除已存在的文件夹）
result_dir = os.path.join(base_dir, 'detection_results')
if os.path.exists(result_dir):
    shutil.rmtree(result_dir)
os.makedirs(result_dir)

# 自动找到2-1下的第一个png图片
png_files = [f for f in os.listdir(base_dir) if f.lower().endswith('.png')]
if not png_files:
    raise FileNotFoundError("未找到png图片")
img_path = os.path.join(base_dir, png_files[0])
image_rgb = cv2.imread(img_path)
img_gray = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
hsv = cv2.cvtColor(image_rgb, cv2.COLOR_BGR2HSV)
_, img_binary = cv2.threshold(img_gray, 50, 255, cv2.THRESH_BINARY)

img = img_gray

# 读取xml标注文件并显示
img_name = os.path.splitext(png_files[0])[0]
xml_path = os.path.join(base_dir, f'{img_name}.xml')
if not os.path.exists(xml_path):
    raise FileNotFoundError(f"未找到xml标注文件: {xml_path}")

# 解析xml文件，提取标注框坐标
import xml.etree.ElementTree as ET

tree = ET.parse(xml_path)
root = tree.getroot()

boxes = []
for obj in root.findall('.//object'):
    bndbox = obj.find('bndbox')
    if bndbox is not None:
        xmin = int(bndbox.find('xmin').text)
        ymin = int(bndbox.find('ymin').text)
        xmax = int(bndbox.find('xmax').text)
        ymax = int(bndbox.find('ymax').text)
        boxes.append([xmin, ymin, xmax, ymax])

# 在原图上绘制标注框
img_boxes = image_rgb.copy()
for box in boxes:
    cv2.rectangle(img_boxes, (box[0], box[1]), (box[2], box[3]), (255, 0, 0), 2)

# 保存并显示带有标注框的图像
plt.figure(figsize=(12, 10))
plt.imshow(cv2.cvtColor(img_boxes, cv2.COLOR_BGR2RGB))
plt.title('Image with Annotations')
plt.axis('off')
plt.savefig(os.path.join(result_dir, f'{img_name}_boxes_plt.png'), bbox_inches='tight', dpi=300)
plt.show()

# 创建结果文本文件
result_txt_path = os.path.join(result_dir, f'{img_name}_results.txt')
with open(result_txt_path, 'w') as f:
    f.write(f"检测结果 - {img_name}\n")
    f.write("="*50 + "\n")

# 整合两个for循环
for idx, box in enumerate(boxes[:4]):
    # 提取标注区域
    cropped_img = image_rgb[box[1]:box[3], box[0]:box[2]]
    gray = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2GRAY)
    # HoughCircles 检测圆
    circles = cv2.HoughCircles(
        gray,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=100,
        param1=30,
        param2=10,
        minRadius=15,
        maxRadius=30
    )
    if circles is not None:
        circles = np.uint16(np.around(circles[0, :]))
        best_circle = circles[0]
        x, y, r = best_circle
        # 将圆心坐标转换为原图中的坐标
        x_global = box[0] + x
        y_global = box[1] + y
        # 在原图上绘制圆和圆心
        cv2.circle(image_rgb, (x_global, y_global), r, (0, 255, 0), 2)
        cv2.circle(image_rgb, (x_global, y_global), 2, (0, 0, 255), 3)
        # 在标注框区域绘制圆和圆心
        cv2.circle(cropped_img, (x, y), r, (0, 255, 0), 1)
        cv2.circle(cropped_img, (x, y), 2, (0, 0, 255), 1)
        
        # 记录检测结果
        with open(result_txt_path, 'a') as f:
            f.write(f"区域{idx+1}检测结果:\n")
            f.write(f"圆心坐标(原图): ({x_global}, {y_global})\n")
            f.write(f"半径: {r}像素\n")
            f.write("-"*50 + "\n")
    else:
        print(f"区域{idx+1}未检测到圆")
        with open(result_txt_path, 'a') as f:
            f.write(f"区域{idx+1}未检测到圆\n")
            f.write("-"*50 + "\n")

# 保存并显示原图结果
plt.figure(figsize=(12, 10))
plt.imshow(cv2.cvtColor(image_rgb, cv2.COLOR_BGR2RGB))
plt.title('Image with Detected Circles')
plt.axis('off')
plt.savefig(os.path.join(result_dir, f'{img_name}_final_plt.png'), bbox_inches='tight', dpi=300)
plt.show()

print(f"所有检测结果已保存到: {os.path.abspath(result_dir)}")