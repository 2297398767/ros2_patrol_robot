import os
import launch
import launch_ros
from ament_index_python.packages import get_package_share_directory
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    pkg_fishbot_description = get_package_share_directory('fishbot_description')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    # 1. 路径解析
    default_model_path = os.path.join(pkg_fishbot_description, 'urdf', 'fishbot', 'fishbot.urdf.xacro')
    world_path = os.path.join(pkg_fishbot_description, 'world', 'slam_maze.sdf')

    robot_description = launch_ros.parameter_descriptions.ParameterValue(
        launch.substitutions.Command([
            'xacro ', default_model_path,
            ' use_ros2_control:=true'  # 🌟 显式注入 true，动态激活新大脑
        ]), 
        value_type=str
    )

    # 2. 核心基础节点
    robot_state_publisher_node = launch_ros.actions.Node(
        package='robot_state_publisher', executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description}, {'use_sim_time': True}]
    )
    
    # 仿真启动
    gz_sim_cmd = launch.actions.IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')),
        launch_arguments={'gz_args': f'-r {world_path}'}.items()
    )

    # 导入小车
    spawn_entity_node = launch_ros.actions.Node(
        package='ros_gz_sim', executable='create',
        arguments=['-name', 'fishbot', '-topic', '/robot_description', '-z', '0.5'],
        output='screen'
    )

    # 3. 专属传感器桥接（使用刚才精简的 YAML）
    ros2_control_bridge_config = os.path.join(pkg_fishbot_description, 'config', 'gz_bridge_ros2_control.yaml')
    bridge_node = launch_ros.actions.Node(
        package='ros_gz_bridge', executable='parameter_bridge',
        arguments=['--ros-args', '-p', f'config_file:={ros2_control_bridge_config}'],
        parameters=[{'use_sim_time': True}],
        output='screen'
    )

    # 4. RViz 可视化
    rviz2_node = launch_ros.actions.Node(
        package='rviz2', executable='rviz2', name='rviz2',
        arguments=['-d', os.path.join(pkg_fishbot_description, 'config/rviz', 'display_model.rviz')],
        parameters=[{'use_sim_time': True}],
        output='screen'
    )

    # === 新增：定义唤醒控制器的节点 (使用 spawner) ===
    # 唤醒关节状态广播器
    load_joint_state_broadcaster = launch_ros.actions.Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
        output="screen",
    )

    # 唤醒力矩控制器
    # load_effort_controller = launch_ros.actions.Node(
    #     package="controller_manager",
    #     executable="spawner",
    #     arguments=["fishbot_effort_controller", "--controller-manager", "/controller_manager"],
    #     output="screen",
    # )

    # 2. 🌟 唤醒差速控制器
    load_diff_drive_controller = launch.actions.ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active', 'fishbot_diff_drive_controller'],
        output='screen'
    )

    # 3. 🌟 启动时间戳打码机节点
    twist_stamper_node = launch_ros.actions.Node(
        package='fishbot_description',
        executable='twist_stamper.py',
        name='twist_stamper',
        parameters=[{'use_sim_time': True}]
    )



    return launch.LaunchDescription([
        gz_sim_cmd,
        robot_state_publisher_node,
        spawn_entity_node,
        bridge_node,
        rviz2_node,
        twist_stamper_node, 
        
        # ⚠️ 核心排坑：事件触发器！必须等小车模型在 Gazebo 中生成完毕 (OnProcessExit) 后，才能唤醒控制器！
        # 首先启动 joint_state_broadcaster
        launch.actions.RegisterEventHandler(
            event_handler=launch.event_handlers.OnProcessExit(
                target_action=spawn_entity_node,
                on_exit=[load_joint_state_broadcaster],
            )
        ),
        # 然后等 joint_state_broadcaster 启动完毕后，再启动 effort_controller
        launch.actions.RegisterEventHandler(
            event_handler=launch.event_handlers.OnProcessExit(
                target_action=load_joint_state_broadcaster,
                on_exit=[load_diff_drive_controller],
            )
        )
    ])