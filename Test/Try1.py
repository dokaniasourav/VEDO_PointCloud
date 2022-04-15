# from vedo import *
# import numpy as np
# import pandas as pd
# import math
# import sys
#
#
#
# def key_func(event):
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
#         struct = None
#         tracking_mode = False
#         connected_box_points_side1 = []
#         connected_box_points_side2 = []
#
#     # elif event.keyPressed == 's':
#     #     with open(outfl, 'w') as f:
#     #         # uncomment the second line to save the line instead (with 100 pts)
#     #         f.write(str(vector(two_points)[:,(0,1)])+'\n')
#     #         printc("\nCoordinates saved to file:", outfl, c='y', invert=1)
#
#     elif event.keyPressed == "t":
#         print("CAMERA RESET")
#         my_camera_reset()
#
#     printc('key press:', event.keyPressed)
#
#
# cloud = load(sys.argv[1]).pointSize(3.5)
# cloud_center = cloud.centerOfMass()
# print("CLOUD CENTER = " + str(cloud_center))
# z_center = cloud_center[2]
# mesh = delaunay2D(cloud.points()).alpha(0.1).c("white")
#
# cam = dict(pos=cloud_center,
#            focalPoint=(2321420.115, 6926160.299, 702.312),
#            viewup=(0, 1.00, 0),
#            distance=293.382,
#            clippingRange=(218.423, 388.447))
#
# plt = Plotter()
# plt.addCallback('KeyPress', key_func)
# plt.addCallback('LeftButtonPress', onLeftClick)
# # plt.addCallback('RightButtonPress', onRightClick)
# plt.addCallback('MouseMove', mouseTrack)
# print("Once the program launches, press 'h' for list of default commands")
# plt.show([mesh, cloud], interactorStyle=0, bg='white', axes=1)  # , camera = cam)
# interactive()
