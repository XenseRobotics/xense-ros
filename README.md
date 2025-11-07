# xense_ros 工作区

本工作区包含两个包：

- `xense_ros`：ROS1 (catkin) 的 Python 包，包含单设备节点 `xense_publisher.py`，将 xensesdk 传感器数据发布到 `/xense/<SN>/` 话题。
- `xense_ros2`：ROS2 (ament_python) 的 Python 包，包含等效功能的单设备节点 `xense_publisher_ros2`。

前提与依赖

- 在运行 ROS/ROS2 节点的 Python 环境中已安装并能 `import xensesdk`。
- 已安装 `cv_bridge`（用于在 OpenCV ndarray 与 `sensor_msgs/Image` 之间转换）。

发布的话题与数据格式（每个设备命名空间为 `/xense/<SN>/`）

- `/xense/<SN>/force` : `std_msgs/Float32MultiArray`（力场数组）
- `/xense/<SN>/force_resultant` : `geometry_msgs/WrenchStamped`（6 个分量：fx,fy,fz -> wrench.force；tx,ty,tz -> wrench.torque）
- `/xense/<SN>/rectify` : `sensor_msgs/Image`（HxWx3 uint8）。
- `/xense/<SN>/depth` : `sensor_msgs/Image`（HxW float32）。
- `/xense/<SN>/status` : `std_msgs/String`（"ok" 或错误信息）

默认参数

- `rectify_width` = 200
- `rectify_height` = 350
- `publish_rate` = 30.0 Hz

ROS1 运行

1. 将 `xense_ros` 目录复制到你的 catkin workspace 的 `src/`（例如 `~/catkin_ws/src/`）。
2. 启动节点（示例）, 将序列号修改成实际序列号：

```bash
roslaunch xense_ros xense_publisher.launch serial_number:=OG000001 rectify_width:=200 rectify_height:=350 publish_rate:=30.0
```

ROS2 运行

1. 将 `xense_ros2` 目录复制到 ROS2 工作区的 `src/`（例如 `~/ros2_ws/src/`）。
2. 启动节点（示例）, 将序列号修改成实际序列号：

```bash
ros2 launch xense_ros2 xense_publisher_launch.py serial_number:=OG000001 rectify_width:=200 rectify_height:=350 publish_rate:=30.0
```
