// Auto-generated. Do not edit!

// (in-package f110_msgs.msg)


"use strict";

const _serializer = _ros_msg_utils.Serialize;
const _arraySerializer = _serializer.Array;
const _deserializer = _ros_msg_utils.Deserialize;
const _arrayDeserializer = _deserializer.Array;
const _finder = _ros_msg_utils.Find;
const _getByteLength = _ros_msg_utils.getByteLength;
let Wpnt = require('./Wpnt.js');
let std_msgs = _finder('std_msgs');

//-----------------------------------------------------------

class WpntArray {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.header = null;
      this.wpnts = null;
    }
    else {
      if (initObj.hasOwnProperty('header')) {
        this.header = initObj.header
      }
      else {
        this.header = new std_msgs.msg.Header();
      }
      if (initObj.hasOwnProperty('wpnts')) {
        this.wpnts = initObj.wpnts
      }
      else {
        this.wpnts = [];
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type WpntArray
    // Serialize message field [header]
    bufferOffset = std_msgs.msg.Header.serialize(obj.header, buffer, bufferOffset);
    // Serialize message field [wpnts]
    // Serialize the length for message field [wpnts]
    bufferOffset = _serializer.uint32(obj.wpnts.length, buffer, bufferOffset);
    obj.wpnts.forEach((val) => {
      bufferOffset = Wpnt.serialize(val, buffer, bufferOffset);
    });
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type WpntArray
    let len;
    let data = new WpntArray(null);
    // Deserialize message field [header]
    data.header = std_msgs.msg.Header.deserialize(buffer, bufferOffset);
    // Deserialize message field [wpnts]
    // Deserialize array length for message field [wpnts]
    len = _deserializer.uint32(buffer, bufferOffset);
    data.wpnts = new Array(len);
    for (let i = 0; i < len; ++i) {
      data.wpnts[i] = Wpnt.deserialize(buffer, bufferOffset)
    }
    return data;
  }

  static getMessageSize(object) {
    let length = 0;
    length += std_msgs.msg.Header.getMessageSize(object.header);
    length += 84 * object.wpnts.length;
    return length + 4;
  }

  static datatype() {
    // Returns string type for a message object
    return 'f110_msgs/WpntArray';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return 'f862195689eef47cf0c81faffd1f380d';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    std_msgs/Header header
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
    
    
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new WpntArray(null);
    if (msg.header !== undefined) {
      resolved.header = std_msgs.msg.Header.Resolve(msg.header)
    }
    else {
      resolved.header = new std_msgs.msg.Header()
    }

    if (msg.wpnts !== undefined) {
      resolved.wpnts = new Array(msg.wpnts.length);
      for (let i = 0; i < resolved.wpnts.length; ++i) {
        resolved.wpnts[i] = Wpnt.Resolve(msg.wpnts[i]);
      }
    }
    else {
      resolved.wpnts = []
    }

    return resolved;
    }
};

module.exports = WpntArray;
