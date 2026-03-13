#!/usr/bin/env python3

import rospy
from visualization_msgs.msg import Marker
from geometry_msgs.msg import Point
from f110_msgs.msg import WpntArray

pub = None

def waypoint_callback(msg):

    marker = Marker()
    marker.header.frame_id = "map"
    marker.header.stamp = rospy.Time.now()

    marker.ns = "trajectory"
    marker.id = 0
    marker.type = Marker.LINE_STRIP
    marker.action = Marker.ADD

    marker.scale.x = 0.05

    marker.color.r = 1.0
    marker.color.g = 0.0
    marker.color.b = 0.0
    marker.color.a = 1.0

    marker.pose.orientation.w = 1.0

    for wp in msg.wpnts:

        p = Point()
        p.x = wp.x_m
        p.y = wp.y_m
        p.z = 0

        marker.points.append(p)

    pub.publish(marker)


if __name__ == "__main__":

    rospy.init_node("trajectory_visualizer")

    pub = rospy.Publisher(
        "/trajectory_marker",   # IMPORTANT: separate topic
        Marker,
        queue_size=1
    )

    rospy.Subscriber(
        "/global_waypoints",
        WpntArray,
        waypoint_callback
    )

    rospy.spin()