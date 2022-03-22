from vedo import *
import numpy as np
import pandas as pd
import copy
import math
import sys
import time
from scipy.optimize import minimize
from scipy.optimize import basinhopping

"""
See if points touch a vehicle as it is moving along a path:
1. Select 'v' to enter vehicle selection mode
2. Select an existing point to be the origin of the vehicle.
3. Your mouse will be tracked at this point, and you can click as many existing points to determine the path of the vehicle. 
4. Right click to say that there are no more points in the path
5. Define the dimensions of the vehicle. (Only confirmed to work well with vehicles with 2 sets of wheels) And the vehicle will appear in red.
6. Press spacebar to make the vehicle run an algorithm to try to get level to the ground. 
7. Press spacebar once more to begin the vehicle's trip along the path. Let the program run and the the vehicle will automatically move along the track. 
8. You will need to repeat 6. and 7. whenever the vehicle reaches a point where it needs to turn.
9. If at any point on the path, the body of the vehicle is touching any points, an output file will be made showing what points are touching. 
"""


# Constantly checking if any meaningful key is selected
def keyfunc(evt):
    global points, cpoints, line, lines, selection_mode, plt, structure_created, prism_mesh, z_min, z_max, pts1, pts2, origin_pre_struct, pre_struct_mode, struct, tracking_mode, pre_struct_mode, box_selection_mode, connected_box_points_side1, connected_box_points_side2, top_face, vehicle_mode
    if evt.keyPressed == 'c':
        # clear points and lines
        plt.remove([points, line], render=True)
        cpoints = []
        line = None
        printc("==== Cleared all points ====", c="r")
    elif evt.keyPressed == "v":
        # Vehicle selection mode
        print("========ENTER VEHICLE SELECTION MODE========")
        vehicle_mode = True
    elif evt.keyPressed == "u":
        # undo prism creation
        for actor in plt.actors:
            plt.remove(actor)
        plt.remove(plt.actors)
        # need to twice for some reason to get them all
        plt.remove(plt.actors)
        plt.add([mesh, cloud]).render()
        print("If not all markings are cleared, press 'u' again.")
        # Reset variables
        line = None
        cpoints = []
        point_ids = []
        pts1 = []
        pts2 = []
        vert = 0
        z_min = None
        z_max = None
        selection_mode = False
        structure_created = False
        prism_mesh = None
        pre_struct_mode = False
        origin_pre_struct = None
        third_clicked_box_pt = None
        struct = None
        tracker_line = None
        tracking_mode = False
        tracker_line_length = 0
        tracker_line_angle = 0
        second_of_three = None
        first_of_three = None
        opposite_corner_of_first = None
        connected_box_points_side1 = []
        connected_box_points_side2 = []
        first_box_con_point = None

    # elif event.keyPressed == 's':
    #     with open(outfl, 'w') as f:
    #         # uncomment the second line to save the line instead (with 100 pts)
    #         f.write(str(vector(cpoints)[:,(0,1)])+'\n')
    #         printc("\nCoordinates saved to file:", outfl, c='y', invert=1)

    elif evt.keyPressed == "t":
        print("CAMERA RESET")
        my_camera_reset()

    printc('key press:', evt.keyPressed)


def onLeftClick(event):
    global points, cpoints, line, selection_mode, pts1, pts2, origin_pre_struct, structure_created, tracking_mode, tracker_line_length, tracker_line, box_selection_mode, third_clicked_box_pt, first_of_three, second_of_three, first_click_z, last_pt
    if vehicle_mode:
        # Add a point and a line
        try:
            cpt = list(event.picked3d)
            cpt = vector(cpt)
            printc("Added point")
            cpoints.append(cpt)
            last_pt = Point(cpt, r=30, c='red')
            plt.add([last_pt])
            if len(cpoints) > 1:
                line = Line(cpoints[-2], cpoints[-1], closed=False).lw(5).c('red')
                plt.add([line])
            plt.render()
            tracking_mode = True
        except:
            # The selected by the clicks must be already existing points
            print("You must select an existing object")
    printc("Left button pressed")


def onRightClick(event):
    global origin_pre_struct, second_of_three, tracking_mode, lines
    # The right click to finish setting the path
    if vehicle_mode == True:
        tracking_mode = False
        line_points = []
        for pt in range(1, len(cpoints)):
            line_points.append([cpoints[pt - 1], cpoints[pt]])
        lines = Lines(line_points).triangulate()
        create_vehicle()
    return


def mouseTrack(event):
    global tracker_line, tracking_mode, tracker_line_length, angle_label, last_pt
    if tracking_mode:
        # When in tracking mode, a ruler will appear at mouse endpoint
        if not event.actor:
            return
        mouse_point = event.picked3d
        try:
            plt.remove(tracker_line)
        except:
            print("First tracker line")
        tracker_line = Ruler(last_pt, mouse_point, lw=3, s=3)
        plt.add([tracker_line])
        plt.render()
    return


# Crete a simulated vehicle
def create_vehicle():
    global vehicle, front_overhang, back_overhang, wheel_radius, v_len, v_width
    # User defines dimensions
    back_overhang = float(input("What should be the back overhang of the vehicle?"))
    front_overhang = float(input("What should be the front overhang of the vehicle?"))
    wheel_radius = float(input("What should be the wheel radius"))
    wheel_set_count = int(input("How many sets of wheels should there be?"))
    wheel_base = float(input("How long should the wheel base be?"))
    v_len = sum([back_overhang, front_overhang, wheel_radius * 2 * wheel_set_count, wheel_base * (wheel_base - 1)])
    v_width = float(input("What should be the width of the vehicle?"))

    vehicle_origin = cpoints[0]
    vehicle_origin[2] += wheel_radius
    # Vehicle wheel base represented on screen
    vehicle = Box(vehicle_origin, length=v_len, width=v_width, height=0.1)

    simulate_vehicle_on_line()


def get_slope_and_yInt(pt1, pt2):
    try:
        slope = (pt2[1] - pt1[1]) / (pt2[0] - pt1[0])
        y_int = pt1[1] - (slope * pt1[0])
        return slope, y_int
    except:
        slope = 1000000
        y_int = pt1[1] - (slope * pt1[0])
        return slope, y_int


def get_perpendicular(pt1, pt2, pt3):
    v1 = np.array([pt2[0] - pt1[0], pt2[1] - pt1[1], pt2[2] - pt1[2]])
    v2 = np.array([pt2[0] - pt3[0], pt2[1] - pt3[1], pt2[2] - pt3[2]])
    return np.cross(v1, v2)


def distance_between_points(pt1, pt2):
    return math.sqrt(((pt1[0] - pt2[0]) ** 2) + ((pt1[1] - pt2[1]) ** 2) + ((pt1[2] - pt2[2]) ** 2))


def define_corners(vehicle):
    global lines, front_overhang, back_overhang, wheel_radius, v_len, v_width, cur_direction
    # Get the corners of the vehicle
    min_X = vehicle.points()[vehicle.points()[:, [0]].sum(axis=1).argmin()]
    max_X = vehicle.points()[vehicle.points()[:, [0]].sum(axis=1).argmax()]
    min_Y = vehicle.points()[vehicle.points()[:, [1]].sum(axis=1).argmin()]
    max_Y = vehicle.points()[vehicle.points()[:, [1]].sum(axis=1).argmax()]

    # Get the vehicles direction
    if cur_direction == "northeast":
        front_left = max_Y
        front_right = max_X
        back_left = min_X
        back_right = min_Y

    elif cur_direction == "northwest":
        front_left = min_X
        front_right = max_Y
        back_left = min_Y
        back_right = max_X

    elif cur_direction == "southwest":
        front_left = min_Y
        front_right = min_X
        back_left = max_X
        back_right = max_Y

    elif cur_direction == "southeast":
        front_left = max_X
        front_right = min_Y
        back_left = max_Y
        back_right = min_X

    # Gets the change in z accross each edge of the vehicle
    left_side_z_unit = abs(front_left[2] - back_left[2]) / v_len
    right_side_z_unit = abs(front_right[2] - back_right[2]) / v_len
    front_z_unit = abs(front_right[2] - front_left[2]) / v_width
    back_z_unit = abs(back_right[2] - back_left[2]) / v_width

    # Get points on the body of the vehicle that are above the tires
    vehicle_tire_body_front_right = [front_right[0] - abs(x_unit) * (wheel_radius + front_overhang),
                                     front_right[1] - abs(y_unit) * (wheel_radius + front_overhang),
                                     front_right[2] - abs(right_side_z_unit) * (wheel_radius + front_overhang)]
    vehicle_tire_body_front_left = [front_left[0] - abs(x_unit) * (wheel_radius + front_overhang),
                                    front_left[1] - abs(y_unit) * (wheel_radius + front_overhang),
                                    front_left[2] - abs(left_side_z_unit) * (wheel_radius + front_overhang)]
    vehicle_tire_body_back_left = [back_left[0] + abs(x_unit) * (wheel_radius + back_overhang),
                                   back_left[1] + abs(y_unit) * (wheel_radius + back_overhang),
                                   back_left[2] + abs(left_side_z_unit) * (wheel_radius + back_overhang)]
    vehicle_tire_body_back_right = [back_right[0] + abs(x_unit) * (wheel_radius + back_overhang),
                                    back_right[1] + abs(y_unit) * (wheel_radius + back_overhang),
                                    back_right[2] + abs(right_side_z_unit) * (wheel_radius + back_overhang)]
    return front_left, front_right, back_left, back_right, vehicle_tire_body_front_right, vehicle_tire_body_front_left, vehicle_tire_body_back_left, vehicle_tire_body_back_right


def get_tire_contact_points(vehicle, vehicle_tire_body_front_right, vehicle_tire_body_front_left,
                            vehicle_tire_body_back_left, vehicle_tire_body_back_right, perp_vector):
    global lines, front_overhang, back_overhang, wheel_radius, v_len, v_width, cur_direction
    # Get high and low points far above and below the corners
    vehicle_point_front_right_high = vehicle_tire_body_front_right.copy()
    vehicle_point_front_left_high = vehicle_tire_body_front_left.copy()
    vehicle_point_back_left_high = vehicle_tire_body_back_left.copy()
    vehicle_point_back_right_high = vehicle_tire_body_back_right.copy()

    vehicle_point_back_left_high = [sum(x) for x in zip(vehicle_point_back_left_high, perp_vector)]
    vehicle_point_front_right_high = [sum(x) for x in zip(vehicle_point_front_right_high, perp_vector)]
    vehicle_point_back_right_high = [sum(x) for x in zip(vehicle_point_back_left_high, perp_vector)]
    vehicle_point_front_left_high = [sum(x) for x in zip(vehicle_point_back_left_high, perp_vector)]

    vehicle_point_front_right_low = vehicle_tire_body_front_right.copy()
    vehicle_point_front_left_low = vehicle_tire_body_front_left.copy()
    vehicle_point_back_left_low = vehicle_tire_body_back_left.copy()
    vehicle_point_back_right_low = vehicle_tire_body_back_right.copy()

    vehicle_point_back_left_low = [x - y for x, y in zip(vehicle_point_back_left_low, perp_vector)]
    vehicle_point_front_right_low = [x - y for x, y in zip(vehicle_point_front_right_low, perp_vector)]
    vehicle_point_back_right_low = [x - y for x, y in zip(vehicle_point_back_right_low, perp_vector)]
    vehicle_point_front_left_low = [x - y for x, y in zip(vehicle_point_front_left_low, perp_vector)]

    # Get the points on the ground where the tires make contact
    tire_contact_front_right = mesh.intersectWithLine(vehicle_point_front_right_high, vehicle_point_front_right_low)[0]
    tire_contact_front_left = mesh.intersectWithLine(vehicle_point_front_left_high, vehicle_point_front_left_low)[0]
    tire_contact_back_left = mesh.intersectWithLine(vehicle_point_back_left_high, vehicle_point_back_left_low)[0]
    tire_contact_back_right = mesh.intersectWithLine(vehicle_point_back_right_high, vehicle_point_back_right_low)[0]
    return tire_contact_front_right, tire_contact_front_left, tire_contact_back_left, tire_contact_back_right


def get_rotation_angles(front_left, front_right, back_left, back_right, tire_contact_front_left,
                        tire_contact_front_right, tire_contact_back_left, tire_contact_back_right,
                        vehicle_tire_body_front_right, vehicle_tire_body_front_left, vehicle_tire_body_back_left,
                        vehicle_tire_body_back_right):
    # Calculate the angles that the vehicle base should rotate in 3d space
    length = sqrt(((tire_contact_back_left[1] - tire_contact_front_right[1]) ** 2) + (
                (tire_contact_back_left[0] - tire_contact_front_right[0]) ** 2))

    z_change_left_side = tire_contact_front_left[2] - tire_contact_back_left[2]  # long side

    z_change_right_side = tire_contact_front_right[2] - tire_contact_back_right[2]  # long side

    z_change_front_side = tire_contact_front_left[2] - tire_contact_front_right[2]  # front/back

    z_change_back_side = tire_contact_back_right[2] - tire_contact_back_left[2]  # front/back

    vehicle_vert_angle_left_side = math.degrees(math.atan2(length, z_change_left_side))
    if vehicle_vert_angle_left_side > 180:
        vehicle_vert_angle_left_side = -1 * (vehicle_vert_angle_left_side - 180)

    vehicle_vert_angle_right_side = math.degrees(math.atan2(length, z_change_right_side))
    if vehicle_vert_angle_right_side > 180:
        vehicle_vert_angle_right_side = -1 * (vehicle_vert_angle_right_side - 180)

    vehicle_vert_angle_front_side = math.degrees(math.atan2(length, z_change_front_side))
    if vehicle_vert_angle_front_side > 180:
        vehicle_vert_angle_front_side = -1 * (vehicle_vert_angle_front_side - 180)

    vehicle_vert_angle_back_side = math.degrees(math.atan2(length, z_change_back_side))
    if vehicle_vert_angle_back_side > 180:
        vehicle_vert_angle_back_side = -1 * (vehicle_vert_angle_back_side - 180)

    front_back_rot_angle = (vehicle_vert_angle_left_side + vehicle_vert_angle_right_side) / 2

    side_rot_angle = (vehicle_vert_angle_front_side + vehicle_vert_angle_back_side) / 2

    print("Rotation VALUES!!!")
    print(front_back_rot_angle - 90)  # Front back
    print(side_rot_angle - 90)  # side to side
    # Picks the correct points on body to pivot/rotate on
    if (front_back_rot_angle - 90) > 0:
        front_back_rot_point = vehicle_tire_body_back_left
    else:
        front_back_rot_point = vehicle_tire_body_front_left
    if (side_rot_angle - 90) > 0:
        side_rot_point = vehicle_tire_body_front_left
    else:
        side_rot_point = vehicle_tire_body_front_right
    rot_point = [(front_left[0] + front_right[0] + back_left[0] + back_right[0]) / 4,
                 (front_left[1] + front_right[1] + back_left[1] + back_right[1]) / 4,
                 (front_left[2] + front_right[2] + back_left[2] + back_right[2]) / 4, ]

    return front_back_rot_angle, side_rot_angle, front_back_rot_point, side_rot_point, rot_point


# TODO: THIS COULD BE IMPROVED --> The initialization of the vehicle is not accurate when it is initialized on significant slopes
def minimum_avg_dist_to_ground(params):
    global vehicle, lines, front_overhang, back_overhang, wheel_radius, v_len, v_width, cur_direction, front_back_rot_angle, side_rot_angle, x_unit, y_unit, front_back_rot_point, side_rot_point, rot_point
    test_front_back_rot_angle, test_side_rot_angle = params

    temp_vehicle = vehicle.clone()
    # Try a rotation to the vehicle
    temp_vehicle.rotate(test_front_back_rot_angle - 90, axis=(-1 * x_unit, y_unit, 0), point=rot_point)

    temp_vehicle.rotate((test_side_rot_angle - 90) * -1, axis=(x_unit, y_unit, 0), point=rot_point)

    # Need to get the points and directions again
    front_left, front_right, back_left, back_right, vehicle_tire_body_front_right, vehicle_tire_body_front_left, vehicle_tire_body_back_left, vehicle_tire_body_back_right = define_corners(
        temp_vehicle)

    vehicle_tire_body_front_right_ASPOINT = Point(vehicle_tire_body_front_right, r=25).c("b")
    vehicle_tire_body_front_left_ASPOINT = Point(vehicle_tire_body_front_left, r=25).c("y")
    vehicle_tire_body_back_left_ASPOINT = Point(vehicle_tire_body_back_left, r=25).c("w")
    vehicle_tire_body_back_right_ASPOINT = Point(vehicle_tire_body_back_right, r=25).c("p")
    # plt.add([vehicle_tire_body_front_right_ASPOINT, vehicle_tire_body_front_left_ASPOINT, vehicle_tire_body_back_left_ASPOINT, vehicle_tire_body_back_right_ASPOINT])
    # plt.render()

    # Get vector perpendicular to the body
    perp_vector = get_perpendicular(vehicle_tire_body_back_left, vehicle_tire_body_front_right,
                                    vehicle_tire_body_back_right)

    # Get points on the ground where the ground makes contact with the tires
    tire_contact_front_right, tire_contact_front_left, tire_contact_back_left, tire_contact_back_right = get_tire_contact_points(
        temp_vehicle, vehicle_tire_body_front_right, vehicle_tire_body_front_left, vehicle_tire_body_back_left,
        vehicle_tire_body_back_right, perp_vector)

    tire_contact_front_right_ASPOINT = Point(tire_contact_front_right, r=15).c("y")
    tire_contact_front_left_ASPOINT = Point(tire_contact_front_left, r=15).c("y")
    tire_contact_back_left_ASPOINT = Point(tire_contact_back_left, r=15).c("y")
    tire_contact_back_right_ASPOINT = Point(tire_contact_back_right, r=15).c("y")
    # plt.add([tire_contact_front_right_ASPOINT, tire_contact_front_left_ASPOINT, tire_contact_back_left_ASPOINT, tire_contact_back_right_ASPOINT])
    # plt.render()

    error_margin = (wheel_radius - 0.1)

    # Check if contact points are below points on body --> This may not be a concern?
    if vehicle_tire_body_back_left[2] >= (tire_contact_back_left[2] + error_margin) and vehicle_tire_body_back_right[
        2] >= (tire_contact_back_right[2] + error_margin) and vehicle_tire_body_front_left[2] >= (
            tire_contact_front_left[2] + error_margin) and vehicle_tire_body_front_right[2] > (
            tire_contact_front_right[2] + error_margin):
        # Get average height of points to the ground
        avg_height = (distance_between_points(tire_contact_back_left,
                                              vehicle_tire_body_back_left) + distance_between_points(
            tire_contact_back_right, vehicle_tire_body_back_right) + distance_between_points(tire_contact_front_left,
                                                                                             vehicle_tire_body_front_left) + distance_between_points(
            tire_contact_front_right, vehicle_tire_body_front_right)) / 4
    else:
        print("Below body")
        avg_height = 100000
    # avg_height = (distance_between_points(tire_contact_back_left, vehicle_tire_body_back_left) + distance_between_points(tire_contact_back_right, vehicle_tire_body_back_right) + distance_between_points(tire_contact_front_left, vehicle_tire_body_front_left) + distance_between_points(tire_contact_front_right, vehicle_tire_body_front_right))/ 4
    print("AVG HEIGHT")
    print(avg_height)
    return avg_height


# FUNCTION TO GET MINIMUM AVERAGE DISTANCE TO GROUND FROM EACH POINT
def first_initialization_rotate_to_ground():
    global vehicle, lines, front_overhang, back_overhang, wheel_radius, v_len, v_width, cur_direction, front_back_rot_angle, side_rot_angle, x_unit, y_unit, front_back_rot_point, side_rot_point, rot_point
    # Loop through different rotations to get average heights off the ground

    front_left, front_right, back_left, back_right, vehicle_tire_body_front_right, vehicle_tire_body_front_left, vehicle_tire_body_back_left, vehicle_tire_body_back_right = define_corners(
        vehicle)

    perp_vector = get_perpendicular(vehicle_tire_body_back_left, vehicle_tire_body_front_right,
                                    vehicle_tire_body_back_right)

    tire_contact_front_right, tire_contact_front_left, tire_contact_back_left, tire_contact_back_right = get_tire_contact_points(
        vehicle, vehicle_tire_body_front_right, vehicle_tire_body_front_left, vehicle_tire_body_back_left,
        vehicle_tire_body_back_right, perp_vector)

    # We have the (PREDICTED)ground points where the wheels make contact, get slope and match the slope of the box to it
    front_back_rot_angle, side_rot_angle, front_back_rot_point, side_rot_point, rot_point = get_rotation_angles(
        front_left, front_right, back_left, back_right, tire_contact_front_left, tire_contact_front_right,
        tire_contact_back_left, tire_contact_back_right, vehicle_tire_body_front_right, vehicle_tire_body_front_left,
        vehicle_tire_body_back_left, vehicle_tire_body_back_right)
    # RUN SCIPY OPTIMIZE
    print("STARTING TO OPTIMIZE")
    print("ROT POINT")
    print(rot_point)
    bnds = ((45, 135), (45, 135))
    minimizer_kwargs = {"method": "L-BFGS-B", "bounds": bnds}
    # val = basinhopping(minimum_avg_dist_to_ground, np.array([front_back_rot_angle, side_rot_angle]), niter = 2000,disp = True, stepsize = 1, minimizer_kwargs=minimizer_kwargs)

    # This tries to find the minimum distance to the ground
    val = minimize(minimum_avg_dist_to_ground, [front_back_rot_angle, side_rot_angle],
                   options={'gtol': 0.01, 'disp': True})

    print("DONE!!")
    print(val)
    fitted_params = val.x

    # Rotate the vehicle to the point that was determined to be the best starting point
    front_back_rot_angle = fitted_params[0]
    side_rot_angle = fitted_params[1]
    vehicle.rotate(front_back_rot_angle - 90, axis=(-1 * x_unit, y_unit, 0), point=rot_point)

    vehicle.rotate((side_rot_angle - 90) * -1, axis=(x_unit, y_unit, 0), point=rot_point)

    plt.show()


def rotate_vehicle_to_ground():
    global vehicle, lines, front_overhang, back_overhang, wheel_radius, v_width, cur_direction, front_back_rot_angle, side_rot_angle, x_unit, y_unit, front_back_rot_point, side_rot_point, rot_point

    # Rotate to the ground at any point after initialization
    last_front_back_rot_angle = front_back_rot_angle
    last_side_rot_angle = side_rot_angle

    front_left, front_right, back_left, back_right, vehicle_tire_body_front_right, vehicle_tire_body_front_left, vehicle_tire_body_back_left, vehicle_tire_body_back_right = define_corners(
        vehicle)

    test1 = Point(front_left, r=20).c("r")
    test2 = Point(back_left, r=20).c("g")
    test3 = Point(front_right, r=20).c("p")
    test4 = Point(back_right, r=20).c("b")
    # plt.add([test1, test2,test3, test4])

    # Get perpendicular direction to tire contact
    perp_vector = get_perpendicular(vehicle_tire_body_back_left, vehicle_tire_body_front_right,
                                    vehicle_tire_body_back_right)

    tire_contact_front_right, tire_contact_front_left, tire_contact_back_left, tire_contact_back_right = get_tire_contact_points(
        vehicle, vehicle_tire_body_front_right, vehicle_tire_body_front_left, vehicle_tire_body_back_left,
        vehicle_tire_body_back_right, perp_vector)

    tire_contact_front_right_ASPOINT = Point(tire_contact_front_right, r=10).c("b")
    tire_contact_front_left_ASPOINT = Point(tire_contact_front_left, r=10).c("y")
    tire_contact_back_left_ASPOINT = Point(tire_contact_back_left, r=10).c("w")
    tire_contact_back_right_ASPOINT = Point(tire_contact_back_right, r=10).c("p")

    # We have the ground points where the wheels make contact, get slope and match the slope of the box to it
    front_back_rot_angle, side_rot_angle, front_back_rot_point, side_rot_point, rot_point = get_rotation_angles(
        front_left, front_right, back_left, back_right, tire_contact_front_left, tire_contact_front_right,
        tire_contact_back_left, tire_contact_back_right, vehicle_tire_body_front_right, vehicle_tire_body_front_left,
        vehicle_tire_body_back_left, vehicle_tire_body_back_right)

    print("XY UNITS")
    print(x_unit)
    print(y_unit)

    print("ROTATION ANGLES")
    print(last_front_back_rot_angle)
    print(last_side_rot_angle)
    print(front_back_rot_angle)
    print(side_rot_angle)
    # Try a rotation to the vehicle
    vehicle.rotate(front_back_rot_angle - last_front_back_rot_angle, axis=(-1 * x_unit, y_unit, 0), point=rot_point)

    vehicle.rotate((side_rot_angle - last_side_rot_angle) * -1, axis=(x_unit, y_unit, 0), point=rot_point)

    # comment this out for fluid movement
    # plt.show()
    plt.render()


# Starts the chain of functions to simulate the vehicle on the line
def simulate_vehicle_on_line():
    global vehicle, lines, front_overhang, back_overhang, wheel_radius, v_width, cur_direction, x_unit, y_unit
    unique_points = [np.unique(sub_arr) for sub_arr in lines.points()]
    tracker_line_angle = None
    last_tracker_line_angle = None
    for val in range(len(unique_points) - 1):
        pt1 = lines.points()[val]
        pt2 = lines.points()[val + 1]

        if pt1[0] == pt2[0] and pt1[1] == pt1[1]:
            continue

        # Rotate to the next line
        dY = pt2[1] - pt1[1]
        dX = pt2[0] - pt1[0]
        # define cur_direction
        if dX >= 0 and dY >= 0:
            cur_direction = "northeast"
        elif dX < 0 and dY >= 0:
            cur_direction = "northwest"
        elif dX < 0 and dY < 0:
            cur_direction = "southwest"
        else:
            cur_direction = "southeast"
        if tracker_line_angle != None:
            print("ROTATE AT NEW POINT")
            last_tracker_line_angle = tracker_line_angle
            tracker_line_angle = math.degrees(math.atan2(dY, dX))
            if tracker_line_angle > 180:
                tracker_line_angle = -1 * (tracker_line_angle - 180)
            vehicle = vehicle.rotate((-1 * last_tracker_line_angle) + tracker_line_angle, axis=(0, 0, 1), point=pt1).c(
                "r")
        else:
            tracker_line_angle = math.degrees(math.atan2(dY, dX))
            if tracker_line_angle > 180:
                tracker_line_angle = -1 * (tracker_line_angle - 180)
            vehicle = vehicle.rotate(tracker_line_angle, axis=(0, 0, 1), point=pt1).c("r")
            plt.add([vehicle])
        plt.show()

        # Get slope of each line, move by a value in that direction
        slope, y_int = get_slope_and_yInt(pt1, pt2)

        x_dir = pt2[0] - pt1[0]
        y_dir = pt2[1] - pt1[1]
        magnitude = math.sqrt((x_dir ** 2) + (y_dir ** 2))
        x_unit = x_dir / magnitude
        y_unit = y_dir / magnitude

        # Make parallel to the ground
        first_initialization_rotate_to_ground()
        get_intersecting_points()

        # Move along line
        while round(vehicle.pos()[0]) != round(pt2[0]) and round(vehicle.pos()[1]) != round(pt2[1]):
            print("START")
            x_dir = pt2[0] - pt1[0]
            y_dir = pt2[1] - pt1[1]
            magnitude = math.sqrt((x_dir ** 2) + (y_dir ** 2))
            x_unit = x_dir / magnitude
            y_unit = y_dir / magnitude
            vehicle.shift(x_unit, y_unit, 0)
            # Make parallel to the ground

            rotate_vehicle_to_ground()
            print("SHIFTED")
            print("START CHECK")
            get_intersecting_points()
            print("FINISH CHECK")
    print("AT DESTINATION")


def get_intersecting_points():
    # This is the line where the slowdown is happening, C++ programming may be able to speed this up
    intersect_pts = vehicle.insidePoints(cloud.points())
    try:
        df_in = pd.DataFrame(data=np.asarray(intersect_pts.points()), columns=["x", "y", "z"])
    except:
        df_in = pd.DataFrame(columns=["x", "y", "z"])
    if df_in.shape[0] > 0:
        df_in.to_csv(f"{vehicle.x()}_{vehicle.y()}_{vehicle.z()}.csv", index=False)
        print("File Saved!")
        print(len(cloud.points()))
        print(df_in.shape)
        print("___________----")
    else:
        print("No touching points")


def my_camera_reset():
    plt.camera.SetPosition([2321420.115, 6926160.299, 995.694])
    plt.camera.SetFocalPoint([2321420.115, 6926160.299, 702.312])
    plt.camera.SetViewUp([0.0, 1.0, 0.0])
    plt.camera.SetDistance(293.382)
    plt.camera.SetClippingRange([218.423, 388.447])
    plt.render()
    print("OK Camera should reset")


line = None
cpoints = []
point_ids = []
pts1 = []
pts2 = []
vert = 0
z_min = None
z_max = None
selection_mode = False
structure_created = False
prism_mesh = None

pre_struct_mode = False
origin_pre_struct = None
third_clicked_box_pt = None
struct = None
tracker_line = None
tracking_mode = False
tracker_line_length = 0
tracker_line_angle = 0
second_of_three = None
first_of_three = None
opposite_corner_of_first = None
connected_box_points_side1 = []
connected_box_points_side2 = []
first_box_con_point = None
angle_of_first = None
first_to_third_angle = None
dim2 = 0
same_for_each = None
angle_label = None
first_click_z = None
top_face = None
tracker_line_one_to_two_length = None
front_back_rot_angle = 0
side_rot_angle = 0
front_back_rot_point = None
side_rot_point = None
rot_point = None
x_unit = None
y_unit = None

vehicle_mode = False
vehicle = None
last_pt = False
lines = None
cur_direction = None

box_selection_mode = False
structures = []
perpendicular = ""

cloud = load(sys.argv[1]).pointSize(3.5)

cloud_center = cloud.centerOfMass()
print("CLOUD CENTER")
print(cloud_center)
z_center = cloud_center[2]

mesh = delaunay2D(cloud.points()).alpha(0.1).c("white")

cam = dict(pos=(cloud_center),
           focalPoint=(2321420.115, 6926160.299, 702.312),
           viewup=(0, 1.00, 0),
           distance=293.382,
           clippingRange=(218.423, 388.447))

plt = Plotter()
plt.addCallback('KeyPress', keyfunc)
plt.addCallback('LeftButtonPress', onLeftClick)
plt.addCallback('RightButtonPress', onRightClick)
plt.addCallback('MouseMove', mouseTrack)
print("Once the program launches, press 'h' for list of default commands")

plt.show([mesh, cloud], interactorStyle=0, bg='white', axes=1)  # , camera = cam)

interactive()
