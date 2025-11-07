#!/usr/bin/env python3
"""
Single-device xense publisher node.

This node requires the following ROS params at startup:
  ~serial_number (string)    -- required, the sensor serial number to open
  ~rectify_width (int)       -- required, rectify image width
  ~rectify_height (int)      -- required, rectify image height
  ~publish_rate (float)      -- optional, default 30.0 Hz

Publishes under namespace `/xense/<SN>/`:
    - force (std_msgs/Float32MultiArray)
    - force_resultant (geometry_msgs/WrenchStamped) -- fx,fy,fz,tx,ty,tz
    - rectify (sensor_msgs/Image)      -- via cv_bridge (encoding: rgb8) (three-channel uint8)
    - depth (sensor_msgs/Image)        -- via cv_bridge (encoding: 32FC1) (single-channel float32)
    - status (std_msgs/String)

Note: cv_bridge and xensesdk must be available in the ROS Python environment.
"""

import rospy
import numpy as np
from std_msgs.msg import Float32MultiArray, MultiArrayDimension, String
from geometry_msgs.msg import WrenchStamped
from sensor_msgs.msg import Image

try:
    from cv_bridge import CvBridge
except Exception as e:
    CvBridge = None

try:
    from xensesdk import Sensor
except Exception:
    Sensor = None


def np_to_multiarray(arr: np.ndarray):
    msg = Float32MultiArray()
    if arr is None:
        return msg
    arr = np.array(arr)
    if arr.ndim == 0:
        dim = MultiArrayDimension()
        dim.label = 'value'
        dim.size = 1
        dim.stride = 1
        msg.layout.dim.append(dim)
        msg.data = [float(arr)]
        return msg

    shape = arr.shape
    stride = 1
    for s in reversed(shape):
        dim = MultiArrayDimension()
        dim.label = 'dim'
        dim.size = int(s)
        dim.stride = stride * int(s)
        msg.layout.dim.insert(0, dim)
        stride = dim.stride

    msg.data = arr.astype(np.float32).ravel(order='C').tolist()
    return msg


def run():
    rospy.init_node('xense_publisher', anonymous=False)

    serial = rospy.get_param('~serial_number', '')
    rect_w = rospy.get_param('~rectify_width', 200)
    rect_h = rospy.get_param('~rectify_height', 350)
    rate_hz = rospy.get_param('~publish_rate', 30.0)

    # validate required params
    if not serial:
        rospy.logerr('Parameter ~serial_number is required')
        return
    if not rect_w or not rect_h:
        rospy.logerr('Parameters ~rectify_width and ~rectify_height are required')
        return

    if Sensor is None:
        rospy.logerr('xensesdk not available in this Python environment')
        return
    if CvBridge is None:
        rospy.logerr('cv_bridge not available in this Python environment; install cv_bridge')
        return

    ns = '/xense/{}/'.format(serial)
    pub_force = rospy.Publisher(ns + 'force', Float32MultiArray, queue_size=1)
    pub_res = rospy.Publisher(ns + 'force_resultant', WrenchStamped, queue_size=1)
    pub_rect_img = rospy.Publisher(ns + 'rectify', Image, queue_size=1)
    pub_depth_img = rospy.Publisher(ns + 'depth', Image, queue_size=1)
    pub_status = rospy.Publisher(ns + 'status', String, queue_size=1)

    bridge = CvBridge()

    sensor = None
    try:
        rospy.loginfo('Creating sensor %s with rectify_size=(%d,%d)' % (serial, rect_w, rect_h))
        sensor = Sensor.create(serial, rectify_size=(rect_w, rect_h))
        rospy.loginfo('Sensor created')
    except Exception as e:
        rospy.logerr('Failed to create Sensor: %s' % e)
        pub_status.publish(String(data='error: %s' % e))
        rospy.signal_shutdown('sensor init failed')
        return

    rate = rospy.Rate(rate_hz)
    while not rospy.is_shutdown():
        try:
            force, res_force, src, depth = sensor.selectSensorInfo(
                Sensor.OutputType.Force,
                Sensor.OutputType.ForceResultant,
                Sensor.OutputType.Rectify,
                Sensor.OutputType.Depth,
            )

            # force array
            if force is not None:
                pub_force.publish(np_to_multiarray(np.array(force)))

            # resultant: expect 6 values [fx,fy,fz,tx,ty,tz]
            if res_force is not None:
                try:
                    w = WrenchStamped()
                    w.header.stamp = rospy.Time.now()
                    # ensure length and convert safely
                    vals = list(res_force)
                    w.wrench.force.x =  vals[0]
                    w.wrench.force.y =  vals[1]
                    w.wrench.force.z =  vals[2]
                    w.wrench.torque.x = vals[3]
                    w.wrench.torque.y = vals[4]
                    w.wrench.torque.z = vals[5]
                    pub_res.publish(w)
                except Exception as e:
                    rospy.logwarn('Failed to publish force_resultant as WrenchStamped: %s' % e)

            # images: src is HxWx3 uint8 (rgb8); depth is HxW float32 (32FC1)
            try:
                if src is not None:
                    arr = np.ascontiguousarray(np.array(src, dtype=np.uint8))
                    img = bridge.cv2_to_imgmsg(arr, encoding='bgr8')
                    img.header.stamp = rospy.Time.now()
                    pub_rect_img.publish(img)

                if depth is not None:
                    arr_d = np.ascontiguousarray(np.array(depth, dtype=np.float32))
                    img = bridge.cv2_to_imgmsg(arr_d, encoding='32FC1')
                    img.header.stamp = rospy.Time.now()
                    pub_depth_img.publish(img)
            except Exception as e:
                rospy.logwarn('cv_bridge conversion failed: %s' % e)

            pub_status.publish(String(data='ok'))

        except Exception as e:
            rospy.logerr('Error reading sensor data: %s' % e)
            pub_status.publish(String(data='error: %s' % e))

        rate.sleep()

    # cleanup
    try:
        if sensor is not None:
            sensor.release()
            rospy.loginfo('Sensor released')
    except Exception:
        pass


if __name__ == '__main__':
    try:
        run()
    except rospy.ROSInterruptException:
        pass
