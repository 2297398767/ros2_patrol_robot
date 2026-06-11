#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TwistStamped

class TwistStamper(Node):
    def __init__(self):
        super().__init__('twist_stamper')
        
        # 创建一个发布者，发布带时间戳的速度指令给控制器
        self.stamped_pub = self.create_publisher(
            TwistStamped,
            '/fishbot_diff_drive_controller/cmd_vel', 
            10)
            
        # 订阅键盘发布的普通速度指令
        self.unstamped_sub = self.create_subscription(
            Twist,
            '/cmd_vel',  
            self.callback,
            10)
            
        self.get_logger().info('Twist Stamper node has been started.')

    def callback(self, msg: Twist):
        stamped_msg = TwistStamped()
        # 🌟 核心：填充 header，获取当前时间戳
        stamped_msg.header.stamp = self.get_clock().now().to_msg()
        stamped_msg.header.frame_id = ""  
        stamped_msg.twist = msg
        self.stamped_pub.publish(stamped_msg)

def main(args=None):
    rclpy.init(args=args)
    node = TwistStamper()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()