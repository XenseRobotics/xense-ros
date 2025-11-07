# xense_ros

这是一个最小的 ROS1 包，用于读取 `xensesdk` 中 `Sensor` 的数据并发布到 ROS 话题。

依赖

- ROS1（catkin 工作区）
- Python 运行时（建议 Python 3）
- xensesdk（由厂商提供，需在运行 ROS 节点的 Python 环境中安装）

安装与使用

1. 将本包放入 catkin 工作区的 `src/` 文件夹，例如 `catkin_ws/src/`。
2. 编译工作区：

```bash
# 在 Linux 下示例
cd ~/catkin_ws
catkin_make
source devel/setup.bash
```

3. 启动节点（单设备 publisher） — 必须指定 `serial_number` 和 rectify size：

```bash
# 启动单设备 publisher（必须传入 serial_number）
roslaunch xense_ros xense_publisher.launch serial_number:=OG000001 rectify_width:=200 rectify_height:=350

# 可选：调整发布频率
roslaunch xense_ros xense_publisher.launch serial_number:=OG000001 rectify_width:=200 rectify_height:=350 publish_rate:=5.0
```

参数

- `~serial_number`：传感器序列号，默认 `OG000001`
- `~rectify_width` / `~rectify_height`：rectify 图像尺寸，默认 `200x350`
- `~publish_rate`：发布频率，默认 `30.0` Hz

发布的话题

- `/xense/<SN>/force` : `std_msgs/Float32MultiArray`（力场数组，flatten）
- `/xense/<SN>/force_resultant` : `geometry_msgs/WrenchStamped`（6 个分量：fx,fy,fz,tx,ty,tz，分别存于 wrench.force 和 wrench.torque）
- `/xense/<SN>/rectify` : `sensor_msgs/Image`（三通道 uint8，encoding=rgb8）
- `/xense/<SN>/depth` : `sensor_msgs/Image`（深度图，单通道 float32，encoding=32FC1）
- `/xense/<SN>/status` : `std_msgs/String`（状态或错误信息）

注意：rectify 和 depth 使用 `sensor_msgs/Image` 发布（rectify 为 rgb8，depth 为 32FC1），因此需要在运行环境中安装 `cv_bridge` 和 `sensor_msgs`。

注意

- 本包假定 `xensesdk` 的 Python 包可被 ROS 的 Python 环境导入（如果使用 ROS 的 Python 版本与系统 Python 不同，请确保在该环境中安装 xensesdk）。
