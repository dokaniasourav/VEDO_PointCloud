# from cmath import inf
# from vedo import *
# import numpy as np
# import pandas as pd
# import copy
# import math
# import sys
# import time
# from scipy.optimize import minimize
# from scipy.optimize import basinhopping
#
# """
# Get average slop of pt along a path:
# 1. Select 'z' to enter slope avg mode
# 2. Select an existing point to be the origin.
# 3. Your mouse will be tracked at this point, and you can click another point to determine the line which you would like to get pt from
# 4. You will be asked how many pt you will want to contribute to the average slope, and you can specify an number less than the number of available pt, or select all.
# 5. Now the pt used to calculate the average will be shown in yellow, and in the terminal it will print the average slope along their connected line.
# """
#
#
# def keyfunc(event):
#     global points, cpoints, line, lines, selection_mode, plt, structure_created, prism_mesh, z_min, z_max, in_points, inz_points_outxy, above_points, below_points, above_points_outxy, below_points_outxy, pts1, pts2, origin_pre_struct, pre_struct_mode, struct, in_points, below_points, in_z_out_xy_points, above_points, tracking_mode, pre_struct_mode, box_selection_mode, connected_box_points_side1, connected_box_points_side2, top_face, vehicle_mode, slope_avg_mode
#     if event.keyPressed == 'c':
#         # clear pt and lines
#         plt.remove([points, line], render=True)
#         cpoints = []
#         points = None
#         line = None
#         printc("==== Cleared all pt ====", c="r")
#     elif event.keyPressed == "v":
#         print("========ENTER VEHICLE SELECTION MODE========")
#         vehicle_mode = True
#     elif event.keyPressed == "z":
#         print("========ENTER SLOPE AVG MODE========")
#         slope_avg_mode = True
#     elif event.keyPressed == "u":
#         # undo prism creation
#         for actor in plt.actors:
#             plt.remove(actor)
#         plt.remove(plt.actors)
#         # need to twice for some reason to get them all
#         plt.remove(plt.actors)
#         plt.add([mesh, cloud]).render()
#         print("If not all markings are cleared, press 'u' again.")
#         points = None
#         line = None
#         cpoints = []
#         point_ids = []
#         pts1 = []
#         pts2 = []
#         vert = 0
#         z_min = None
#         z_max = None
#         selection_mode = False
#         structure_created = False
#         prism_mesh = None
#         within_out_points = None
#         in_points = None
#         above_points = None
#         below_points = None
#         pre_struct_mode = False
#         origin_pre_struct = None
#         third_clicked_box_pt = None
#         struct = None
#         tracker_line = None
#         tracking_mode = False
#         tracker_line_length = 0
#         tracker_line_angle = 0
#         second_of_three = None
#         first_of_three = None
#         opposite_corner_of_first = None
#         connected_box_points_side1 = []
#         connected_box_points_side2 = []
#         first_box_con_point = None
#
#     # elif event.keyPressed == 's':
#     #     with open(outfl, 'w') as f:
#     #         # uncomment the second line to save the line instead (with 100 pts)
#     #         f.write(str(vector(cpoints)[:,(0,1)])+'\n')
#     #         printc("\nCoordinates saved to file:", outfl, c='y', invert=1)
#
#     elif event.keyPressed == "t":
#         print("CAMERA RESET")
#         my_camera_reset()
#
#     printc('key press:', event.keyPressed)
#
#
# def onLeftClick(event):
#     global first_pt, second_pt, points, cpoints, line, selection_mode, pts1, pts2, origin_pre_struct, structure_created, tracking_mode, tracker_line_length, tracker_line, box_selection_mode, third_clicked_box_pt, first_of_three, second_of_three, first_click_z, last_pt
#     if vehicle_mode:
#         # Add a point and a line
#         try:
#             cpt = list(event.picked3d)
#             cpt = vector(cpt)
#             printc("Added point")
#             cpoints.append(cpt)
#             last_pt = Point(cpt, r=30, c='red')
#             plt.add([last_pt])
#
#             if len(cpoints) > 1:
#                 line = Line(cpoints[-2], cpoints[-1], closed=False).lw(5).c('red')
#                 plt.add([line])
#             plt.render()
#             tracking_mode = True
#         except:
#             print("You must select an existing object")
#     elif slope_avg_mode:
#         try:
#             cpt = list(event.picked3d)
#             cpt = vector(cpt)
#             printc("Added point")
#             cpoints.append(cpt)
#             last_pt = Point(cpt, r=30, c='red')
#             plt.add([last_pt])
#             if len(cpoints) == 2:
#                 line = Line(cpoints[-2], cpoints[-1], closed=False).lw(5).c('red')
#                 plt.add([line])
#
#                 second_pt = np.array([cpt[0], cpt[1], cpt[2]])
#
#                 plt.render()
#                 tracking_mode = False
#                 # Get actual pt
#                 print("GET LINE OF POINTS")
#                 point_list = get_line_of_points(cpoints)
#                 # Get average slope of pt
#                 print("GET AVG SLOPE")
#                 avg_slope_on_line = get_avg_slope(point_list)
#             elif len(cpoints) == 1:
#                 first_pt = np.array([cpt[0], cpt[1], cpt[2]])
#
#             else:
#                 tracking_mode = True
#             plt.render()
#
#
#         except:
#             print("You must select an existing object")
#     printc("Left button pressed")
#
#
# def mouseTrack(event):
#     global tracker_line, tracking_mode, tracker_line_length, angle_label, last_pt
#     if tracking_mode:
#         if not event.actor:
#             return
#         mouse_point = event.picked3d
#         try:
#             plt.remove(tracker_line)
#         except:
#             print("First tracker line")
#         tracker_line = Ruler(last_pt, mouse_point, lw=3, s=3)
#         plt.add([tracker_line])
#         plt.render()
#     return
#
#
# def get_line_of_points(point_vals):
#     x_dir = point_vals[1][0] - point_vals[0][0]
#     y_dir = point_vals[1][1] - point_vals[0][1]
#     magnitude = math.sqrt((x_dir ** 2) + (y_dir ** 2))
#     x_unit = x_dir / magnitude
#     y_unit = y_dir / magnitude
#     start_pt = Point(point_vals[0], r=30, c='black')
#     plt.add([start_pt])
#     plt.render()
#     cur_point = point_vals[0]
#     line_pts = []
#     while round(cur_point[0]) != round(point_vals[1][0]) and round(cur_point[1]) != round(point_vals[1][1]):
#         cur_point = [cur_point[0] + x_unit, cur_point[1] + y_unit, cur_point[2]]
#         cur_point_as_pt = Point(cur_point, r=30, c="purple")
#
#         line_pt = cloud.closestPoint(cur_point)
#         line_pts.append(line_pt)
#     return line_pts
#
#
# def get_slope(pt1, pt2, run):
#     try:
#         slope = (pt2[2] - pt1[2]) / (pt2[run] - pt1[run])
#     except:
#         slope = (pt2[2] - pt1[2]) / 0.00001
#     if slope == math.inf or slope == math.inf * -1 or slope == math.nan:
#         slope = 0
#     return slope
#
#
# def get_avg_slope(line_pts):
#     global first_pt, second_pt
#     # Determine if y or x is longer on the line
#     first_point_x = line_pts[0][0]
#     last_point_x = line_pts[-1][0]
#     x_range = abs(first_point_x - last_point_x)
#     first_point_y = line_pts[0][1]
#     last_point_y = line_pts[-1][1]
#     y_range = abs(first_point_y - last_point_y)
#     # Get correct 2-d slope
#     try:
#         smooth_factor = int(input(
#             "How many pt (+/- 1 due to divisibility) between the start and end do you want to contribute to the avg(num <= to length/ or 'all'). "))
#         if smooth_factor > len(line_pts):
#             smooth_factor = len(line_pts)
#     except:
#         smooth_factor = len(line_pts)
#     if smooth_factor == 0:
#         pts_to_use = [first_pt, second_pt]
#     else:
#         try:
#             step_factor = len(line_pts) // (smooth_factor + 1)
#             pts_to_use = line_pts[0::step_factor]
#         except:
#             step_factor = len(line_pts) // (smooth_factor)
#             pts_to_use = line_pts[0::step_factor]
#         pts_to_use = pts_to_use[1:-1]
#         # pts_to_use.append(line_pts[-1])
#         pts_to_use = [np.asarray(first_pt)] + pts_to_use
#         # pts_to_use[:0] = np.asarray(first_pt)
#         pts_to_use.append(np.asarray(second_pt))
#
#     for p in pts_to_use:
#         cur = Point(p, r=30).c("y")
#         plt.add([cur])
#         plt.render()
#     pts_to_use_df = pd.DataFrame(pts_to_use, columns=["x", "y", "z"])
#     slopes_between_pt_indices = []
#     if x_range >= y_range:
#         pts_to_use_df["y"] = np.nan
#         run = 0
#         # Get slope between x and z axis where x is "run"
#         for pt in range(1, len(pts_to_use)):
#             slopes_between_pt_indices.append(get_slope(pts_to_use[pt - 1], pts_to_use[pt], run))
#     else:
#         pts_to_use_df["x"] = np.nan
#         run = 1
#         # Get slope between y and z axis where y is "run"
#         for pt in range(1, len(pts_to_use)):
#             slopes_between_pt_indices.append(get_slope(pts_to_use[pt - 1], pts_to_use[pt], run))
#     pts_to_use_df.to_csv("pts_used_in_avg_slope_calc.csv")
#     print("SLOPES")
#     print(slopes_between_pt_indices)
#     result = sum(slopes_between_pt_indices) / len(slopes_between_pt_indices)
#     print("RESULT!!! The following is the average slope between the " + str(len(pts_to_use)) + " pts used")
#     print(result)
#     return result
#
#
# def get_perpendicular(pt1, pt2, pt3):
#     v1 = np.array([pt2[0] - pt1[0], pt2[1] - pt1[1], pt2[2] - pt1[2]])
#     v2 = np.array([pt2[0] - pt3[0], pt2[1] - pt3[1], pt2[2] - pt3[2]])
#     return np.cross(v1, v2)
#
#
# def distance_between_points(pt1, pt2):
#     return math.sqrt(((pt1[0] - pt2[0]) ** 2) + ((pt1[1] - pt2[1]) ** 2) + ((pt1[2] - pt2[2]) ** 2))
#
#
# def my_camera_reset():
#     plt.camera.SetPosition([2321420.115, 6926160.299, 995.694])
#     plt.camera.SetFocalPoint([2321420.115, 6926160.299, 702.312])
#     plt.camera.SetViewUp([0.0, 1.0, 0.0])
#     plt.camera.SetDistance(293.382)
#     plt.camera.SetClippingRange([218.423, 388.447])
#     plt.render()
#     print("OK Camera should reset")
#
#
# points = None
# line = None
# cpoints = []
# point_ids = []
# pts1 = []
# pts2 = []
# vert = 0
# z_min = None
# z_max = None
# selection_mode = False
# structure_created = False
# prism_mesh = None
# within_out_points = None
# in_points = None
# above_points = None
# below_points = None
# pre_struct_mode = False
# origin_pre_struct = None
# third_clicked_box_pt = None
# struct = None
# tracker_line = None
# tracking_mode = False
# tracker_line_length = 0
# tracker_line_angle = 0
# second_of_three = None
# first_of_three = None
# opposite_corner_of_first = None
# connected_box_points_side1 = []
# connected_box_points_side2 = []
# first_box_con_point = None
# angle_of_first = None
# first_to_third_angle = None
# dim2 = 0
# same_for_each = None
# angle_label = None
# first_click_z = None
# top_face = None
# tracker_line_one_to_two_length = None
# front_back_rot_angle = 0
# side_rot_angle = 0
# front_back_rot_point = None
# side_rot_point = None
# rot_point = None
# x_unit = None
# y_unit = None
# first_pt = None
# second_pt = None
#
# vehicle_mode = False
# slope_avg_mode = False
# vehicle = None
# last_pt = False
# lines = None
# cur_direction = None
#
# box_selection_mode = False
# structures = []
# perpendicular = ""
#
# cloud = load(sys.argv[1]).pointSize(3.5)
# # print(cloud)
# # print("CLOUD CENTER")
# # print(cloud_center)
# # z_center = cloud_center[2]
# #
# mesh = delaunay2D(cloud.points()).alpha(0.1).c("white")
# #
# # cam = dict(pos=(cloud_center),
# #            focalPoint=(2321420.115, 6926160.299, 702.312),
# #            viewup=(0, 1.00, 0),
# #            distance=293.382,
# #            clippingRange=(218.423, 388.447))
# #
# plt = Plotter()
# plt.addCallback('KeyPress', keyfunc)
# plt.addCallback('LeftButtonPress', onLeftClick)
# # plt.addCallback('RightButtonPress', onRightClick)
# plt.addCallback('MouseMove', mouseTrack)
# # print("Once the program launches, press 'h' for list of default commands")
# #
# plt.show([mesh, cloud], interactorStyle=0, bg='white', axes=1)
#
# interactive()
#
