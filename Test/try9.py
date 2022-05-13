import random

import vedo
import math
import numpy as np


def dist_xyz(point1, point2):
    if len(point1) != 3 or len(point2) != 3:
        print('Bad Value of pt in dist_xyz')
        return None

    return math.sqrt((point1[0] - point2[0]) ** 2 +
                     (point1[1] - point2[1]) ** 2 +
                     (point1[2] - point2[2]) ** 2)


def dist_xy(point1, point2):
    if len(point1) < 2 or len(point1) < 2:
        print('Bad Value of pt in dist_xy')
        return None

    return math.sqrt((point1[0] - point2[0]) ** 2 +
                     (point1[1] - point2[1]) ** 2)


def two_point_op(points, op='SUB'):
    if len(points) < 2:
        return []

    if op == 'SUB':
        return [points[0][0] - points[1][0],
                points[0][1] - points[1][1],
                points[0][2] - points[1][2]]
    if op == 'ADD':
        return [points[1][0] + points[0][0],
                points[1][1] + points[0][1],
                points[1][2] + points[0][2]]
    if op == 'AVG':
        return [(points[1][0] + points[0][0]) / 2.0,
                (points[1][1] + points[0][1]) / 2.0,
                (points[1][2] + points[0][2]) / 2.0]



def find_closest_point(point, num_retry=25, dist_threshold=1.5):
    fact = 1.0
    for rt in range(0, num_retry):
        # rand_point = [(xyz + (random.random() - 0.5)*fact) for xyz in point]
        rand_point = [point[0], point[1], point[2] - (random.random() - 0.3) * fact]
        close_point = cloud.closestPoint(rand_point)
        fact *= 1.08
        if dist_xy(close_point, rand_point) < dist_threshold:
            return close_point

    print('Failed to find a close point for ', point)
    return None


def on_left_click(event):
    global cloud
    if event.picked3d is None:
        return
    cpt2 = vedo.vector(list(event.picked3d))
    cpt = cloud.closestPoint(cpt2)
    com = vedo.Point(cpt)
    veh_l = 7.0
    veh_w = 3.0
    veh_h = 0.2
    whl_r = 0.6
    whl_h = 0.3

    whl_center = [[cpt[0] - veh_l/3.6, cpt[1] - veh_w/2.0, cpt[2] + whl_r],     # left, bottom
                  [cpt[0] + veh_l/3.6, cpt[1] - veh_w/2.0, cpt[2] + whl_r],     # right, bottom
                  [cpt[0] - veh_l/3.6, cpt[1] + veh_w/2.0, cpt[2] + whl_r],     # left, top
                  [cpt[0] + veh_l/3.6, cpt[1] + veh_w/2.0, cpt[2] + whl_r]]     # right, top

    box_bottom = [[cpt[0] - veh_l / 2.0, cpt[1] - veh_w / 2.0, cpt[2] + whl_r - veh_h/2.0],
                  [cpt[0] + veh_l / 2.0, cpt[1] - veh_w / 2.0, cpt[2] + whl_r - veh_h/2.0],
                  [cpt[0] - veh_l / 2.0, cpt[1] + veh_w / 2.0, cpt[2] + whl_r - veh_h/2.0],
                  [cpt[0] + veh_l / 2.0, cpt[1] + veh_w / 2.0, cpt[2] + whl_r - veh_h/2.0]]

    whl_bottom = [[whl_center[i][0], whl_center[i][1], whl_center[i][2] - whl_r] for i in range(0, 4)]
    whl_bottom_fix = []
    for i in range(0, 4):
        whl_bottom_fix.append(find_closest_point(whl_bottom[i], num_retry=30, dist_threshold=0.1))
        print(whl_center[i][2] - whl_bottom_fix[i][2])

    pair_points = [
        [0, 1, 2],
        [1, 0, 3],
        [2, 0, 3],
        [3, 1, 2]]

    cen_bottom = two_point_op([whl_bottom[0], whl_bottom[3]], op='AVG')

    whl_object = [vedo.Cylinder(whl_center[i], r=whl_r, height=whl_h, axis=(0, 1, 0),
                                alpha=0.6).triangulate().c('purple') for i in range(0, 4)]

    ln_obj = [vedo.Line(whl_center[0], whl_center[3], closed=True, c='red', alpha=0.3),
              vedo.Line(whl_center[2], whl_center[1], closed=True, c='red', alpha=0.3)]

    box = vedo.Box([cpt[0], cpt[1], cpt[2] + whl_r], length=veh_l, width=veh_w, height=veh_h,
                   alpha=0.4).triangulate().c('pink')

    print('Made mesh')
    mesh_rad = 1.0
    con = []
    mesh = []
    for i, pt in enumerate(box_bottom):
        close_pt = cloud.closestPoint(pt, radius=mesh_rad)
        if len(close_pt) > 2:
            mesh_i = vedo.delaunay2D(close_pt)
            mesh_i.c('hotpink')
            con_i = mesh_i.intersectWith(box)
            con.append(con_i)
            mesh.append(mesh_i)
            print(len(con_i.points()))

    print('Cons = ', con)
    veh_obj = [com, box]
    veh_obj.extend(whl_object)
    veh_obj.extend(ln_obj)
    veh_obj.extend(mesh)
    veh_obj.extend(con)
    plt.add(veh_obj)

    # rot = 4
    # for i in range(0, 40):
    #     box.rotate(angle=rot, point=cpt, axis=(0, 0, 1))
    #     for j in range(0, 4):
    #         whl_object[j].rotate(angle=rot, point=whl_center[j], axis=(0, 0, 1))
    #     for j in range(0, 2):
    #         ln_obj[j].rotate(angle=rot, point=cpt, axis=(0, 0, 1))
    #     whl_center[3], whl_center[0] = ln_obj[0].points()
    #     whl_center[2], whl_center[1] = ln_obj[1].points()
    #
    #     for j in range(0, 4):
    #         whl_object[j].pos(whl_center[j])
    #     plt.render()


filename = '../t3.ply'
# cloud = vedo.load(vedo.dataurl+"porsche.ply")
cloud = vedo.load(filename)
print('Done cloud load')
min_xyz = np.min(cloud.points(), axis=0)
max_xyz = np.max(cloud.points(), axis=0)
range_xyz = max_xyz - min_xyz
print(range_xyz)
# settings.useParallelProjection = True
plt = vedo.Plotter(pos=[0, 0], size=[800, 1080])
plt.addCallback('RightButtonPress', on_left_click)

cloud_center = cloud.centerOfMass()
cam = dict(pos=(cloud_center[0], cloud_center[1], cloud_center[2] + 200),
           focalPoint=cloud_center,
           viewup=(0, 1.00, 0),
           clippingRange=(218.423, 388.447)
           )
plt.show([cloud], interactorStyle=0, bg='white', axes=1, zoom=1.0,
         interactive=True, camera=cam)
