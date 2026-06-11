import os
import launch
import launch_ros
from ament_index_python.packages import get_package_share_directory
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    # 获取参数文件路径
    autopatrol_robot_dir = get_package_share_directory('autopatrol_robot')
    patrol_config_path = os.path.join(autopatrol_robot_dir, 'config', 'patrol_config.yaml')
    
    # 巡检总管节点
    action_node_turtle_control = launch_ros.actions.Node(
        package='autopatrol_robot',
        executable='patrol_node',
        parameters=[patrol_config_path])
        
    # 语音播报节点
    action_node_patrol_client = launch_ros.actions.Node(
        package='autopatrol_robot',
        executable='speaker')
        
    return launch.LaunchDescription([
        action_node_turtle_control,
        action_node_patrol_client,
    ])