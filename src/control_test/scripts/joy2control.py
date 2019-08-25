#! /usr/bin/env python
import rospy
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Joy
import os

# This ROS Node converts Joystick inputs from the joy node
# into commands for turtlesim or any other robot

# Receives joystick messages (subscribed to Joy topic)
# then converts the joysick inputs into Twist commands
# axis 1 aka left stick vertical controls linear speed
# axis 0 aka left stick horizonal controls angular speed

class JoyMsg():
    ''' Data type for recieving data from Joystick "/joy_teleop/joy" '''
    linear_v = 0            # either (-1, 0, 1)
    angular_v = 0           # either (-1, 0, 1)
    blue_button = False
    orange_button = False
    red_button = False
    green_button = False

def recieve_joy_msg(JM, data):
    ''' Pass data from Joystick rostopic to JoyMsg object '''
    JM.linear_v = data.axes[1]
    JM.angular_v = data.axes[0]
    JM.blue_button = data.buttons[0]
    JM.green_button = data.buttons[1]
    JM.red_button = data.buttons[2]
    JM.orange_button = data.buttons[3]
    # print("data.axes", data.axes)
    # print("data.buttons", data.buttons)
    
    return JM

speed_ratio_l = 0   # To slow down linear velocity smoothly
speed_ratio_a = 0   # To slow down angular velocity smoothly
pre_linear_v = 0    # Record previous motion
pre_angular_v = 0   # Record previous motion
full_speed = 0.5    # Highest speed
def choose_action(twist, jmsg):
    ''' Decide Husky's action corresponding to info of an JoyMsg object '''
    global speed_ratio_l
    global speed_ratio_a
    global pre_linear_v
    global pre_angular_v
    global full_speed

    # decide linear velocity
    if jmsg.linear_v:
        if pre_linear_v * jmsg.linear_v == -1:  # Suddenly change of direction leads to speed drop to 0.
            speed_ratio_l = 0
        pre_linear_v = jmsg.linear_v
        twist.linear.x = speed_ratio_l * full_speed * jmsg.linear_v
        speed_ratio_l = speed_ratio_l + 0.04 if speed_ratio_l < 1 else 1
    else:
        twist.linear.x = speed_ratio_l * full_speed * pre_linear_v
        speed_ratio_l = speed_ratio_l - 0.04 if speed_ratio_l > 0 else 0
    
    # decide angular velocity
    if jmsg.angular_v:
        if pre_angular_v * jmsg.angular_v == -1:    # Suddenly change of direction leads to speed drop to 0.
            speed_ratio_a = 0
        pre_angular_v = jmsg.angular_v
        twist.angular.z = speed_ratio_a * full_speed * jmsg.angular_v
        speed_ratio_a = speed_ratio_a + 0.05 if speed_ratio_a < 1 else 1
    else:
        twist.angular.z = speed_ratio_a * full_speed * pre_angular_v
        speed_ratio_a = speed_ratio_a - 0.1 if speed_ratio_a >= 0.1 else 0

    if jmsg.blue_button:    # Car brakes
        twist.linear.x = 0
        twist.angular.z = 0
        speed_ratio_l = 0
        speed_ratio_a = 0

    if jmsg.orange_button:  # Increase full speed
        full_speed = full_speed + 0.025 if full_speed < 1 else 1
    elif jmsg.green_button: # Decrease full speed
        full_speed = full_speed - 0.025 if full_speed > 0.05 else 0.05
    elif jmsg.red_button:   # Reset full speed to 0.5
        twist.linear.x = 0
        twist.angular.z = 0
        speed_ratio_l = 0
        speed_ratio_a = 0
        full_speed = 0.5


    return twist

def callback(data):
    twist = Twist()
    jmsg = JoyMsg()
    jmsg = recieve_joy_msg(jmsg, data)

    twist = choose_action(twist, jmsg)
    
    print('Linear Speed \t %f' % twist.linear.x)
    print('Angular Speed \t %f' % twist.angular.z)
    print('Full Speed \t %f' % full_speed)
    # print('Speed_ratio_a %f' % speed_ratio_a)
    print('------------------------------------------')

    pub.publish(twist)

# Intializes everything
def start():
    # starts the node
    rospy.init_node('Joy2Husky')
    rate = rospy.Rate(10)   # 10 Hz

    # publishing to "/husky_velocity_controller/cmd_vel" to control Husky
    global pub
    pub = rospy.Publisher('joy_teleop/cmd_vel', Twist, queue_size=10)
    # subscribed to joystick inputs on topic "/joy_teleop/joy"
    rospy.Subscriber("/joy_teleop/joy", Joy, callback)
    
    
    rospy.spin()

if __name__ == '__main__':
    try:
        os.system('rosnode kill /joy_teleop/teleop_twist_joy')
    except:
        pass

    try:    
        start()
    except rospy.ROSInterruptException: 
        pass
