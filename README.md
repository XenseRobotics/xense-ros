# xense_ros

本工作区包含两个包：

- `xense_ros`：ROS1 (catkin) 的 Python 包，包含单设备节点 `xense_publisher.py`，将 xensesdk 传感器数据发布到 `/xense/<SN>/` 话题。
- `xense_ros2`：ROS2 (ament_python) 的 Python 包，包含等效功能的单设备节点 `xense_publisher_ros2`。

依赖

- 在运行 ROS/ROS2 节点的 Python 环境中已安装并能 `import xensesdk`。
- 已安装 `cv_bridge`（用于在 OpenCV ndarray 与 `sensor_msgs/Image` 之间转换）。

发布的话题与数据格式（每个设备命名空间为 `/xense/<SN>/`）

- `/xense/<SN>/force` : `std_msgs/Float32MultiArray`（力场数组）
- `/xense/<SN>/force_resultant` : `geometry_msgs/WrenchStamped`（6 个分量：fx,fy,fz -> wrench.force；tx,ty,tz -> wrench.torque）
- `/xense/<SN>/rectify` : `sensor_msgs/Image`（HxWx3 uint8）。
- `/xense/<SN>/depth` : `sensor_msgs/Image`（HxW float32）。
- `/xense/<SN>/marker2d` : `std_msgs/Float32MultiArray`（形状为 nrow x ncol x 2 的 float32 数组）。
- `/xense/<SN>/status` : `std_msgs/String`（"ok" 或错误信息）

## 1. 使用指南

1) 建议在一个专用的 conda 环境中安装 `xensesdk`：

```bash
conda create -n xense_env python=3.9 -y
conda activate xense_env
# 下面的安装命令根据 xensesdk 的分发形式而不同，例如 pip 安装：
pip install xensesdk
```

2) 确保节点脚本使用该 conda 环境的 Python 解释器：将 `xense_publisher.py`（或 ROS2 的 `xense_publisher_ros2.py`）第一行的 shebang 修改为该环境的 python 完整路径。例如：

```bash
#!/home/youruser/miniconda3/envs/xense_env/bin/python
```

然后赋予 `xense_publisher.py` 可执行权限。

如何查找 conda 环境中的 python 路径：

```bash
conda activate xense_env
which python      # Linux/macOS
# 或者 (Windows PowerShell):
(Get-Command python).Source
```

3) 将 xense_ros 文件夹复制到 ros_ws/src 中, 启动传感器

运行示例（ROS1）

```bash
roslaunch xense_ros xense_publisher.launch serial_number:=OG000001 rectify_width:=200 rectify_height:=350 publish_rate:=30.0
```

运行示例（ROS2）

```bash
ros2 launch xense_ros2 xense_publisher_launch.py serial_number:=OG000001 rectify_width:=200 rectify_height:=350 publish_rate:=30.0
```

## 2. 常见问题解答 (FAQ)

在某些 Linux 系统上，从 conda 环境导入某些库时，Python 或 C 扩展可能因为系统和 conda 中的 `libffi` 版本不一致而失败（常见错误类似于找不到 `libffi.so.7` 或链接错误）。一种常见修复方式是把 conda 环境中对应的 `libffi` 动态库做一个系统级的软链接：

```bash
# 先找到 conda 环境下的 libffi，比如：
ls /home/youruser/miniconda3/envs/xense_env/lib/libffi*.so*

# 然后在 conda 目录中创建一个软链接（示例）：
ln -s /home/youruser/miniconda3/envs/xense_env/lib/libffi.so.7 /usr/lib/libffi.so.7
```

注意：

- 在进行上述操作前，请确认源文件路径和目标路径是正确的。
