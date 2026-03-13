// Auto-generated. Do not edit!

// (in-package f110_msgs.msg)


"use strict";

const _serializer = _ros_msg_utils.Serialize;
const _arraySerializer = _serializer.Array;
const _deserializer = _ros_msg_utils.Deserialize;
const _arrayDeserializer = _deserializer.Array;
const _finder = _ros_msg_utils.Find;
const _getByteLength = _ros_msg_utils.getByteLength;

//-----------------------------------------------------------

class Wpnt {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.id = null;
      this.s_m = null;
      this.d_m = null;
      this.x_m = null;
      this.y_m = null;
      this.d_right = null;
      this.d_left = null;
      this.psi_rad = null;
      this.kappa_radpm = null;
      this.vx_mps = null;
      this.ax_mps2 = null;
    }
    else {
      if (initObj.hasOwnProperty('id')) {
        this.id = initObj.id
      }
      else {
        this.id = 0;
      }
      if (initObj.hasOwnProperty('s_m')) {
        this.s_m = initObj.s_m
      }
      else {
        this.s_m = 0.0;
      }
      if (initObj.hasOwnProperty('d_m')) {
        this.d_m = initObj.d_m
      }
      else {
        this.d_m = 0.0;
      }
      if (initObj.hasOwnProperty('x_m')) {
        this.x_m = initObj.x_m
      }
      else {
        this.x_m = 0.0;
      }
      if (initObj.hasOwnProperty('y_m')) {
        this.y_m = initObj.y_m
      }
      else {
        this.y_m = 0.0;
      }
      if (initObj.hasOwnProperty('d_right')) {
        this.d_right = initObj.d_right
      }
      else {
        this.d_right = 0.0;
      }
      if (initObj.hasOwnProperty('d_left')) {
        this.d_left = initObj.d_left
      }
      else {
        this.d_left = 0.0;
      }
      if (initObj.hasOwnProperty('psi_rad')) {
        this.psi_rad = initObj.psi_rad
      }
      else {
        this.psi_rad = 0.0;
      }
      if (initObj.hasOwnProperty('kappa_radpm')) {
        this.kappa_radpm = initObj.kappa_radpm
      }
      else {
        this.kappa_radpm = 0.0;
      }
      if (initObj.hasOwnProperty('vx_mps')) {
        this.vx_mps = initObj.vx_mps
      }
      else {
        this.vx_mps = 0.0;
      }
      if (initObj.hasOwnProperty('ax_mps2')) {
        this.ax_mps2 = initObj.ax_mps2
      }
      else {
        this.ax_mps2 = 0.0;
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type Wpnt
    // Serialize message field [id]
    bufferOffset = _serializer.int32(obj.id, buffer, bufferOffset);
    // Serialize message field [s_m]
    bufferOffset = _serializer.float64(obj.s_m, buffer, bufferOffset);
    // Serialize message field [d_m]
    bufferOffset = _serializer.float64(obj.d_m, buffer, bufferOffset);
    // Serialize message field [x_m]
    bufferOffset = _serializer.float64(obj.x_m, buffer, bufferOffset);
    // Serialize message field [y_m]
    bufferOffset = _serializer.float64(obj.y_m, buffer, bufferOffset);
    // Serialize message field [d_right]
    bufferOffset = _serializer.float64(obj.d_right, buffer, bufferOffset);
    // Serialize message field [d_left]
    bufferOffset = _serializer.float64(obj.d_left, buffer, bufferOffset);
    // Serialize message field [psi_rad]
    bufferOffset = _serializer.float64(obj.psi_rad, buffer, bufferOffset);
    // Serialize message field [kappa_radpm]
    bufferOffset = _serializer.float64(obj.kappa_radpm, buffer, bufferOffset);
    // Serialize message field [vx_mps]
    bufferOffset = _serializer.float64(obj.vx_mps, buffer, bufferOffset);
    // Serialize message field [ax_mps2]
    bufferOffset = _serializer.float64(obj.ax_mps2, buffer, bufferOffset);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type Wpnt
    let len;
    let data = new Wpnt(null);
    // Deserialize message field [id]
    data.id = _deserializer.int32(buffer, bufferOffset);
    // Deserialize message field [s_m]
    data.s_m = _deserializer.float64(buffer, bufferOffset);
    // Deserialize message field [d_m]
    data.d_m = _deserializer.float64(buffer, bufferOffset);
    // Deserialize message field [x_m]
    data.x_m = _deserializer.float64(buffer, bufferOffset);
    // Deserialize message field [y_m]
    data.y_m = _deserializer.float64(buffer, bufferOffset);
    // Deserialize message field [d_right]
    data.d_right = _deserializer.float64(buffer, bufferOffset);
    // Deserialize message field [d_left]
    data.d_left = _deserializer.float64(buffer, bufferOffset);
    // Deserialize message field [psi_rad]
    data.psi_rad = _deserializer.float64(buffer, bufferOffset);
    // Deserialize message field [kappa_radpm]
    data.kappa_radpm = _deserializer.float64(buffer, bufferOffset);
    // Deserialize message field [vx_mps]
    data.vx_mps = _deserializer.float64(buffer, bufferOffset);
    // Deserialize message field [ax_mps2]
    data.ax_mps2 = _deserializer.float64(buffer, bufferOffset);
    return data;
  }

  static getMessageSize(object) {
    return 84;
  }

  static datatype() {
    // Returns string type for a message object
    return 'f110_msgs/Wpnt';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return '13f150fd4a210ecd18beb652ce35aefa';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
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
    const resolved = new Wpnt(null);
    if (msg.id !== undefined) {
      resolved.id = msg.id;
    }
    else {
      resolved.id = 0
    }

    if (msg.s_m !== undefined) {
      resolved.s_m = msg.s_m;
    }
    else {
      resolved.s_m = 0.0
    }

    if (msg.d_m !== undefined) {
      resolved.d_m = msg.d_m;
    }
    else {
      resolved.d_m = 0.0
    }

    if (msg.x_m !== undefined) {
      resolved.x_m = msg.x_m;
    }
    else {
      resolved.x_m = 0.0
    }

    if (msg.y_m !== undefined) {
      resolved.y_m = msg.y_m;
    }
    else {
      resolved.y_m = 0.0
    }

    if (msg.d_right !== undefined) {
      resolved.d_right = msg.d_right;
    }
    else {
      resolved.d_right = 0.0
    }

    if (msg.d_left !== undefined) {
      resolved.d_left = msg.d_left;
    }
    else {
      resolved.d_left = 0.0
    }

    if (msg.psi_rad !== undefined) {
      resolved.psi_rad = msg.psi_rad;
    }
    else {
      resolved.psi_rad = 0.0
    }

    if (msg.kappa_radpm !== undefined) {
      resolved.kappa_radpm = msg.kappa_radpm;
    }
    else {
      resolved.kappa_radpm = 0.0
    }

    if (msg.vx_mps !== undefined) {
      resolved.vx_mps = msg.vx_mps;
    }
    else {
      resolved.vx_mps = 0.0
    }

    if (msg.ax_mps2 !== undefined) {
      resolved.ax_mps2 = msg.ax_mps2;
    }
    else {
      resolved.ax_mps2 = 0.0
    }

    return resolved;
    }
};

module.exports = Wpnt;
