#!/usr/bin/env python3
"""
ROS2 single-device xense publisher node.

Parameters (ROS2 params):
  serial_number (string) -- required
  rectify_width (int)    -- required
  rectify_height (int)   -- required
  publish_rate (float)   -- optional, default 10.0

Publishes under namespace /xense/<SN>/ similar to ROS1 version:
    - force (std_msgs/Float32MultiArray)
    - force_resultant (geometry_msgs/WrenchStamped) -- fx,fy,fz,tx,ty,tz
    - rectify (sensor_msgs/Image) -- rgb8
    - depth (sensor_msgs/Image) -- 32FC1
    - marker2d (std_msgs/Float32MultiArray) -- shape: (nrow,ncol,2), dtype: float32
    - status (std_msgs/String)
"""

import rclpy
from rclpy.node import Node
import numpy as np
from std_msgs.msg import Float32MultiArray, MultiArrayDimension, String
from geometry_msgs.msg import WrenchStamped
from sensor_msgs.msg import Image

try:
    from cv_bridge import CvBridge
except Exception:
    CvBridge = None

try:
    from xensesdk import Sensor
except Exception:
    Sensor = None


def np_to_multiarray(arr: np.ndarray):
    msg = Float32MultiArray()
    if arr is None:
        return msg
    a = np.array(arr)
    if a.ndim == 0:
        dim = MultiArrayDimension()
        dim.label = 'value'
        dim.size = 1
        dim.stride = 1
        msg.layout.dim.append(dim)
        msg.data = [float(a)]
        return msg

    shape = a.shape
    stride = 1
    for s in reversed(shape):
        dim = MultiArrayDimension()
        dim.label = 'dim'
        dim.size = int(s)
        dim.stride = stride * int(s)
        msg.layout.dim.insert(0, dim)
        stride = dim.stride
    msg.data = a.astype(np.float32).ravel(order='C').tolist()
    return msg


class XensePublisher(Node):
    def __init__(self):
        super().__init__('xense_publisher_ros2')

        # declare params
        self.declare_parameter('serial_number', '')
        self.declare_parameter('rectify_width', 200)
        self.declare_parameter('rectify_height', 350)
        self.declare_parameter('publish_rate', 30.0)

        serial = self.get_parameter('serial_number').get_parameter_value().string_value
        rect_w = self.get_parameter('rectify_width').get_parameter_value().integer_value
        rect_h = self.get_parameter('rectify_height').get_parameter_value().integer_value
        rate_hz = self.get_parameter('publish_rate').get_parameter_value().double_value

        if not serial:
            self.get_logger().error('Parameter serial_number is required')
            raise RuntimeError('serial_number required')
        if rect_w <= 0 or rect_h <= 0:
            self.get_logger().error('rectify_width and rectify_height are required and must be > 0')
            raise RuntimeError('rectify size required')

        if Sensor is None:
            self.get_logger().error('xensesdk not available')
            raise RuntimeError('missing xensesdk')
        if CvBridge is None:
            self.get_logger().error('cv_bridge not available')
            raise RuntimeError('missing cv_bridge')

        self.serial = serial
        ns = '/xense/{}/'.format(self.serial)

        self.pub_force = self.create_publisher(Float32MultiArray, ns + 'force', 10)
        self.pub_res = self.create_publisher(WrenchStamped, ns + 'force_resultant', 10)
        self.pub_rect = self.create_publisher(Image, ns + 'rectify', 10)
        # do not publish difference as requested
        self.pub_depth = self.create_publisher(Image, ns + 'depth', 10)
        self.pub_marker2d = self.create_publisher(Float32MultiArray, ns + 'marker2d', 10)
        self.pub_status = self.create_publisher(String, ns + 'status', 10)

        self.bridge = CvBridge()

        # create sensor
        try:
            self.get_logger().info('Creating sensor %s with rectify_size=(%d,%d)' % (serial, rect_w, rect_h))
            self.sensor = Sensor.create(serial, rectify_size=(rect_w, rect_h))
            self.get_logger().info('Sensor created')
        except Exception as e:
            self.get_logger().error('Failed to create Sensor: %s' % e)
            self.pub_status.publish(String(data='error: %s' % e))
            raise

        # timer
        period = 1.0 / max(float(rate_hz), 1e-3)
        self.timer = self.create_timer(period, self.timer_callback)

    # src is HxWx3 uint8 already; depth is HxW float32

    def timer_callback(self):
        try:
            force, res_force, src, depth, marker2d = self.sensor.selectSensorInfo(
                Sensor.OutputType.Force,
                Sensor.OutputType.ForceResultant,
                Sensor.OutputType.Rectify,
                Sensor.OutputType.Depth,
                Sensor.OutputType.Marker2D,
            )

            if force is not None:
                self.pub_force.publish(np_to_multiarray(np.array(force)))

            if marker2d is not None:
                self.pub_marker2d.publish(np_to_multiarray(np.array(marker2d, dtype=np.float32)))

            if res_force is not None:
                # res_force is guaranteed to be 6D: [fx,fy,fz,tx,ty,tz]
                vals = list(res_force)
                w = WrenchStamped()
                w.header.stamp = self.get_clock().now().to_msg()
                w.wrench.force.x = float(vals[0])
                w.wrench.force.y = float(vals[1])
                w.wrench.force.z = float(vals[2])
                w.wrench.torque.x = float(vals[3])
                w.wrench.torque.y = float(vals[4])
                w.wrench.torque.z = float(vals[5])
                self.pub_res.publish(w)

            # rectify / diff -> rgb8
            try:
                if src is not None:
                    arr = np.ascontiguousarray(np.array(src, dtype=np.uint8))
                    img = self.bridge.cv2_to_imgmsg(arr, encoding='bgr8')
                    img.header.stamp = self.get_clock().now().to_msg()
                    self.pub_rect.publish(img)
                # do not publish diff; publish rectify and depth
                if depth is not None:
                    arr_d = np.ascontiguousarray(np.array(depth, dtype=np.float32))
                    img = self.bridge.cv2_to_imgmsg(arr_d, encoding='32FC1')
                    img.header.stamp = self.get_clock().now().to_msg()
                    self.pub_depth.publish(img)
            except Exception as e:
                self.get_logger().warning('cv_bridge conversion failed: %s' % e)

            self.pub_status.publish(String(data='ok'))

        except Exception as e:
            self.get_logger().error('Error reading sensor data: %s' % e)
            self.pub_status.publish(String(data='error: %s' % e))

    def destroy_node(self):
        try:
            if self.sensor is not None:
                self.sensor.release()
                self.get_logger().info('Sensor released')
        except Exception:
            pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = XensePublisher()
        rclpy.spin(node)
    except Exception as e:
        print('xense_ros2 node error:', e)
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
