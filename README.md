# 圆形检测与点云可视化系统

## 项目概述

本项目是一个集成了2D图像处理和3D点云可视化的系统，主要功能包括：
1. 在2D图像中检测指定区域内的圆形目标
2. 将检测结果映射到3D点云中进行可视化展示

## 文件结构
data/
└── pic/
└── [日期时间文件夹]/
└── 2-1/
├── [图像文件].png # 原始图像
├── [图像文件].xml # 标注文件
├── [点云文件].lc_pcd # 点云数据
└── detection_results/ # 自动生成的检测结果
├── [图像名]_boxes_plt.png # 标注区域可视化
├── [图像名]_final_plt.png # 检测结果可视化
└── [图像名]_results.txt # 检测结果文本

text

## 快速开始

1. **准备数据**：
   ```bash
   mkdir -p data/pic/20250616194552/2-1
   # 将.png、.xml和.lc_pcd文件放入上述目录
运行圆形检测：

bash
python CircleDetect.py
可视化点云：

bash
python showROIpcd.py
模块详细说明
1. CircleDetect.py
功能特点
自动检测图像中的圆形目标

支持基于XML标注的ROI区域检测

生成可视化结果和检测报告

关键参数配置
python
# 可调整的霍夫圆检测参数
HoughCircles(
    dp=1,          # 分辨率反比
    minDist=100,    # 圆心最小间距
    param1=30,      # Canny高阈值
    param2=10,      # 累加器阈值
    minRadius=15,   # 最小半径
    maxRadius=30    # 最大半径
)
输出示例
圆形检测结果：
![圆形检测结果](https://github.com/user-attachments/assets/2fef760e-f61a-4690-9684-1d2f41171841)

2. showROIpcd.py
功能特点
支持加密的.lc_pcd点云格式

3D可视化检测结果

交互式查看功能

点云数据结构
字节范围	数据类型	说明
0-2	uint8	RGB颜色
3-12	5×int16	x,y,z坐标和图像位置
交互控制
操作	功能
左键拖动	旋转视角
右键拖动	平移视图
滚轮	缩放
Q键	退出
依赖安装
bash
pip install opencv-python numpy matplotlib open3d lxml

输出示例
对应点云标注：
![对应点云标注](https://github.com/user-attachments/assets/c5bdc893-e176-4381-8baf-0677ee10fc63)
