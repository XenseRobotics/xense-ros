from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    ld = LaunchDescription()

    node = Node(
        package='xense_ros2',
        executable='xense_publisher_ros2',
        name='xense_publisher_ros2',
        output='screen',
        parameters=[
            {'serial_number': ''},
            {'rectify_width': 200},
            {'rectify_height': 350},
            {'publish_rate': 30.0},
        ]
    )

    ld.add_action(node)
    return ld
