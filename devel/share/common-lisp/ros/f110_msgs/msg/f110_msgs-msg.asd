
(cl:in-package :asdf)

(defsystem "f110_msgs-msg"
  :depends-on (:roslisp-msg-protocol :roslisp-utils :std_msgs-msg
)
  :components ((:file "_package")
    (:file "Wpnt" :depends-on ("_package_Wpnt"))
    (:file "_package_Wpnt" :depends-on ("_package"))
    (:file "WpntArray" :depends-on ("_package_WpntArray"))
    (:file "_package_WpntArray" :depends-on ("_package"))
  ))