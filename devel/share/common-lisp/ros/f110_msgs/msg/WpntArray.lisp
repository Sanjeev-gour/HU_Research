; Auto-generated. Do not edit!


(cl:in-package f110_msgs-msg)


;//! \htmlinclude WpntArray.msg.html

(cl:defclass <WpntArray> (roslisp-msg-protocol:ros-message)
  ((header
    :reader header
    :initarg :header
    :type std_msgs-msg:Header
    :initform (cl:make-instance 'std_msgs-msg:Header))
   (wpnts
    :reader wpnts
    :initarg :wpnts
    :type (cl:vector f110_msgs-msg:Wpnt)
   :initform (cl:make-array 0 :element-type 'f110_msgs-msg:Wpnt :initial-element (cl:make-instance 'f110_msgs-msg:Wpnt))))
)

(cl:defclass WpntArray (<WpntArray>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <WpntArray>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'WpntArray)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name f110_msgs-msg:<WpntArray> is deprecated: use f110_msgs-msg:WpntArray instead.")))

(cl:ensure-generic-function 'header-val :lambda-list '(m))
(cl:defmethod header-val ((m <WpntArray>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader f110_msgs-msg:header-val is deprecated.  Use f110_msgs-msg:header instead.")
  (header m))

(cl:ensure-generic-function 'wpnts-val :lambda-list '(m))
(cl:defmethod wpnts-val ((m <WpntArray>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader f110_msgs-msg:wpnts-val is deprecated.  Use f110_msgs-msg:wpnts instead.")
  (wpnts m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <WpntArray>) ostream)
  "Serializes a message object of type '<WpntArray>"
  (roslisp-msg-protocol:serialize (cl:slot-value msg 'header) ostream)
  (cl:let ((__ros_arr_len (cl:length (cl:slot-value msg 'wpnts))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_arr_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_arr_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_arr_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_arr_len) ostream))
  (cl:map cl:nil #'(cl:lambda (ele) (roslisp-msg-protocol:serialize ele ostream))
   (cl:slot-value msg 'wpnts))
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <WpntArray>) istream)
  "Deserializes a message object of type '<WpntArray>"
  (roslisp-msg-protocol:deserialize (cl:slot-value msg 'header) istream)
  (cl:let ((__ros_arr_len 0))
    (cl:setf (cl:ldb (cl:byte 8 0) __ros_arr_len) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 8) __ros_arr_len) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 16) __ros_arr_len) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 24) __ros_arr_len) (cl:read-byte istream))
  (cl:setf (cl:slot-value msg 'wpnts) (cl:make-array __ros_arr_len))
  (cl:let ((vals (cl:slot-value msg 'wpnts)))
    (cl:dotimes (i __ros_arr_len)
    (cl:setf (cl:aref vals i) (cl:make-instance 'f110_msgs-msg:Wpnt))
  (roslisp-msg-protocol:deserialize (cl:aref vals i) istream))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<WpntArray>)))
  "Returns string type for a message object of type '<WpntArray>"
  "f110_msgs/WpntArray")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'WpntArray)))
  "Returns string type for a message object of type 'WpntArray"
  "f110_msgs/WpntArray")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<WpntArray>)))
  "Returns md5sum for a message object of type '<WpntArray>"
  "f862195689eef47cf0c81faffd1f380d")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'WpntArray)))
  "Returns md5sum for a message object of type 'WpntArray"
  "f862195689eef47cf0c81faffd1f380d")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<WpntArray>)))
  "Returns full string definition for message of type '<WpntArray>"
  (cl:format cl:nil "std_msgs/Header header~%Wpnt[] wpnts~%~%~%================================================================================~%MSG: std_msgs/Header~%# Standard metadata for higher-level stamped data types.~%# This is generally used to communicate timestamped data ~%# in a particular coordinate frame.~%# ~%# sequence ID: consecutively increasing ID ~%uint32 seq~%#Two-integer timestamp that is expressed as:~%# * stamp.sec: seconds (stamp_secs) since epoch (in Python the variable is called 'secs')~%# * stamp.nsec: nanoseconds since stamp_secs (in Python the variable is called 'nsecs')~%# time-handling sugar is provided by the client library~%time stamp~%#Frame this data is associated with~%string frame_id~%~%================================================================================~%MSG: f110_msgs/Wpnt~%int32 id~%~%# frenet coordinates~%float64 s_m~%float64 d_m~%~%# map coordinates~%float64 x_m~%float64 y_m~%~%# track bound distance~%float64 d_right~%float64 d_left~%~%# track information~%float64 psi_rad~%float64 kappa_radpm~%float64 vx_mps~%float64 ax_mps2~%~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'WpntArray)))
  "Returns full string definition for message of type 'WpntArray"
  (cl:format cl:nil "std_msgs/Header header~%Wpnt[] wpnts~%~%~%================================================================================~%MSG: std_msgs/Header~%# Standard metadata for higher-level stamped data types.~%# This is generally used to communicate timestamped data ~%# in a particular coordinate frame.~%# ~%# sequence ID: consecutively increasing ID ~%uint32 seq~%#Two-integer timestamp that is expressed as:~%# * stamp.sec: seconds (stamp_secs) since epoch (in Python the variable is called 'secs')~%# * stamp.nsec: nanoseconds since stamp_secs (in Python the variable is called 'nsecs')~%# time-handling sugar is provided by the client library~%time stamp~%#Frame this data is associated with~%string frame_id~%~%================================================================================~%MSG: f110_msgs/Wpnt~%int32 id~%~%# frenet coordinates~%float64 s_m~%float64 d_m~%~%# map coordinates~%float64 x_m~%float64 y_m~%~%# track bound distance~%float64 d_right~%float64 d_left~%~%# track information~%float64 psi_rad~%float64 kappa_radpm~%float64 vx_mps~%float64 ax_mps2~%~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <WpntArray>))
  (cl:+ 0
     (roslisp-msg-protocol:serialization-length (cl:slot-value msg 'header))
     4 (cl:reduce #'cl:+ (cl:slot-value msg 'wpnts) :key #'(cl:lambda (ele) (cl:declare (cl:ignorable ele)) (cl:+ (roslisp-msg-protocol:serialization-length ele))))
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <WpntArray>))
  "Converts a ROS message object to a list"
  (cl:list 'WpntArray
    (cl:cons ':header (header msg))
    (cl:cons ':wpnts (wpnts msg))
))
