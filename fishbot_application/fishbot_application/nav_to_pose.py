#!/usr/bin/env python3
import rclpy
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from geometry_msgs.msg import PoseStamped

def main():
    rclpy.init()
    navigator = BasicNavigator()
    # 确保 Nav2 已经就绪
    navigator.waitUntilNav2Active()

    # 封装目标点
    goal_pose = PoseStamped()
    goal_pose.header.frame_id = 'map'
    goal_pose.header.stamp = navigator.get_clock().now().to_msg()
    goal_pose.pose.position.x = 2.0 
    goal_pose.pose.position.y = 1.0 
    goal_pose.pose.orientation.w = 1.0 

    print("🏁 正在前往单点目标...")
    navigator.goToPose(goal_pose)

    # 循环读取反馈
    while not navigator.isTaskComplete():
        feedback = navigator.getFeedback()
        if feedback:
            print(f"剩余距离: {feedback.distance_remaining:.2f} 米", end='\r')

    # 获取结果
    if navigator.getResult() == TaskResult.SUCCEEDED:
        print('\n🎯 成功到达目标点！')
    else:
        print('\n❌ 导航失败！')
        
    rclpy.shutdown()

if __name__ == '__main__':
    main()