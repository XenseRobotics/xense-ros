cmake_minimum_required(VERSION 3.0.2)
project(xense_ros)


find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  geometry_msgs
  sensor_msgs
  cv_bridge
)

catkin_package(
  CATKIN_DEPENDS rospy std_msgs geometry_msgs sensor_msgs cv_bridge
)

include_directories(${catkin_INCLUDE_DIRS})

catkin_install_python(PROGRAMS
  scripts/xense_publisher.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)
