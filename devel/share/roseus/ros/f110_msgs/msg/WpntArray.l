;; Auto-generated. Do not edit!


(when (boundp 'f110_msgs::WpntArray)
  (if (not (find-package "F110_MSGS"))
    (make-package "F110_MSGS"))
  (shadow 'WpntArray (find-package "F110_MSGS")))
(unless (find-package "F110_MSGS::WPNTARRAY")
  (make-package "F110_MSGS::WPNTARRAY"))

(in-package "ROS")
;;//! \htmlinclude WpntArray.msg.html
(if (not (find-package "STD_MSGS"))
  (ros::roseus-add-msgs "std_msgs"))


(defclass f110_msgs::WpntArray
  :super ros::object
  :slots (_header _wpnts ))

(defmethod f110_msgs::WpntArray
  (:init
   (&key
    ((:header __header) (instance std_msgs::Header :init))
    ((:wpnts __wpnts) ())
    )
   (send-super :init)
   (setq _header __header)
   (setq _wpnts __wpnts)
   self)
  (:header
   (&rest __header)
   (if (keywordp (car __header))
       (send* _header __header)
     (progn
       (if __header (setq _header (car __header)))
       _header)))
  (:wpnts
   (&rest __wpnts)
   (if (keywordp (car __wpnts))
       (send* _wpnts __wpnts)
     (progn
       (if __wpnts (setq _wpnts (car __wpnts)))
       _wpnts)))
  (:serialization-length
   ()
   (+
    ;; std_msgs/Header _header
    (send _header :serialization-length)
    ;; f110_msgs/Wpnt[] _wpnts
    (apply #'+ (send-all _wpnts :serialization-length)) 4
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; std_msgs/Header _header
       (send _header :serialize s)
     ;; f110_msgs/Wpnt[] _wpnts
     (write-long (length _wpnts) s)
     (dolist (elem _wpnts)
       (send elem :serialize s)
       )
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; std_msgs/Header _header
     (send _header :deserialize buf ptr-) (incf ptr- (send _header :serialization-length))
   ;; f110_msgs/Wpnt[] _wpnts
   (let (n)
     (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4)
     (setq _wpnts (let (r) (dotimes (i n) (push (instance f110_msgs::Wpnt :init) r)) r))
     (dolist (elem- _wpnts)
     (send elem- :deserialize buf ptr-) (incf ptr- (send elem- :serialization-length))
     ))
   ;;
   self)
  )

(setf (get f110_msgs::WpntArray :md5sum-) "f862195689eef47cf0c81faffd1f380d")
(setf (get f110_msgs::WpntArray :datatype-) "f110_msgs/WpntArray")
(setf (get f110_msgs::WpntArray :definition-)
      "std_msgs/Header header
Wpnt[] wpnts


================================================================================
MSG: std_msgs/Header
# Standard metadata for higher-level stamped data types.
# This is generally used to communicate timestamped data 
# in a particular coordinate frame.
# 
# sequence ID: consecutively increasing ID 
uint32 seq
#Two-integer timestamp that is expressed as:
# * stamp.sec: seconds (stamp_secs) since epoch (in Python the variable is called 'secs')
# * stamp.nsec: nanoseconds since stamp_secs (in Python the variable is called 'nsecs')
# time-handling sugar is provided by the client library
time stamp
#Frame this data is associated with
string frame_id

================================================================================
MSG: f110_msgs/Wpnt
int32 id

# frenet coordinates
float64 s_m
float64 d_m

# map coordinates
float64 x_m
float64 y_m

# track bound distance
float64 d_right
float64 d_left

# track information
float64 psi_rad
float64 kappa_radpm
float64 vx_mps
float64 ax_mps2


")



(provide :f110_msgs/WpntArray "f862195689eef47cf0c81faffd1f380d")


