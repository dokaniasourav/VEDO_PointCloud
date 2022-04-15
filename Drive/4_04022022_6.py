# import multiprocessing
# import os
# import sys
# import csv
# import time
# import random
# import numpy as np
# import tkinter as tk
#
# import vedo
# from vedo import *
# from datetime import datetime
# import typing
# from tkinter import filedialog
#
# # import dill
# # import concurrent.futures
# # import threading
#
# RD_1 = 20
# RD_2 = 15
# RD_3 = 10
# RD_4 = 8
#
# TEXT_SIZE = 1
# TEXT_SPACING = 2
# SCALE_FACTOR = 0.2
#
# '''Script for plotting and finding average slope of points along a path:
#
# 1. Firstly, click on the map to initialize it
# 2. Enter 'z' or 'Z' to enter slope avg mode
# 3. You can now see instructions in map as well.
#    Select any two points and use the slider to provide the number of points required
# 4. You will be asked how many pt you will want to contribute to the average
#    slope, and you can specify an number less than the number of available pt, or select all
# 5. CSV file will be created with the slope values
# '''
#
#
# # Constantly checking if any meaningful key is selected
# def on_key_press(event):
#     global plt, g_plot
#     g_plot.last_key_press = event.keyPressed
#     if event.keyPressed in ['c', 'C']:
#         # clear pt and lines
#         for point in g_plot.plotted_points:
#             plt.remove(point, render=True)
#         for t_line in g_plot.plotted_trackers:
#             plt.remove(t_line, render=True)
#         for p_line in g_plot.plotted_lines:
#             plt.remove(p_line, render=True)
#         plt.sliders = g_plot.current_points = []
#         g_plot.plotted_points = g_plot.plotted_lines = g_plot.plotted_trackers = []
#         printc("==== Cleared all points on plot ====", c="r")
#         for i in range(1, 6):
#             update_text(f'text{i}', '')
#         update_text('text4', 'Cleared everything on the plot')
#         update_text('text5', 'Press R to enter rectangle mode')
#         update_text('text6', 'Press Z to enter slope mode')
#     elif event.keyPressed == 'Escape':
#         plt.clear()
#         exit()
#     elif event.keyPressed in ['z', 'Z']:
#         if not g_plot.rectangle_mode:
#             print("=== ENTER SLOPE AVG MODE ====")
#             update_text('text5', 'Slope averaging is ON')
#             g_plot.slope_avg_mode = True
#     elif event.keyPressed in ['R', 'r']:
#         if not g_plot.slope_avg_mode:
#             print("=== ENTER RECTANGLE MODE ====")
#             update_text('text5', 'Rectangle mode is ON')
#             g_plot.rectangle_mode = True
#     elif event.keyPressed in ['u', 'U']:
#         reset_plot()
#     elif event.keyPressed == 't':
#         my_camera_reset()
#     # elif event.keyPressed in [str(e) for e in range(0, 9)]:
#     #     handle_inp()
#
#
# def enter_callback(event):
#     global g_plot
#     if not g_plot.initialized:
#         update_text('text1', '', [2, -2 * TEXT_SPACING, 5])
#         update_text('text2', 'SlopeAVG and Tracking: OFF', [2, -3 * TEXT_SPACING, 5])
#         update_text('text3', '', [2, -4 * TEXT_SPACING, 5])
#         update_text('text4', 'Press Z to enter slope mode',
#                     [3, g_plot.max_xyz[1] - g_plot.min_xyz[1] + 3 * TEXT_SPACING, 5])
#         update_text('text5', 'Press R to enter slope mode',
#                     [3, g_plot.max_xyz[1] - g_plot.min_xyz[1] + 2 * TEXT_SPACING, 5])
#         update_text('text6', '', [3, g_plot.max_xyz[1] - g_plot.min_xyz[1] + 1 * TEXT_SPACING, 5])
#         # all_tasks['timer_id'] = plt.timerCallback('create', dt=10)
#         g_plot.initialized = True
#     if g_plot.timerID is not None:
#         plt.timerCallback('destroy', timerId=g_plot.timerID)
#         g_plot.timerID = None
#
#
# def leave_callback(event):
#     global g_plot, all_tasks
#     # if 'timer_id' in all_tasks.keys():
#     #     return
#     # if g_plot.timerID is None:
#     #     g_plot.timerID = plt.timerCallback('create', dt=500)
#
#
# def on_left_click(event):
#     global g_plot, cloud
#     global max_points
#
#     if event.picked3d is None:
#         return
#
#     # find_closest_point(vector(list(event.picked3d)))
#
#     if g_plot.slider_selected:
#         # Get actual pt
#         plt.sliders = []
#         plt.render()
#         print(f'Number of pt on the line: {max_points}')
#         update_text('text4', f'Please wait ...')
#         get_avg_slope()
#         g_plot.slider_selected = False
#         g_plot.current_points = []
#
#     if g_plot.slope_avg_mode or g_plot.rectangle_mode:
#         cpt2 = vector(list(event.picked3d))
#         cpt = find_closest_point(cpt2)
#         if cpt is None:
#             return
#         g_plot.current_points.append(cpt)
#         if g_plot.slope_avg_mode:
#             add_point(cpt, size=RD_2, col='red')
#         else:
#             add_point(cpt, size=RD_3, col='yellow')
#
#         if len(g_plot.current_points) == 1:
#             if not g_plot.tracking_mode:
#                 print("Tracking is ON now ... ")
#                 if g_plot.slope_avg_mode:
#                     update_text('text2', 'SlopeAVG and Tracking: ON', )
#                 else:
#                     update_text('text2', 'RectMode and Tracking: ON', )
#                 update_text('text4', 'Select 2nd point on map')
#                 g_plot.tracking_mode = True
#
#         elif len(g_plot.current_points) == 2:
#             if g_plot.slope_avg_mode:
#                 g_plot.tracking_mode = False
#                 g_plot.slope_avg_mode = False
#                 update_text('text2', 'SlopeAVG: ON, Tracking: OFF')
#                 update_text('text3', '')
#                 rem_all_trackers()
#                 add_line(g_plot.current_points, width=2, col='white')
#                 max_points = int(round(dist_xyz(g_plot.current_points[0],
#                                                 g_plot.current_points[1]) / SCALE_FACTOR))
#                 plt.addSlider3D(
#                     slider_y,
#                     pos1=[g_plot.min_xyz[0] + 5,
#                           g_plot.max_xyz[1] + TEXT_SPACING,
#                           g_plot.min_xyz[2] + 5],
#                     pos2=[g_plot.max_xyz[0] - 5,
#                           g_plot.max_xyz[1] + TEXT_SPACING,
#                           g_plot.min_xyz[2] + 5],
#                     xmin=0, xmax=max_points,
#                     s=0.01, c="blue", t=1.5,
#                     title="Select a value for number of pt",
#                     showValue=False
#                 )
#                 update_text('text4', 'Select no of points on slider')
#                 update_text('text5', f'Max points = {max_points}, click anywhere on map to finish selection')
#                 all_objects['slider'] = plt.actors[-1:]
#                 g_plot.smooth_factor = 0
#                 g_plot.slider_selected = True
#             else:
#                 update_text('text4', 'Make the desired rectangle')
#         elif len(g_plot.current_points) == 3:
#             rect_points = get_rectangle(g_plot.current_points)
#             rem_all_trackers()
#             plt.remove(g_plot.plotted_points.pop())
#             plt.remove(g_plot.plotted_points.pop())
#             plt.remove(g_plot.plotted_points.pop())
#             for vertex in range(0, 4):
#                 add_point(rect_points[vertex], size=RD_4, col='Green')
#                 add_line([rect_points[vertex], rect_points[vertex - 1]], width=3, col='Yellow')
#             move_camera((rect_points[0] + rect_points[1] +
#                          rect_points[2] + rect_points[3]) / 4)
#             g_plot.rect_points = rect_points
#             update_text('text4', 'Add the first point to draw line')
#         elif len(g_plot.current_points) == 4:
#             d_sign = 0
#             xp, yp = g_plot.current_points[3][0], g_plot.current_points[3][1]
#             for vertex in range(0, 4):
#                 x2, y2 = g_plot.rect_points[vertex - 0][0], g_plot.rect_points[vertex - 0][1]
#                 x1, y1 = g_plot.rect_points[vertex - 1][0], g_plot.rect_points[vertex - 1][1]
#                 determinant = (x2 - x1) * (yp - y1) - (xp - x1) * (y2 - y1)
#                 if d_sign == 0:
#                     d_sign = determinant
#                     continue
#
#                 if (determinant > 0 > d_sign) or (d_sign > 0 > determinant):
#                     d_sign = 0
#                     break
#
#             if d_sign == 0:
#                 print(f'Point {g_plot.current_points.pop()} lies outside the rectangle, choose again')
#                 plt.remove(g_plot.plotted_points.pop())
#                 rem_all_trackers()
#             else:
#                 update_text('text4', 'Select the 2nd point within the rectangle')
#         elif len(g_plot.current_points) == 5:
#             d_sign = 0
#             xp, yp = g_plot.current_points[3][0], g_plot.current_points[3][1]
#             for vertex in range(0, 4):
#                 x2, y2 = g_plot.rect_points[vertex - 0][0], g_plot.rect_points[vertex - 0][1]
#                 x1, y1 = g_plot.rect_points[vertex - 1][0], g_plot.rect_points[vertex - 1][1]
#                 determinant = (x2 - x1) * (yp - y1) - (xp - x1) * (y2 - y1)
#                 if d_sign == 0:
#                     d_sign = determinant
#                     continue
#
#                 if (determinant > 0 > d_sign) or (d_sign > 0 > determinant):
#                     d_sign = 0
#                     break
#
#             if d_sign == 0:
#                 print(f'Point {g_plot.current_points.pop()} lies outside the rectangle, choose again')
#                 plt.remove(g_plot.plotted_points.pop())
#             else:
#                 update_text('text4', 'Calculating the point star now')
#                 rem_all_trackers()
#
#                 const_dist = 12 * 0.3048
#                 perpendicular_angle = get_angle(g_plot.rect_points[1], g_plot.rect_points[2])
#
#                 # horizontal_angle = get_angle(rect_points[0], rect_points[1])
#                 # print('Angles perpendicular = ', perpendicular_angle,
#                 #       ', horizontal = ', horizontal_angle)
#
#                 num_points = 4
#                 for p in range(0, num_points):
#                     new_center_point = (g_plot.current_points[3] * (p + 1) +
#                                         g_plot.current_points[4] * (num_points - p)) / (num_points + 1)
#                     act_center_point = find_closest_point(new_center_point)
#                     add_point(act_center_point, size=RD_4, col='Blue')
#                     point_star_structure = [{'angle': perpendicular_angle + i} for i in range(-85, 90, 5)]
#
#                     critical_angle1 = get_angle(act_center_point, g_plot.rect_points[2])
#                     critical_angle2 = get_angle(act_center_point, g_plot.rect_points[3])
#
#                     swap_index = 0
#                     if critical_angle1 > critical_angle2:
#                         swap_index = 2
#                         temp = critical_angle1
#                         critical_angle1 = critical_angle2
#                         critical_angle2 = temp
#
#                     # print('Critical angles = ', critical_angle1, critical_angle2)
#                     for i in range(0, len(point_star_structure)):
#                         new_angle = point_star_structure[i]['angle']
#                         # act_circle_point[2] += 0.2
#                         x_value = const_dist * np.math.cos(new_angle * np.pi / 180)
#                         y_value = const_dist * np.math.sin(new_angle * np.pi / 180)
#                         new_circle_point = [act_center_point[0] + x_value, act_center_point[1] + y_value,
#                                             act_center_point[2]]
#                         act_circle_point = find_closest_point(new_circle_point)
#                         if act_circle_point is None:
#                             print('Error finding the point ..')
#                             point_star_structure[i]['point'] = None
#                             continue
#
#                         if new_angle < critical_angle1:
#                             int_point = get_xy_intersection(act_circle_point, act_center_point,
#                                                             g_plot.rect_points[1 + swap_index],
#                                                             g_plot.rect_points[2 - swap_index])
#                         elif new_angle < critical_angle2:
#                             int_point = get_xy_intersection(act_circle_point, act_center_point,
#                                                             g_plot.rect_points[2],
#                                                             g_plot.rect_points[3])
#                         else:
#                             int_point = get_xy_intersection(act_circle_point, act_center_point,
#                                                             g_plot.rect_points[0 + swap_index],
#                                                             g_plot.rect_points[3 - swap_index])
#
#                         if dist_xy(act_circle_point, act_center_point) > dist_xy(int_point, act_center_point):
#                             point_star_structure[i]['point'] = int_point
#                             point_star_structure[i]['slope'] = get_slope(int_point, act_center_point)
#                             point_star_structure[i]['valid'] = False
#                         else:
#                             point_star_structure[i]['point'] = act_circle_point
#                             point_star_structure[i]['slope'] = get_slope(act_circle_point, act_center_point)
#                             point_star_structure[i]['valid'] = True
#                             # add_point(act_circle_point, size=RD_4, col='White')
#                             # add_line([act_circle_point, act_center_point], width=3, col='White')
#
#                     max_slope_index = 0
#                     max_slope_value = 0
#                     points_to_plot = []
#                     lines_to_plot = []
#
#                     for i, star_point in enumerate(point_star_structure):
#                         if star_point['valid']:
#                             points_to_plot.append(star_point['point'])
#                             lines_to_plot.append([act_center_point, star_point['point']])
#                             if abs(max_slope_value) < abs(star_point['slope']):
#                                 max_slope_index = i
#                                 max_slope_value = star_point['slope']
#                     print('Max slope at ', max_slope_index, ' val = ', point_star_structure[max_slope_index])
#                     for i, star_point in enumerate(point_star_structure):
#                         if star_point['valid']:
#                             # plt.remove(g_plot.plotted_lines.pop())
#                             # plt.remove(g_plot.plotted_points.pop())
#                             print(star_point['slope'], end=', ')
#
#                     add_point(point_star_structure[max_slope_index]['point'], size=RD_4, col='White')
#                     add_line([point_star_structure[max_slope_index]['point'], act_center_point], width=4,
#                              col='White', spread=10)
#
#                 g_plot.current_points = []
#                 g_plot.tracking_mode = False
#                 g_plot.rectangle_mode = False
#
#
# def dist_xyz(point1, point2):
#     if len(point1) != 3 or len(point2) != 3:
#         print('Bad Value of pt in dist_xyz')
#         return None
#
#     return sqrt((point1[0] - point2[0]) ** 2 +
#                 (point1[1] - point2[1]) ** 2 +
#                 (point1[2] - point2[2]) ** 2)
#
#
# def dist_xy(point1, point2):
#     if len(point1) < 2 or len(point1) < 2:
#         print('Bad Value of pt in dist_xy')
#         return None
#
#     return sqrt((point1[0] - point2[0]) ** 2 +
#                 (point1[1] - point2[1]) ** 2)
#
#
# def add_rectangle(points):
#     if len(points) < 3:
#         print('Insufficient points')
#         return
#
#
# def mouse_track(event):
#     global g_plot, g_plot
#
#     if not g_plot.tracking_mode:
#         return
#
#     # Track the mouse if a point has already been selected
#     if not event.actor:
#         # print('No actor found while tracking ... ')
#         return
#
#     mouse_point = event.picked3d
#
#     # For normal sloping related calculations #
#     # Same functionality in len(g_plot.current_points) == 1 statement
#     # if not g_plot.rectangle_mode:
#     #     for line in g_plot.plotted_trackers:
#     #         plt.remove(line)
#     #     g_plot.plotted_trackers = []
#     #     add_ruler([g_plot.current_points[0], mouse_point], width=3, col='red', size=TEXT_SIZE)
#     #     update_text('text3', f'Dist: {dist_xyz(g_plot.current_points[0], mouse_point):.3f}')
#     #     return
#
#     # For the Rectangle Mode operation #
#     if len(g_plot.current_points) == 1 or len(g_plot.current_points) == 4:
#         if len(g_plot.plotted_trackers) > 0:
#             plt.remove(g_plot.plotted_trackers.pop())
#         add_ruler([g_plot.current_points[-1], mouse_point], width=3, col='yellow', size=TEXT_SIZE)
#         update_text('text3', f'Dist: {dist_xyz(g_plot.current_points[-1], mouse_point):.3f}')
#         return
#
#     if len(g_plot.current_points) == 2:
#         rem_all_trackers()
#         rect_points = get_rectangle([g_plot.current_points[0], g_plot.current_points[1], mouse_point])
#         for i in range(0, 4):
#             add_ruler([rect_points[i], rect_points[i - 1]], width=3, col='white', size=TEXT_SIZE)
#         return
#
#
# def get_rectangle(points):
#     if len(points) != 3:
#         print('Bad input in get_rect')
#         return []
#     point_1 = np.array(points[0])
#     point_2 = np.array(points[1])
#     point_3 = np.array(points[2])
#
#     point_12 = point_1 - point_2
#     point_31 = point_3 - point_1
#     point_32 = point_3 - point_2
#
#     cosine_1 = np.dot(point_12, point_31) / (np.linalg.norm(point_12) * np.linalg.norm(point_31))
#     cosine_2 = np.dot(point_12, point_32) / (np.linalg.norm(point_12) * np.linalg.norm(point_32))
#
#     new_point_1 = point_3 - (point_12 * (dist_xyz(point_1, point_3) * cosine_1)) / dist_xyz(point_1, point_2)
#     new_point_2 = point_3 - (point_12 * (dist_xyz(point_2, point_3) * cosine_2)) / dist_xyz(point_1, point_2)
#
#     max_z = max(points[1][2], points[0][2])
#     points[1][2] = points[0][2] = new_point_1[2] = new_point_2[2] = max_z
#
#     update_text('text4', f'Angles = {cosine_1:.3f} and {cosine_2:.3f}')
#     return [points[1], points[0], new_point_1, new_point_2]
#
#
# # The get_line_of_points takes the two endpoints, then does its best to get the pt along the path of the line
# # that are on the ground of the point cloud Does this by iterating through the pt that make up the line in
# # space, then getting the closest point that is actually a part of the mesh to that point
#
#
# def add_point(pos, size=RD_1, col='red', silent=True, is_text=False):
#     global g_plot
#     new_point = Point(pos, r=size, c=col)  # Point to be added, default radius and default color
#     plt.add(new_point)
#     g_plot.plotted_points.append(new_point)
#     if is_text:
#         pos2 = [pos[0], pos[1], pos[2] + 2]
#         new_text = Text3D(txt=','.join(['%.3f' % e for e in (pos - g_plot.min_xyz)]),
#                           s=2, pos=pos2, depth=0.1, alpha=1.0, c='w')
#         plt.add([new_text])
#
#     # plt.render()
#     if not silent:
#         print(f'Added point: {pos - g_plot.min_xyz}')
#     return new_point
#
#
# def add_text(text, pos, silent=False, size=2):
#     pos[2] += 1
#     tx1 = Text3D(txt=text, s=size, pos=pos, depth=0.1, alpha=1.0)
#     plt.add([tx1])
#     # plt.render()
#     if not silent:
#         print(f'Text Rendered at {pos - g_plot.min_xyz}')
#     return tx1
#
#
# def add_line(points, col='red', width=5, silent=True, spread=1):
#     global g_plot
#     new_line = None
#     if len(points) >= 2:
#         for i in range(1, spread + 1):
#             new_line = vedo.Line([points[0][0], points[0][1], points[0][2] + i * 0.04],
#                                  [points[1][0], points[1][1], points[1][2] + i * 0.04],
#                                  lw=width, c=col, alpha=1.0)
#             plt.add([new_line])
#             g_plot.plotted_lines.append(new_line)
#             # plt.render()
#             if not silent:
#                 print(f'Added {col} line bw {points[0] - g_plot.min_xyz} and {points[1] - g_plot.min_xyz}')
#     else:
#         print('Invalid number of points')
#     return new_line
#
#
# def add_lines(points, col='yellow', width=4, silent=True):
#     if len(points) < 2:
#         print('Invalid number of pt')
#         return None
#     new_lines = []
#     # with concurrent.futures.ThreadPoolExecutor() as executor:
#     #     results = [executor.map(add_line, ([points[i - 1], points[i]], col, width, silent))
#     #                for i in range(1, len(points))]
#     for i in range(1, len(points)):
#         # threading.Thread(target=add_line, args=([points[i - 1], points[i]], col, width, silent)).start()
#         new_lines.append(add_line([points[i - 1], points[i]], col=col, width=width, silent=silent))
#     return new_lines
#
#
# def add_ruler(points, col='white', width=4, size=2):
#     global g_plot
#     if len(points) >= 2:
#         # distance = dist_xyz(points[0], points[1])
#         # line_text = ''
#         # if distance > 50:
#         #     line_text = f'{dist_xyz(points[0], points[1]):.2f}'
#         # elif distance > 25:
#         #     line_text = f'{dist_xyz(points[0], points[1]):.1f}'
#         start = [points[0][0], points[0][1], points[0][2] + 1]
#         ended = [points[1][0], points[1][1], points[1][2] + 1]
#         new_line = Ruler(start, ended, lw=width, c=col, alpha=1.0, s=size)
#         plt.add([new_line])
#         g_plot.plotted_trackers.append(new_line)
#         return new_line
#     else:
#         print('Invalid number of pt')
#
#
# def update_text(text_id, value, rel_pos=None, size=TEXT_SIZE):
#     global all_objects
#     if rel_pos is None:
#         rel_pos = [5, 5, 5]
#     if text_id in all_objects.keys():
#         plt.remove(all_objects[text_id]['text'])
#         rel_pos = all_objects[text_id]['pos']
#     new_text = add_text(value, pos=g_plot.min_xyz + rel_pos, silent=True, size=size)
#     all_objects[text_id] = {
#         'text': new_text,
#         'pos': rel_pos
#     }
#     plt.add(new_text)
#
#
# def two_point_op(points, op='SUB'):
#     if len(points) < 2:
#         return []
#
#     if op == 'SUB':
#         return [points[0][0] - points[1][0],
#                 points[0][1] - points[1][1],
#                 points[0][2] - points[1][2]]
#     if op == 'ADD':
#         return [points[1][0] + points[0][0],
#                 points[1][1] + points[0][1],
#                 points[1][2] + points[0][2]]
#
#
# def print_point(point):
#     print(','.join(['%.3f' % e for e in (point - g_plot.min_xyz)]))
#
#
# # Get the average slope of from point to point for a specified number of pt on the line
# def get_avg_slope():
#     global g_plot, max_points, cloud, all_tasks
#     update_text('text3', 'Enter num pt:')
#     if g_plot.smooth_factor >= max_points:
#         g_plot.smooth_factor = max_points - 1
#
#     if g_plot.smooth_factor == 0:
#         points_to_use = g_plot.current_points
#     else:
#         x_unit = (g_plot.current_points[1][0] - g_plot.current_points[0][0]) / (g_plot.smooth_factor + 1)
#         y_unit = (g_plot.current_points[1][1] - g_plot.current_points[0][1]) / (g_plot.smooth_factor + 1)
#         cur_point = g_plot.current_points[0]
#         z_offset = 0
#         points_to_use = []
#         bad_point_count = made_better = 0
#         acceptable_dist = 0.2
#         for i in range(0, g_plot.smooth_factor):
#             new_approx_point = [cur_point[0] + x_unit, cur_point[1] + y_unit, cur_point[2] + z_offset]
#             # add_point(new_approx_point, size=RD_4, col='white', silent=True)
#             new_actual_point = cloud.closestPoint(new_approx_point)
#             xy_dist_temp = dist_xy(new_approx_point, new_actual_point)
#             if xy_dist_temp < acceptable_dist:
#                 points_to_use.append(new_actual_point)
#                 z_offset = new_actual_point[2] - new_approx_point[2]
#             else:
#                 bad_point_count += 1
#                 new_approx_point = [cur_point[0] + (x_unit * 1.1), cur_point[1] + (y_unit * 1.1),
#                                     cur_point[2] + z_offset]
#                 new_actual_points = cloud.closestPoint(new_approx_point, radius=acceptable_dist)
#                 if len(new_actual_points) > 1:
#                     made_better += 1
#                     points_to_use.append(new_actual_points[0])
#                     z_offset = new_actual_points[0][2] - new_approx_point[2]
#             cur_point = new_approx_point
#         print('Bad points = ', bad_point_count)
#
#         if len(points_to_use) < 1:
#             print('Error in point selection. Aborting')
#             return
#         points_to_use.insert(0, g_plot.current_points[0])
#         points_to_use.append(g_plot.current_points[1])
#     # Loop through pt and plot them
#
#     update_text('text3', f'Rendering {len(points_to_use)} pt')
#     print(f'Rendering {len(points_to_use)} on map ', end='')
#     # st = '.'
#     # for p in points_to_use:
#     #     add_point(p, size=RD_3, col='g', silent=True)
#     #     update_text('text6', st)
#     #     st += '.'
#     #     print('.', end='')
#     # time.sleep(0.3)
#     print(' Done!')
#     lines_to_use = []
#     for i in range(len(points_to_use) - 1):
#         lines_to_use.append([points_to_use[i], points_to_use[i+1]])
#
#     add_timer_task(f'Add {len(points_to_use)} on map', task_type='add_point', task_data=points_to_use)
#     add_timer_task(f'Adding {len(lines_to_use)} on map', task_type='add_line', task_data=lines_to_use)
#     # point1 = ', '.join(['%.3f' % e for e in points_to_use[0]])
#     # print_text = ''
#
#     total_slope = 0
#     slopes_bw_points = []
#     for pt in range(1, len(points_to_use)):
#         # point2 = ','.join(['%.3f' % e for e in points_to_use[pt]])
#         xyz_dist = dist_xyz(points_to_use[pt - 1], points_to_use[pt - 0])
#         slope_xy = get_slope(points_to_use[pt - 1], points_to_use[pt - 0])
#         if abs(slope_xy) < 1000:
#             total_slope += slope_xy
#             slopes_bw_points.append({
#                 'X1': points_to_use[pt - 1][0],
#                 'Y1': points_to_use[pt - 1][1],
#                 'Z1': points_to_use[pt - 1][2],
#                 'X2': points_to_use[pt - 0][0],
#                 'Y2': points_to_use[pt - 0][1],
#                 'Z2': points_to_use[pt - 0][2],
#                 'Slope': slope_xy,
#                 'Distance': xyz_dist
#             })
#
#         # print_text += point1 + ', ' + point2 + '\n'
#         # point1 = point2
#
#     print_text = 'X1, Y1, Z1, X2, Y2, Z2, Slope, Distance \n'
#     print_text += '\n'.join(['%.3f, %.3f, %.3f, %.3f, %.3f, %.3f, %.3f, %.3f' %
#                              (e['X1'] - g_plot.min_xyz[0], e['Y1'] - g_plot.min_xyz[1],
#                               e['Z1'] - g_plot.min_xyz[2],
#                               e['X2'] - g_plot.min_xyz[0], e['Y2'] - g_plot.min_xyz[1],
#                               e['Z2'] - g_plot.min_xyz[2],
#                               e['Slope'], e['Distance']) for e in slopes_bw_points])
#
#     update_text('text5', 'Press z again to enter slope mode')
#     print(print_text)
#
#     # slope_2 = {
#     #     'X1': [],
#     #     'Y1': [],
#     #     'Z1': [],
#     #     'X2': [],
#     #     'Y2': [],
#     #     'Z2': [],
#     #     'Slope': []
#     # }
#     # for e in slopes_bw_points:
#     #     for key in slope_2.keys():
#     #         slope_2[key].append(e[key])
#
#     dir_name = f'Output_{datetime.now().strftime("%Y%m%d")}'
#     os.makedirs(dir_name, exist_ok=True)
#     csv_file_name = f'Slope_{datetime.now().strftime("%Y%m%d%H%M%S")}_{len(points_to_use)}_points.csv'
#     try:
#         with open(dir_name + '\\' + csv_file_name, 'w', newline='', encoding='utf-8') as csv_file:
#             writer = csv.DictWriter(csv_file, fieldnames=[e for e in slopes_bw_points[0].keys()])
#             writer.writeheader()
#             for data in slopes_bw_points:
#                 writer.writerow(data)
#     except IOError:
#         print("I/O error")
#
#     result = total_slope / len(slopes_bw_points)
#
#     # pd_slope_array.to_csv(f'calc_slope_{result}.csv')
#     print(f'Average slope between {len(points_to_use)} points = {result}, \n List of slopes for indices: ')
#     update_text('text4', f'Avg slope = {result:.3f}')
#     # print(pd_slope_array)
#     return result
#
#
# def add_timer_task(task_name, task_type, task_data, post_completion='Done'):
#
#     global all_tasks
#
#     if task_name in all_tasks.keys():
#         all_tasks[task_name]['points'].extend(task_data)
#     else:
#         all_tasks[task_name] = {
#             'points': task_data,
#             'index': 0,
#             'post': post_completion,
#             'type': type,
#             'timer_id': plt.timerCallback('create', dt=10)
#         }
#
#
# def handle_timer(event):
#     global all_tasks, g_plot
#     for key in all_tasks.keys():
#         ind = all_tasks[key]['index']
#         task_type = all_tasks[key]['type']
#         total_points = len(all_tasks[key]['points'])
#         if ind < total_points:
#             if task_type == 'add_point':
#                 add_point(all_tasks[key]['points'][ind], size=RD_3, col='g', silent=True)
#                 all_tasks[key]['index'] += 1
#                 update_text('text6', f'Added {ind + 1} out of {total_points} points')
#             elif task_type == 'add_line':
#                 add_line(all_tasks[key]['points'][ind], col='yellow', width=4, silent=True)
#                 all_tasks[key]['index'] += 1
#             else:
#                 print('Invalid task type provided')
#                 all_tasks[key]['index'] += 10000
#         else:
#             post_timer_completion(all_tasks[key]['post'])
#             timer_id = all_tasks[key]['timer']
#             plt.timerCallback('destroy', timerId=timer_id)
#             del all_tasks[key]
#
#     if g_plot.timerID is not None:
#         try:
#             q_data = g_plot.out_q.get(block=False)
#             print('Got Queue data ', q_data)
#         except Exception as e:
#             print('Got nothing')
#             q_data = e
#
#
# def reset_plot():
#     global g_plot, cloud
#     print('Removing all objects from map')
#     plt.clear()
#     plt.axes = 1
#     # plt.add([mesh, cloud]).render()
#     plt.add([cloud]).render()
#     update_text('text2', 'SlopeAVG and Tracking: OFF')
#     update_text('text3', '')
#     update_text('text4', '')
#     g_plot.initialized = False
#     g_plot.current_points = []
#     g_plot.tracking_mode = False
#
#
# # def get_list(num_elements, arr):
# #     arr_len = len(arr)
# #     return [arr[(i * arr_len // num_elements) + (arr_len // (2 * num_elements))] for i in range(num_elements)]
#
#
# def button_action(button):
#     global g_plot
#     g_plot.slope_avg_mode = (not g_plot.slope_avg_mode)
#     button.switch()  # change to next status
#
#
# def my_camera_reset():
#     plt.camera.SetPosition([2321420.115, 6926160.299, 995.694])
#     plt.camera.SetFocalPoint([2321420.115, 6926160.299, 702.312])
#     plt.camera.SetViewUp([0.0, 1.0, 0.0])
#     plt.camera.SetDistance(293.382)
#     plt.camera.SetClippingRange([218.423, 388.447])
#     # plt.render()
#     print('Camera Reset Done')
#
#
# def slider_y(widget, event):
#     global g_plot
#     value = widget.GetRepresentation().GetValue()
#     value = (value ** 1.5) / (max_points ** 0.5)
#     g_plot.smooth_factor = round(value)
#     update_text('text4', f'{round(g_plot.smooth_factor)} points selected')
#     # update_text('text5', f'Max points = {max_points}')
#
#
# def get_slope(point1, point2):
#     xy_dist = dist_xy(point1, point2)
#     zz_dist = (point2[2] - point1[2])
#     if xy_dist < 0.001:
#         print('Points selected are too close')
#         xy_dist = 0.001
#     return zz_dist / xy_dist
#
#
# def get_xy_intersection(a1, a2, b1, b2):
#     """
#     a1, a2, b1, b2: [x, y] of points in line A and line B
#     """
#     s = np.vstack([a1[0:2], a2[0:2],
#                    b1[0:2], b2[0:2]])  # s for stacked
#     h = np.hstack((s, np.ones((4, 1))))  # h for homogeneous
#     l1 = np.cross(h[0], h[1])  # get first line
#     l2 = np.cross(h[2], h[3])  # get second line
#     x, y, z = np.cross(l1, l2)  # point of intersection
#     if z == 0:  # lines are parallel
#         print('Could not find line intersection')
#         return [0.0, 0.0]
#
#     return [x / z, y / z, (a1[2] + a2[2]) / 2]
#
#
# def post_timer_completion(msg):
#     if msg == 'Done':
#         print('Done completing the required timer task')
#     else:
#         print(msg)
#
#
# def rem_all_trackers():
#     global g_plot
#     for line in g_plot.plotted_trackers:
#         plt.remove(line)
#     g_plot.plotted_trackers = []
#
#
# def move_camera(point, elevation=0):
#     global g_plot, plt
#
#     # if elevation == 0:
#     #     elevation = g_plot.cam_center[2]
#     # new_cam_pos = [point[0], point[1], elevation]
#     # focal_pos = point
#     # new_cam = dict(pos=new_cam_pos,
#     #                focalPoint=focal_pos,
#     #                viewup=(0, 1.00, 0),
#     #                clippingRange=(218.423, 388.447)
#     #                )
#     plt.flyTo(point)
#     # plt.show(g_plot.show_ele_list, interactorStyle=0, bg='white', axes=1, zoom=1.0, interactive=True, camera=new_cam)
#
#
# def get_file_names():
#     tk.Tk().withdraw()
#     if len(sys.argv) < 2:
#         print('No PLY file specified: opening prompt')
#         # file_1 = filedialog.askopenfilename(initialdir=os.getcwd(), title="Select the PLY File",
#         #                                     filetypes=[('Point-cloud file', ('.ply', '.pcd'))])
#         file_1 = 't3.ply'
#     else:
#         file_1 = sys.argv[1]
#
#     if len(sys.argv) < 3:
#         print('No Image file specified: opening prompt')
#         # file_2 = filedialog.askopenfilename(initialdir=os.getcwd(), title="Select the Image File",
#         #                                     filetypes=[('Image Files', ('.png', '.jpg'))])
#         file_2 = '3_1.png'
#     else:
#         file_2 = sys.argv[2]
#
#     if not os.path.isfile(file_1):
#         print('Invalid file path: ', file_1, ' Not found!')
#         exit(1)
#
#     if not os.path.isfile(file_2):
#         print('Invalid file path: ', file_1, ' Not found!')
#         exit(1)
#
#     return [file_1, file_2]
#
#
# def toggle_state(queue_obj: multiprocessing.Queue, value):
#     d = {
#         'time': time.time(),
#         'value': value
#     }
#     queue_obj.put(d)
#     print(queue_obj.qsize())
#
#
# def gui_main(inp_q: multiprocessing.Queue, out_q: multiprocessing.Queue):
#     root = tk.Tk()
#     root.geometry('400x300')
#     root.title('Main menu')
#
#     label = tk.Label(root, text="Enter a value ", borderwidth=2, font=10)
#
#     text = tk.StringVar()
#     entry = tk.Entry(root, textvariable=text)
#     # e.bind('<Key>', key_press)
#
#     button_1 = tk.Button(root, text="Enter Slope AVG Mode", command=lambda: toggle_state(out_q, entry.get()))
#
#     label.pack()
#     entry.pack()
#     button_1.pack()
#     root.mainloop()
#
#
# settings.enableDefaultKeyboardCallbacks = False
# plt = Plotter(pos=[0, 0], size=[600, 1080])
# temp_file = open('temp_file', mode='w+')
# temp_file.close()
# cloud = load('temp_file')
#
#
# def plt_main(inp_q, out_q):
#     global cloud, plt, g_plot
#
#     print(f'Program started :')
#
#     [filename, pic_name] = get_file_names()
#     print(f'Selected PLY file: {filename} and picture: {pic_name}')
#
#     ################################################################################################
#     st = time.time()
#     cloud = load(filename).pointSize(4.0)
#     print(f'Loaded cloud {filename} in {time.time() - st} sec')
#
#     st = time.time()
#     pic = Picture(pic_name)
#     print(f'Loaded picture {pic_name} in {time.time() - st} sec')
#
#     g_plot.min_xyz = np.min(cloud.points(), axis=0)
#     g_plot.max_xyz = np.max(cloud.points(), axis=0)
#     print(g_plot.max_xyz - g_plot.min_xyz)
#     g_plot.inp_q = inp_q
#     g_plot.out_q = out_q
#
#     # st = time.time()
#     # new_mesh = delaunay2D(cloud.points()).alpha(0.3).c('grey')  # Some new_mesh object with low alpha
#     dim = pic.dimensions()
#     range_xyz = g_plot.max_xyz - g_plot.min_xyz
#     scale_fact = [range_xyz[0] / dim[0], range_xyz[1] / dim[1], 1]
#     pic = pic.scale(scale_fact).pos(g_plot.min_xyz[0] - 1, g_plot.min_xyz[1] + 0.2,
#                                     g_plot.min_xyz[2]).rotateZ(2)
#     # print(f'Mesh created in {time.time() - st} sec for {len(cloud.points())} points')
#
#     plt.addCallback('KeyPress', on_key_press)
#     plt.addCallback('LeftButtonPress', on_left_click)
#     plt.addCallback('MouseMove', mouse_track)
#     plt.addCallback('timer', handle_timer)
#     plt.addCallback('Enter', enter_callback)
#     plt.addCallback('Leave', leave_callback)
#     print('Once the program launches, Use the following keymap:'
#           '\n\t \'z\'   for Slope mode'
#           '\n\t \'r\'   for Rectangle Mode'
#           '\n\t \'c\'   for Clearing everything'
#           '\n\t \'u\'   for Resetting the plot'
#           '\n\t \'Esc\' to Close everything')
#
#     st = time.time()
#     g_plot.cloud_center = cloud.centerOfMass()  # Center of mass for the whole cloud
#     print(f'Center of mass = {g_plot.cloud_center}, calc in {time.time() - st} sec')
#     g_plot.cam_center = [g_plot.cloud_center[0], g_plot.cloud_center[1], g_plot.cloud_center[2] + 150]
#     g_plot.show_ele_list = [cloud, pic]
#     cam = dict(pos=g_plot.cam_center,
#                focalPoint=g_plot.cloud_center,
#                viewup=(0, 1.00, 0),
#                clippingRange=(218.423, 388.447)
#                )
#     plt.show(g_plot.show_ele_list, interactorStyle=0, bg='white', axes=1, zoom=1.0, interactive=True,
#              camera=cam)
#
#
# def key_press(event):
#     global g_plot
#     g_plot.last_key_press = event.char
#     print(event)
#
#
# def find_closest_point(point, num_retry=25, dist_threshold=1.5):
#     fact = 1.0
#     for rt in range(0, num_retry):
#         # rand_point = [(xyz + (random.random() - 0.5)*fact) for xyz in point]
#         rand_point = [point[0], point[1], point[2] - (random.random() - 0.3) * fact]
#         close_point = cloud.closestPoint(rand_point)
#         fact *= 1.08
#         if dist_xy(close_point, rand_point) < dist_threshold:
#             return close_point
#
#     print('Failed to find a close point for ', point)
#     return None
#
#
# def get_angle(point1, point2):
#     yy_diff = point2[1] - point1[1]
#     xx_diff = point2[0] - point1[0]
#     angle_measure = np.math.acos(xx_diff / dist_xy(point1, point2)) * (180 / np.pi)
#     if yy_diff < 0:
#         return 360 - angle_measure
#     else:
#         return angle_measure
#     # return angle_measure
#
#
# class LocalPlotter:
#     slope_avg_mode = False
#     tracking_mode = False
#     rectangle_mode = False
#     slider_selected = False
#     initialized = False
#     min_xyz: []
#     max_xyz: []
#     cloud_center: []
#     cam_center: []
#     last_key_press = None
#     smooth_factor = 0
#     temp_dict: {}
#     inp_q: multiprocessing.Queue
#     out_q: multiprocessing.Queue
#     timerID = None
#     current_points = []
#     plotted_trackers = []
#     plotted_points = []
#     plotted_lines = []
#     rect_points = []
#     show_ele_list = []
#
#
# ''' All the global variables declared '''
# g_plot = LocalPlotter()
# max_points = 0
# all_objects = {
# }
# all_tasks = {
# }
# ''' End of variable declarations '''
#
#
# ################################################################################################
# ############################## MAIN LIKE SECTION ###############################################
#
# # gui_thread = threading.Thread(target=gui_main)
# # print('Starting the GUI Thread')
# # gui_thread.start()
#
# # plotter_thread = threading.Thread(target=plotter_main)
# # print('Starting plotter thread')
# # plotter_thread.start()
#
# ################################################################################################
#
#
# def main():
#     inp_q = multiprocessing.Queue()
#     out_q = multiprocessing.Queue()
#
#     plt_process = multiprocessing.Process(target=plt_main, args=(inp_q, out_q))
#     plt_process.start()
#
#     # gui_process = multiprocessing.Process(target=gui_main, args=(inp_q, out_q))
#     # gui_process.start()
#     # gui_process.join()
#     plt_process.join()
#
#
# if __name__ == '__main__':
#     main()
#     exit()
