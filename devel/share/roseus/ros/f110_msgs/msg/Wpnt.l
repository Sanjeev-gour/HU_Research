;; Auto-generated. Do not edit!


(when (boundp 'f110_msgs::Wpnt)
  (if (not (find-package "F110_MSGS"))
    (make-package "F110_MSGS"))
  (shadow 'Wpnt (find-package "F110_MSGS")))
(unless (find-package "F110_MSGS::WPNT")
  (make-package "F110_MSGS::WPNT"))

(in-package "ROS")
;;//! \htmlinclude Wpnt.msg.html


(defclass f110_msgs::Wpnt
  :super ros::object
  :slots (_id _s_m _d_m _x_m _y_m _d_right _d_left _psi_rad _kappa_radpm _vx_mps _ax_mps2 ))

(defmethod f110_msgs::Wpnt
  (:init
   (&key
    ((:id __id) 0)
    ((:s_m __s_m) 0.0)
    ((:d_m __d_m) 0.0)
    ((:x_m __x_m) 0.0)
    ((:y_m __y_m) 0.0)
    ((:d_right __d_right) 0.0)
    ((:d_left __d_left) 0.0)
    ((:psi_rad __psi_rad) 0.0)
    ((:kappa_radpm __kappa_radpm) 0.0)
    ((:vx_mps __vx_mps) 0.0)
    ((:ax_mps2 __ax_mps2) 0.0)
    )
   (send-super :init)
   (setq _id (round __id))
   (setq _s_m (float __s_m))
   (setq _d_m (float __d_m))
   (setq _x_m (float __x_m))
   (setq _y_m (float __y_m))
   (setq _d_right (float __d_right))
   (setq _d_left (float __d_left))
   (setq _psi_rad (float __psi_rad))
   (setq _kappa_radpm (float __kappa_radpm))
   (setq _vx_mps (float __vx_mps))
   (setq _ax_mps2 (float __ax_mps2))
   self)
  (:id
   (&optional __id)
   (if __id (setq _id __id)) _id)
  (:s_m
   (&optional __s_m)
   (if __s_m (setq _s_m __s_m)) _s_m)
  (:d_m
   (&optional __d_m)
   (if __d_m (setq _d_m __d_m)) _d_m)
  (:x_m
   (&optional __x_m)
   (if __x_m (setq _x_m __x_m)) _x_m)
  (:y_m
   (&optional __y_m)
   (if __y_m (setq _y_m __y_m)) _y_m)
  (:d_right
   (&optional __d_right)
   (if __d_right (setq _d_right __d_right)) _d_right)
  (:d_left
   (&optional __d_left)
   (if __d_left (setq _d_left __d_left)) _d_left)
  (:psi_rad
   (&optional __psi_rad)
   (if __psi_rad (setq _psi_rad __psi_rad)) _psi_rad)
  (:kappa_radpm
   (&optional __kappa_radpm)
   (if __kappa_radpm (setq _kappa_radpm __kappa_radpm)) _kappa_radpm)
  (:vx_mps
   (&optional __vx_mps)
   (if __vx_mps (setq _vx_mps __vx_mps)) _vx_mps)
  (:ax_mps2
   (&optional __ax_mps2)
   (if __ax_mps2 (setq _ax_mps2 __ax_mps2)) _ax_mps2)
  (:serialization-length
   ()
   (+
    ;; int32 _id
    4
    ;; float64 _s_m
    8
    ;; float64 _d_m
    8
    ;; float64 _x_m
    8
    ;; float64 _y_m
    8
    ;; float64 _d_right
    8
    ;; float64 _d_left
    8
    ;; float64 _psi_rad
    8
    ;; float64 _kappa_radpm
    8
    ;; float64 _vx_mps
    8
    ;; float64 _ax_mps2
    8
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; int32 _id
       (write-long _id s)
     ;; float64 _s_m
       (sys::poke _s_m (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;; float64 _d_m
       (sys::poke _d_m (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;; float64 _x_m
       (sys::poke _x_m (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;; float64 _y_m
       (sys::poke _y_m (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;; float64 _d_right
       (sys::poke _d_right (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;; float64 _d_left
       (sys::poke _d_left (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;; float64 _psi_rad
       (sys::poke _psi_rad (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;; float64 _kappa_radpm
       (sys::poke _kappa_radpm (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;; float64 _vx_mps
       (sys::poke _vx_mps (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;; float64 _ax_mps2
       (sys::poke _ax_mps2 (send s :buffer) (send s :count) :double) (incf (stream-count s) 8)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; int32 _id
     (setq _id (sys::peek buf ptr- :integer)) (incf ptr- 4)
   ;; float64 _s_m
     (setq _s_m (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;; float64 _d_m
     (setq _d_m (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;; float64 _x_m
     (setq _x_m (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;; float64 _y_m
     (setq _y_m (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;; float64 _d_right
     (setq _d_right (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;; float64 _d_left
     (setq _d_left (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;; float64 _psi_rad
     (setq _psi_rad (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;; float64 _kappa_radpm
     (setq _kappa_radpm (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;; float64 _vx_mps
     (setq _vx_mps (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;; float64 _ax_mps2
     (setq _ax_mps2 (sys::peek buf ptr- :double)) (incf ptr- 8)
   ;;
   self)
  )

(setf (get f110_msgs::Wpnt :md5sum-) "13f150fd4a210ecd18beb652ce35aefa")
(setf (get f110_msgs::Wpnt :datatype-) "f110_msgs/Wpnt")
(setf (get f110_msgs::Wpnt :definition-)
      "int32 id

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



(provide :f110_msgs/Wpnt "13f150fd4a210ecd18beb652ce35aefa")


