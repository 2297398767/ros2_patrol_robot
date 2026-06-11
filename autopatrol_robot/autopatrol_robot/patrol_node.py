import rclpy
from geometry_msgs.msg import PoseStamped, Pose
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from tf2_ros import TransformListener, Buffer
from tf_transformations import euler_from_quaternion, quaternion_from_euler
from rclpy.duration import Duration
from autopatrol_interfaces.srv import SpeachText

from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2

class PatrolNode(BasicNavigator):
    def __init__(self, node_name='patrol_node'):
        super().__init__(node_name)
        # 导航相关定义：声明初始位姿和目标点集参数
        self.declare_parameter('initial_point', [0.0, 0.0, 0.0])
        self.declare_parameter('target_points', [0.0, 0.0, 0.0, 1.0, 1.0, 1.57])
        self.initial_point = self.get_parameter('initial_point').value
        self.target_points = self.get_parameter('target_points').value

        self.buffer = Buffer()
        self.listener = TransformListener(self.buffer, self)

        # 语音合成客户端
        self.speach_client_ = self.create_client(SpeachText, 'speech_text')

         # 订阅与保存图像相关定义
        self.declare_parameter('image_save_path', '')
        self.image_save_path = self.get_parameter('image_save_path').value
        self.bridge = CvBridge()
        self.latest_image = None
        self.subscription_image = self.create_subscription(
            Image, '/camera/image_raw', self.image_callback, 10)
    
    def get_pose_by_xyyaw(self, x, y, yaw):
        """通过 x, y, yaw 合成 PoseStamped"""
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.pose.position.x = x
        pose.pose.position.y = y
        rotation_quat = quaternion_from_euler(0, 0, yaw)
        pose.pose.orientation.x = rotation_quat[0]
        pose.pose.orientation.y = rotation_quat[1]
        pose.pose.orientation.z = rotation_quat[2]
        pose.pose.orientation.w = rotation_quat[3]
        return pose

    def init_robot_pose(self):
        """初始化机器人位姿"""
        # 从参数获取初始化点
        self.initial_point = self.get_parameter('initial_point').value
        # 合成位姿并调用底层的 setInitialPose 进行初始化
        self.setInitialPose(self.get_pose_by_xyyaw(
            self.initial_point[0], self.initial_point[1], self.initial_point[2]))
        # 等待直到导航激活
        self.waitUntilNav2Active()

    def get_target_points(self):
        """通过参数值获取目标点集合"""
        points = []
        self.target_points = self.get_parameter('target_points').value
        # 按三个一组的形式进行分割
        for index in range(int(len(self.target_points)/3)):
            x = self.target_points[index*3]
            y = self.target_points[index*3+1]
            yaw = self.target_points[index*3+2]
            points.append([x, y, yaw])
            self.get_logger().info(f'获取到目标点: {index}->({x}, {y}, {yaw})')
        return points

    def nav_to_pose(self, target_pose):
        """导航到指定位姿"""
        self.waitUntilNav2Active()
        self.goToPose(target_pose)

        while not self.isTaskComplete():
            feedback = self.getFeedback()
            if feedback:
                # 计算剩余时间 (秒)
                t = feedback.estimated_time_remaining.sec + \
                    feedback.estimated_time_remaining.nanosec / 1e9
                if t > 0.0:
                    self.get_logger().info(f'预计: {t:.1f} s 后到达')
                else:
                    self.get_logger().info('导航进行中...')
            
            # 必须加，否则回调不处理
            rclpy.spin_once(self, timeout_sec=0.2)

        # 最终结果判断
        result = self.getResult()
        if result == TaskResult.SUCCEEDED:
            self.get_logger().info('导航结果: 成功')
        elif result == TaskResult.CANCELED:
            self.get_logger().warn('导航结果: 被取消')
        elif result == TaskResult.FAILED:
            self.get_logger().error('导航结果: 失败')
        else:
            self.get_logger().error('导航结果: 返回状态无效')


    def get_current_pose(self):
        """通过 TF 获取当前位姿"""
        while rclpy.ok():
            try:
                tf = self.buffer.lookup_transform(
                    'map', 'base_footprint', rclpy.time.Time(seconds=0), rclpy.time.Duration(seconds=1))
                transform = tf.transform
                rotation_euler = euler_from_quaternion([
                    transform.rotation.x,
                    transform.rotation.y,
                    transform.rotation.z,
                    transform.rotation.w])
                self.get_logger().info(f'平移: {transform.translation}, 旋转欧拉角: {rotation_euler}')
                return transform
            except Exception as e:
                self.get_logger().warn(f'不能够获取坐标变换，原因: {str(e)}')


    def speach_text(self, text):
        """调用服务播放语音"""
        while not self.speach_client_.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('语音合成服务未上线,等待中...')
        request = SpeachText.Request()
        request.text = text
        future = self.speach_client_.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        if future.result() is not None:
            result = future.result().result
            if result:
                self.get_logger().info(f'语音合成成功:{text}')
            else:
                self.get_logger().warn(f'语音合成失败:{text}')
        else:
            self.get_logger().warn('语音合成服务请求失败')

    def image_callback(self, msg):
        """将最新的消息放到 latest_image 中"""
        self.latest_image = msg

    def record_image(self):
        """记录图像"""
        if self.latest_image is not None:
            pose = self.get_current_pose()
            if pose:
                cv_image = self.bridge.imgmsg_to_cv2(self.latest_image)
                # 拼接文件名：路径 + image_x_y.png，以当前坐标命名
                cv2.imwrite(f'{self.image_save_path}image_{pose.translation.x:.2f}_{pose.translation.y:.2f}.png', cv_image)



def main():
    rclpy.init()
    patrol = PatrolNode()
    patrol.init_robot_pose()

     # 【新增】：初始化前的语音播报
    patrol.speach_text(text='正在初始化位置')    
    # 【新增】：初始化完成的语音播报
    patrol.speach_text(text='位置初始化完成')
    
    # 无限循环巡检
    while rclpy.ok():
        points = patrol.get_target_points()
        for point in points:
            x, y, yaw = point[0], point[1], point[2]
            # 【新增】：导航前播报当前目标点
            patrol.speach_text(text=f'准备前往目标点{x},{y}')

            target_pose = patrol.get_pose_by_xyyaw(x, y, yaw)
            patrol.nav_to_pose(target_pose)

            # 记录图像
            patrol.speach_text(text=f"已到达目标点{x},{y},准备记录图像")
            patrol.record_image()
            patrol.speach_text(text="图像记录完成")
            
    rclpy.shutdown()

if __name__ == '__main__':
    main()