import struct
import numpy as np
from typing import NamedTuple, List, Tuple, Dict, Optional
import os
import open3d as o3d
import re

class PointCloudData(NamedTuple):
    x: float  # mm
    y: float  # mm
    z: float  # mm
    r: int
    g: int
    b: int
    wPos: int
    hPos: int

class DetectionResult(NamedTuple):
    region_id: int
    center_x: int
    center_y: int
    radius: int

def parse_detection_results(txt_path: str) -> List[DetectionResult]:
    """解析检测结果txt文件"""
    results = []
    with open(txt_path, 'r') as f:
        content = f.read()
    
    # 使用正则表达式提取检测结果
    pattern = r"区域(\d+)检测结果:\n圆心坐标\(原图\): \((\d+), (\d+)\)\n半径: (\d+)像素"
    matches = re.findall(pattern, content)
    
    for match in matches:
        region_id = int(match[0])
        center_x = int(match[1])
        center_y = int(match[2])
        radius = int(match[3])
        results.append(DetectionResult(region_id, center_x, center_y, radius))
    
    return results

def read_lc_pcd_file(file_path: str) -> Tuple[dict, List[PointCloudData]]:
    """读取13字节/点格式的.lc_pcd文件"""
    HEADER_SIZE = 256
    XOR_KEY = 0x9C
    POINT_SIZE = 13
    
    with open(file_path, 'rb') as f:
        # 读取并解密头部
        encrypted_header = f.read(HEADER_SIZE)
        decrypted_header = bytes([b ^ XOR_KEY for b in encrypted_header])
        
        # 解析头部
        header_fields = struct.unpack('<7I', decrypted_header[:28])
        header_dict = {
            'version': header_fields[0],
            'point_count': header_fields[1],
            'data_size': header_fields[2],
            'width': header_fields[3],
            'height': header_fields[4],
            'color_type': 'GRAY' if header_fields[5] == 0 else 'COLOR',
            'ratio': header_fields[6],
            'reserved': decrypted_header[28:HEADER_SIZE]
        }
        
        # 读取点云数据
        data_bytes = f.read()
        points = []
        
        for i in range(header_dict['point_count']):
            offset = i * POINT_SIZE
            point_data = data_bytes[offset:offset+POINT_SIZE]
            
            r, g, b = point_data[0], point_data[1], point_data[2]
            x, y, z, wPos, hPos = struct.unpack('<5h', point_data[3:13])
            
            points.append(PointCloudData(
                x=x * 0.1, y=y * 0.1, z=z * 0.1,
                r=r, g=g, b=b,
                wPos=wPos, hPos=hPos
            ))
    
    return header_dict, points

def visualize_point_cloud(points: List[PointCloudData], detection_results: Optional[List[DetectionResult]] = None):
    """使用open3d可视化点云，并标记检测区域"""
    # 转换为numpy数组
    xyz = np.array([(p.x, p.y, p.z) for p in points])
    rgb = np.array([(p.r/255, p.g/255, p.b/255) for p in points])
    
    # 创建open3d点云对象
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(xyz)
    pcd.colors = o3d.utility.Vector3dVector(rgb)
    
    # 计算边界框用于参考
    bbox = o3d.geometry.AxisAlignedBoundingBox.create_from_points(pcd.points)
    
    # 可视化设置
    vis = o3d.visualization.Visualizer()
    vis.create_window(window_name='3D点云可视化(带检测区域)', width=1000, height=800)
    vis.add_geometry(pcd)
    vis.add_geometry(bbox)
    
    # 添加坐标系
    coordinate_frame = o3d.geometry.TriangleMesh.create_coordinate_frame(size=200, origin=[0,0,0])
    vis.add_geometry(coordinate_frame)
    
    # 如果有检测结果，标记对应区域
    if detection_results:
        # 创建一个字典，按图像位置快速查找点
        pos_to_point = {(p.wPos, p.hPos): p for p in points}
        
        # 为每个检测区域创建标记
        for result in detection_results:
            # 找到检测区域内的点
            region_points = []
            for p in points:
                distance = np.sqrt((p.wPos - result.center_x)**2 + (p.hPos - result.center_y)**2)
                if distance <= result.radius:
                    region_points.append(p)
            
            if region_points:
                # 创建标记点云
                region_xyz = np.array([(p.x, p.y, p.z) for p in region_points])
                region_rgb = np.array([[1, 0, 0] for _ in region_points])  # 红色标记
                
                region_pcd = o3d.geometry.PointCloud()
                region_pcd.points = o3d.utility.Vector3dVector(region_xyz)
                region_pcd.colors = o3d.utility.Vector3dVector(region_rgb)
                vis.add_geometry(region_pcd)
                
                # 添加标签 - 使用球体标记代替文本
                if region_xyz.shape[0] > 0:
                    center_3d = np.mean(region_xyz, axis=0)
                    sphere = o3d.geometry.TriangleMesh.create_sphere(radius=10)
                    sphere.paint_uniform_color([1, 0, 0])  # 红色
                    sphere.translate(center_3d)
                    #vis.add_geometry(sphere)
    
    # 设置视角
    view_ctl = vis.get_view_control()
    view_ctl.set_front([0, -1, 0])  # 设置相机朝前向量
    view_ctl.set_up([0, 0, 1])     # 设置相机朝上向量
    
    # 渲染选项
    render_opt = vis.get_render_option()
    render_opt.point_size = 2.0
    render_opt.background_color = np.array([0.1, 0.1, 0.1])
    
    print("\n正在显示3D点云...")
    print("操作指南:")
    print("- 鼠标左键拖动: 旋转视角")
    print("- 鼠标右键拖动: 平移视图")
    print("- 滚轮: 缩放")
    print("- 按Q键退出可视化窗口")
    
    vis.run()
    vis.destroy_window()

if __name__ == "__main__":
    try:
        # 文件路径设置
        pic_folder = '20250616194552'
        base_dir = f'/home/jzp/桌面/CircleDetect/data/pic/{pic_folder}/2-1'
        
        # 查找点云文件
        pcd_files = [f for f in os.listdir(base_dir) if f.lower().endswith('.lc_pcd')]
        if not pcd_files:
            raise FileNotFoundError("未找到.lc_pcd文件")
        pcd_path = os.path.join(base_dir, pcd_files[0])
        
        # 查找检测结果文件
        img_name = os.path.splitext(pcd_files[0])[0]
        result_dir = os.path.join(base_dir, 'detection_results')
        txt_path = os.path.join(result_dir, f'{img_name}_results.txt')
        
        detection_results = None
        if os.path.exists(txt_path):
            print(f"找到检测结果文件: {txt_path}")
            detection_results = parse_detection_results(txt_path)
            print(f"解析到{len(detection_results)}个检测区域")
        else:
            print("未找到检测结果文件，将显示原始点云")
        
        print(f"\n正在读取点云文件: {pcd_path}")
        
        # 读取点云数据
        header, points = read_lc_pcd_file(pcd_path)
        
        # 打印基本信息
        print("\n头部信息:")
        for k, v in header.items():
            print(f"{k}: {v}")
        
        print(f"\n成功读取{len(points)}个点")
        if len(points) > 0:
            print("\n第一个点示例:")
            print(f"位置(mm): ({points[0].x:.1f}, {points[0].y:.1f}, {points[0].z:.1f})")
            print(f"颜色(RGB): ({points[0].r}, {points[0].g}, {points[0].b})")
            print(f"图像位置: ({points[0].wPos}, {points[0].hPos})")
            
            # 计算坐标范围
            xyz = np.array([(p.x, p.y, p.z) for p in points])
            print("\n坐标范围(mm):")
            print(f"X: {xyz[:,0].min():.1f} 到 {xyz[:,0].max():.1f}")
            print(f"Y: {xyz[:,1].min():.1f} 到 {xyz[:,1].max():.1f}")
            print(f"Z: {xyz[:,2].min():.1f} 到 {xyz[:,2].max():.1f}")
            
            # 可视化点云
            visualize_point_cloud(points, detection_results)

            print("第一个点：", points[0])
        
    except Exception as e:
        print(f"\n错误: {str(e)}")