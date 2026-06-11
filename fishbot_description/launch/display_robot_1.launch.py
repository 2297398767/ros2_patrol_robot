import launch
import launch_ros
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # 获取默认路径
    urdf_tutorial_path = get_package_share_directory('fishbot_description')
    
    # 【核心修改 1】：将默认模型路径指向新的 xacro 总装配图
    default_model_path = urdf_tutorial_path + '/urdf/fishbot/fishbot.urdf.xacro' 
    default_rviz_config_path = urdf_tutorial_path + '/config/rviz/display_model.rviz'
    
    action_declare_arg_model_path = launch.actions.DeclareLaunchArgument(
        name='model', default_value=str(default_model_path),
        description='URDF 的绝对路径')
        
    # 【核心修改 2】：将原来的 ['cat ', ...] 改为 ['xacro ', ...]
    robot_description = launch_ros.parameter_descriptions.ParameterValue(
        launch.substitutions.Command(
            ['xacro ', launch.substitutions.LaunchConfiguration('model')]),
        value_type=str)
        
    # 状态发布节点 (RSP)
    robot_state_publisher_node = launch_ros.actions.Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description}]
    )
    
    # 关节状态发布节点 (JSP)
    joint_state_publisher_node = launch_ros.actions.Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
    )
    
    # RViz 节点
    rviz_node = launch_ros.actions.Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', default_rviz_config_path] # <--- 加上这一行
    )
    
    return launch.LaunchDescription([
        action_declare_arg_model_path,
        joint_state_publisher_node,
        robot_state_publisher_node,
        rviz_node
    ])