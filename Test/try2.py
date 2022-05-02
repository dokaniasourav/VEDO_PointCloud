# from vedo import *
# import numpy as np
# from datetime import datetime
# from pandas import DataFrame
# import math
# import sys
# import time
# import csv
#
# points = []
# line = None
#
#
# def on_left_click(event):
#     global points
#     if event.picked3d is not None:
#         print(event.picked3d)
#         cpt = vector(list(event.picked3d))
#         new_point = Point(cpt, r=10, c='w')  # Point to be added, default radius and default color
#         plt.add([new_point])
#         if len(points) == 0:
#             update_text('text1', 'A', [2, -15, 5])
#             update_text('text2', 'B', [2, -10, 5])
#             update_text('text3', 'C', [2, -20, 5])
#             points.append(cpt)
#             points.append(cpt)
#             print('Added new points')
#         else:
#             points = []
#             print('Reset points')
#
#
# def mouse_track(event):
#     global line, points
#     if event.picked3d is not None:
#         if len(points) > 0:
#             points[0] = vector(list(event.picked3d))
#             new_point1 = cloud.closestPoint(points[0])
#             new_point2 = cloud.closestPoint(points[0], radius=1)
#             update_text('text1', f'D1 = {dist_xyz(points[0], new_point1)}')
#             if len(new_point2) > 1:
#                 update_text('text2', f'D2 = {dist_xyz(points[0], new_point2[0])}')
#             else:
#                 update_text('text2', f'NA')
#
#             # points[1] = vector(list(event.picked3d))
#             # if line is not None:
#             #     plt.remove(line)
#             # line = add_line(points)
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
# def on_key_press(event):
#     printc(f'{event.keyPressed} pressed: ')
#     # c = input('Enter something ')
#
#
# def add_line(pt, col='red', width=5, silent=False):
#     new_line = None
#     if len(pt) >= 2:
#         new_line = Ruler(pt[0], pt[1], lw=width, c=col, alpha=1.0)
#         plt.add([new_line])
#         print(f'Added line bw {pt[0]} and {pt[1]}')
#         plt.render()
#     else:
#         print('Invalid number of pt')
#     return new_line
#
#
# def update_text(text_id, value, rel_pos=None, size=3):
#     global text_objects
#     if rel_pos is None:
#         rel_pos = [5, 5, 5]
#     if text_id in text_objects.keys():
#         plt.remove(text_objects[text_id]['text'])
#         rel_pos = text_objects[text_id]['pos']
#     new_text = add_text(value, pos=min_xyz + rel_pos, silent=True, size=size)
#     text_objects[text_id] = {
#         'text': new_text,
#         'pos': rel_pos
#     }
#     plt.add(new_text)
#
#
# def add_text(text, pos, silent=False, size=2):
#     pos[2] += 1
#     tx1 = Text3D(txt=text, s=size, pos=pos, depth=0.1, alpha=1.0)
#     plt.add([tx1])
#     # plt.render()
#     if not silent:
#         print(f'Text Rendered at {pos - min_xyz}')
#     return tx1
#
#
# text_objects = {
# }
# print(f'Program started :')
# start_time = time.time()
#
# if len(sys.argv) < 2:
#     filename = 'Hump_1.ply'
# else:
#     filename = sys.argv[1]
#
# cloud = load(filename).pointSize(3.5)
# print(f'Loaded file {filename} in {time.time() - start_time} seconds')
#
# start_time = time.time()
# cloud_center = cloud.centerOfMass()  # Center of mass for the whole cloud
#
# print(f'Center of mass = {cloud_center}, calc in {time.time() - start_time} sec')
#
# min_xyz = np.min(cloud.points(), axis=0)
# max_xyz = np.max(cloud.points(), axis=0)
# dif_xyz = np.subtract(cloud.points(), min_xyz)
#
# cloud.legend('My cloud map')
# start_time = time.time()
# mesh = delaunay2D(cloud.points()).alpha(0.3).c('grey')  # Some mesh object with low alpha
# print(f'Mesh created in {time.time() - start_time} sec for {len(cloud.points())} pt')
#
# cloud_center_1 = (cloud_center[0], cloud_center[1], cloud_center[2] + 450)
# # cloud_center_2 = [cloud_center[0], cloud_center[1], cloud_center[2]+50]
# cam = dict(pos=cloud_center_1,
#            focalPoint=cloud_center,
#            viewup=(0, 1.00, 0),
#            # distance=293.382,
#            clippingRange=(218.423, 388.447))
#
# plt = Plotter(pos=[0, 0], size=[500, 1080])
# plt.addCallback('KeyPress', on_key_press)
# plt.addCallback('LeftButtonPress', on_left_click)
# plt.addCallback('MouseMove', mouse_track)
# plt.show([mesh, cloud], interactorStyle=0, bg='white', axes=1, zoom=1.5, interactive=True)  # , camera=cam)
# exit()
#
# # interactive()
# # print('Finished execution')
