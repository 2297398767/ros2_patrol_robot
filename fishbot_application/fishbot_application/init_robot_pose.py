#!/usr/bin/env python3
import rclpy
from nav2_simple_commander.robot_navigator import BasicNavigator
from geometry_msgs.msg import PoseStamped

def main():
    rclpy.init()
    navigator = BasicNavigator()

    initial_pose = PoseStamped()
    initial_pose.header.frame_id = 'map'
    initial_pose.header.stamp = navigator.get_clock().now().to_msg()
    
    # 填入 Gazebo 中机器人的出生点坐标 (假设为原点)
    initial_pose.pose.position.x = 0.0 
    initial_pose.pose.position.y = 0.0
    initial_pose.pose.orientation.w = 1.0 

    print("🚀 正在发送初始位姿，唤醒 AMCL...")
    navigator.setInitialPose(initial_pose)
    
    navigator.waitUntilNav2Active()
    print("✅ Nav2 导航栈已全面激活！代价地图已生成！")
    rclpy.shutdown()

if __name__ == '__main__':
    main()