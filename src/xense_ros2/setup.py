from setuptools import setup

package_name = 'xense_ros2'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='your name',
    maintainer_email='you@example.com',
    description='ROS2 package to publish sensor data from xensesdk (single-device)',
    license='MIT',
    entry_points={
        'console_scripts': [
            'xense_publisher_ros2 = xense_ros2.xense_publisher_ros2:main',
        ],
    },
)
