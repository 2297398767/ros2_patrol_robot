#!/usr/bin/env python3
import math
import rclpy
from rclpy.node import Node
from tf2_ros import TransformException
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener

def get_yaw_from_quaternion(x, y, z, w):
    """
    将四元数转换为偏航角 (Yaw)，返回弧度值
    """
    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (y * y + z * z)
    yaw = math.atan2(t3, t4)
    return yaw


class RobotPoseListener(Node):
    def __init__(self):
        super().__init__('robot_pose_listener')
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        # 每隔 1 秒调用一次获取位置的函数
        self.timer = self.create_timer(1.0, self.get_pose)

    def get_pose(self):
        try:
            # 监听从 map 到 base_footprint 的最新 TF 变换
            t = self.tf_buffer.lookup_transform('map', 'base_footprint', rclpy.time.Time())
            x = t.transform.translation.x
            y = t.transform.translation.y

            # 获取旋转四元数
            qx = t.transform.rotation.x
            qy = t.transform.rotation.y
            qz = t.transform.rotation.z
            qw = t.transform.rotation.w

            # 计算偏航角 (弧度)
            yaw_rad = get_yaw_from_quaternion(qx, qy, qz, qw)
            
            # 直接打印坐标和弧度朝向
            self.get_logger().info(
                f'📍 实时位姿: X={x:.2f}, Y={y:.2f}, 朝向={yaw_rad:.2f} rad'
            )
        except TransformException as ex:
            self.get_logger().info(f'等待 TF 变换: {ex}')

def main():
    rclpy.init()
    node = RobotPoseListener()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()