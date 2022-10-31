# import random
#
# import vedo
# import math
# import numpy as np
#
#
# def dist_xyz(point1, point2):
#     if len(point1) != 3 or len(point2) != 3:
#         print('Bad Value of pt in dist_xyz')
#         return None
#
#     return math.sqrt((point1[0] - point2[0]) ** 2 +
#                      (point1[1] - point2[1]) ** 2 +
#                      (point1[2] - point2[2]) ** 2)
#
#
# def dist_xy(point1, point2):
#     if len(point1) < 2 or len(point1) < 2:
#         print('Bad Value of pt in dist_xy')
#         return None
#
#     return math.sqrt((point1[0] - point2[0]) ** 2 +
#                      (point1[1] - point2[1]) ** 2)
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
#     if op == 'AVG':
#         return [(points[1][0] + points[0][0]) / 2.0,
#                 (points[1][1] + points[0][1]) / 2.0,
#                 (points[1][2] + points[0][2]) / 2.0]
#
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
# def on_left_click(event):
#     global cloud
#     if event.picked3d is None:
#         return
#     cpt2 = vedo.vector(list(event.picked3d))
#     cpt = cloud.closestPoint(cpt2)
#     com = vedo.Point(cpt)
#     veh_l = 7.0
#     veh_w = 3.0
#     veh_h = 0.2
#     whl_r = 0.6
#     whl_h = 0.3
#
#     whl_center = [[cpt[0] - veh_l/3.6, cpt[1] - veh_w/2.0, cpt[2] + whl_r],     # left, bottom
#                   [cpt[0] + veh_l/3.6, cpt[1] - veh_w/2.0, cpt[2] + whl_r],     # right, bottom
#                   [cpt[0] - veh_l/3.6, cpt[1] + veh_w/2.0, cpt[2] + whl_r],     # left, top
#                   [cpt[0] + veh_l/3.6, cpt[1] + veh_w/2.0, cpt[2] + whl_r]]     # right, top
#
#     whl_bottoms = [[whl_center[i][0], whl_center[i][1], whl_center[i][2] + whl_r] for i in range(0, 4)]
#
#     ''' Wheel bottom rectangle mesh '''
#     wheel_bottom_mesh = vedo.Mesh([whl_bottoms, [(0, 1, 2), (1, 2, 3)]])
#     wheel_bottom_mesh.backColor('orange4').color('orange').lineColor('black').lineWidth(1)
#     plt.add(wheel_bottom_mesh)
#     plt.render()
#     print(wheel_bottom_mesh.points())
#
#     for i in range(1, 10):
#         wheel_bottom_mesh.rotate(15, [0, 0, 1], whl_bottoms[0])
#         plt.render()
#         print(wheel_bottom_mesh.points())
#
# filename = '../t3.ply'
# # cloud = vedo.load(vedo.dataurl+"porsche.ply")
# cloud = vedo.load(filename)
# print('Done cloud load')
# min_xyz = np.min(cloud.points(), axis=0)
# max_xyz = np.max(cloud.points(), axis=0)
# range_xyz = max_xyz - min_xyz
# print(range_xyz)
# # settings.useParallelProjection = True
# plt = vedo.Plotter(pos=[0, 0], size=[800, 1080])
# plt.addCallback('RightButtonPress', on_left_click)
#
# cloud_center = cloud.centerOfMass()
# cam = dict(pos=(cloud_center[0], cloud_center[1], cloud_center[2] + 200),
#            focalPoint=cloud_center,
#            viewup=(0, 1.00, 0),
#            clippingRange=(218.423, 388.447)
#            )
# plt.show([cloud], interactorStyle=0, bg='white', axes=1, zoom=1.0,
#          interactive=True, camera=cam)
