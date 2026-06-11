#!/usr/bin/env python3
import rclpy
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from geometry_msgs.msg import PoseStamped

# 辅助函数：快速生成位姿对象
def create_pose(navigator, x, y):
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.header.stamp = navigator.get_clock().now().to_msg()
    pose.pose.position.x = x
    pose.pose.position.y = y
    pose.pose.orientation.w = 1.0
    return pose

def main():
    rclpy.init()
    navigator = BasicNavigator()
    navigator.waitUntilNav2Active()

    # 创建目标点列表 (根据迷宫地图坐标设定)
    waypoints = [
        create_pose(navigator, 2.0, 0.0),
        create_pose(navigator, 2.0, -2.0),
        create_pose(navigator, 0.0, -2.0),
        create_pose(navigator, 0.0, 0.0) # 闭环回到起点
    ]

    print("🛸 开始执行多路点自动巡检...")
    navigator.followWaypoints(waypoints)

    while not navigator.isTaskComplete():
        feedback = navigator.getFeedback()
        if feedback:
            # current_waypoint 索引从0开始，所以+1
            print(f"正在前往第 {feedback.current_waypoint + 1} 个目标点...", end='\r')

    if navigator.getResult() == TaskResult.SUCCEEDED:
        print('\n🎉 完美！所有巡检点已走完！')
        
    rclpy.shutdown()

if __name__ == '__main__':
    main()