import os
import launch
import launch_ros
from ament_index_python.packages import get_package_share_directory
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    pkg_fishbot_description = get_package_share_directory('fishbot_description')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    # 1. 解析 Xacro 文件
    default_model_path = os.path.join(pkg_fishbot_description, 'urdf', 'fishbot', 'fishbot.urdf.xacro')
    robot_description = launch_ros.parameter_descriptions.ParameterValue(
        launch.substitutions.Command(['xacro ', default_model_path]), value_type=str
    )
    
    # 2. 启动 Robot State Publisher (RSP)
    robot_state_publisher_node = launch_ros.actions.Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[
            {'robot_description': robot_description},
            {'use_sim_time': True}  # 重点：告诉节点使用仿真时间
        ]
    )

    # 3. 启动 Gazebo Harmonic 并加载本地的迷宫地图
    world_path = os.path.join(pkg_fishbot_description, 'world', 'slam_maze.sdf')
    gz_sim_cmd = launch.actions.IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': f'-r {world_path}'}.items() # -r 表示启动后自动 Run
    )

    # 4. 将机器人注入到 Gazebo 中（Harmonic 新版写法）
    spawn_entity_node = launch_ros.actions.Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'fishbot',
            '-topic', '/robot_description',
            '-z', '0.5' # 💡 排坑：让机器人从 0.5 米的高空落下，防止初始穿模导致物理大爆炸
        ],
        output='screen'
    )

    # 5. 加载 Bridge 通信桥梁
    diff_drive_bridge_config = os.path.join(pkg_fishbot_description, 'config', 'gz_bridge_diff_drive.yaml')
    diff_drive_bridge_node = launch_ros.actions.Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '--ros-args',
            '-p',
            f'config_file:={diff_drive_bridge_config}'
        ],
        parameters=[{'use_sim_time': True}],  # 必须同步仿真时钟
        output='screen'
    )

    # 6. 启动 RViz 
    rviz_config_path = os.path.join(pkg_fishbot_description, 'config/rviz', 'display_model.rviz') # 请确保上次课的 rviz 配置已保存
    rviz2_node = launch_ros.actions.Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_path],
        parameters=[{'use_sim_time': True}], # 必须与仿真时钟同步！
        output='screen'
    )


    return launch.LaunchDescription([
        robot_state_publisher_node,
        gz_sim_cmd,
        spawn_entity_node,
        diff_drive_bridge_node,
        rviz2_node
    ])