import os
import sys
import csv
import time
from pprint import pprint

import vedo
import copy
import random
import tkinter
import numpy as np
import multiprocessing
import tkinter.filedialog
import tkinter.simpledialog
from datetime import datetime

import Global as Glb
import Helper as HpF
import Interface as Intf

# from tkinter import filedialog

# import dill
# import concurrent.futures
# import threading


'''Script for plotting and finding average slope of points along a path: 

1. Firstly, click on the map to initialize it
2. Enter 'z' or 'Z' to enter slope avg mode
3. You can now see instructions in map as well. 
   Select any two points and use the slider to provide the number of points required 
4. You will be asked how many pt you will want to contribute to the average 
   slope, and you can specify an number less than the number of available pt, or select all 
5. CSV file will be created with the slope values
'''


# Constantly checking if any meaningful key is selected
def on_key_press(event):
    global plt, g_plot
    g_plot.last_key_press = event.keyPressed
    if event.keyPressed in ['c', 'C']:
        for point in g_plot.plotted_points:
            plt.remove(point, render=True)
        for t_line in g_plot.plotted_trackers:
            plt.remove(t_line, render=True)
        for p_line in g_plot.plotted_lines:
            plt.remove(p_line, render=True)
        plt.sliders = g_plot.current_points = []
        g_plot.plotted_points = g_plot.plotted_lines = g_plot.plotted_trackers = []
        print('==== Cleared all points on the plot ====')
        for i in range(1, 6):
            update_text(f'text{i}', '')
        update_text('text4', 'Cleared everything on the plot')
        update_text('text5', 'Press R to enter rectangle mode')
        update_text('text6', 'Press Z to enter slope mode')
        g_plot.plotter_mode = Glb.IDEAL_PLT_MODE
    elif event.keyPressed == 'Escape':
        plt.clear()
        exit()
    elif event.keyPressed in ['u', 'U']:
        reset_plot()
    elif event.keyPressed == 't':
        my_camera_reset()
    elif g_plot.plotter_mode == Glb.IDEAL_PLT_MODE:
        if event.keyPressed in ['z', 'Z']:
            print("=== ENTER SLOPE AVG MODE ====")
            update_text('text5', 'Slope averaging is ON')
            g_plot.plotter_mode = Glb.SLOPE_AVG_MODE
        elif event.keyPressed in ['R', 'r']:
            print("=== ENTER RECTANGLE MODE ====")
            update_text('text5', 'Rectangle mode is ON')
            g_plot.plotter_mode = Glb.RECTANGLE_MODE
        elif event.keyPressed in ['V', 'v']:
            print("=== ENTER VEHICLE MODE ====")
            update_text('text5', 'Vehicle mode is ON')
            g_plot.plotter_mode = Glb.VEHICLE_RUNNER

    # elif event.keyPressed in [str(e) for e in range(0, 9)]:
    #     handle_inp()


def enter_callback(event):
    global g_plot
    if not g_plot.initialized:
        update_text('text1', '', [2, -2 * Glb.TEXT_SPACING, 5])
        update_text('text2', 'SlopeAVG and Tracking: OFF', [2, -3 * Glb.TEXT_SPACING, 5])
        update_text('text3', '', [2, -4 * Glb.TEXT_SPACING, 5])
        update_text('text4', 'Press Z to enter slope mode',
                    [3, g_plot.max_xyz[1] - g_plot.min_xyz[1] + 3 * Glb.TEXT_SPACING, 5])
        update_text('text5', 'Press R to enter slope mode',
                    [3, g_plot.max_xyz[1] - g_plot.min_xyz[1] + 2 * Glb.TEXT_SPACING, 5])
        update_text('text6', '', [3, g_plot.max_xyz[1] - g_plot.min_xyz[1] + 1 * Glb.TEXT_SPACING, 5])
        # all_tasks['timer_id'] = plt.timerCallback('create', dt=10)
        g_plot.initialized = True
    if g_plot.timerID is not None:
        plt.timerCallback('destroy', timerId=g_plot.timerID)
        g_plot.timerID = None


def leave_callback(event):
    global g_plot, all_tasks
    # if 'timer_id' in all_tasks.keys():
    #     return
    # if g_plot.timerID is None:
    #     g_plot.timerID = plt.timerCallback('create', dt=500)


def handle_timer(event):
    global all_tasks, g_plot
    done_keys = []
    for task_name in all_tasks.keys():
        ind = all_tasks[task_name]['index']
        task_type = all_tasks[task_name]['type']
        metadata = all_tasks[task_name]['meta']
        task_data = all_tasks[task_name]['data']
        if ind < len(task_data):
            if task_type == 'add_point':
                metadata['pos'] = task_data[ind]
                # add_point(task_data[ind], size=Glb.RD_3, col='g', silent=True)
                add_point(**metadata)
                all_tasks[task_name]['index'] += 1
            elif task_type == 'add_line':
                metadata['points'] = task_data[ind]
                add_line(**metadata)
                all_tasks[task_name]['index'] += 1
            else:
                print('Invalid task type provided')
                all_tasks[task_name]['index'] += 10000
        else:
            done_keys.append(task_name)

    for done_key in done_keys:
        post_timer_completion(all_tasks[done_key])
        timer_id = all_tasks[done_key]['timer']
        plt.timerCallback('destroy', timerId=timer_id)
        del all_tasks[done_key]

    if g_plot.timerID is not None:
        try:
            q_data = g_plot.out_q.get(block=False)
            print('Got Queue data ', q_data)
        except Exception as e:
            print('Got nothing')
            q_data = e


def post_timer_completion(task_data):
    msg = task_data['post']
    task_name = task_data['name']
    print(f'Timer task {task_name} completed, msg = {msg}')


def add_timer_task(task_name, task_type, task_data, meta=None, post_completion='Done'):
    global all_tasks

    if task_name in all_tasks.keys():
        all_tasks[task_name]['data'].extend(task_data)
    else:
        if meta is None:
            meta = {}
        all_tasks[task_name] = {
            'name': task_name,
            'data': task_data,
            'index': 0,
            'post': post_completion,
            'type': task_type,
            'timer': plt.timerCallback('create', dt=10),
            'meta': meta
        }


def on_right_click(event):
    if event.picked3d is None:
        return
    cpt2 = vedo.vector(list(event.picked3d))
    cpt = find_closest_point(cpt2)
    if cpt is None:
        return
    move_camera(cpt)


def on_left_click(event):
    global g_plot, cloud
    # global max_points

    if event.picked3d is None:
        return

    if g_plot.plotter_mode != Glb.IDEAL_PLT_MODE:
        cpt2 = vedo.vector(list(event.picked3d))
        cpt = find_closest_point(cpt2)
        if cpt is None:
            return
        if g_plot.plotter_mode == Glb.SLOPE_AVG_MODE:
            add_point(cpt, size=Glb.RD_2, col='red')
            g_plot.current_points.append(cpt)
        elif g_plot.plotter_mode == Glb.RECTANGLE_MODE:
            add_point(cpt, size=Glb.RD_3, col='yellow')
            g_plot.current_points.append(cpt)
        elif g_plot.plotter_mode == Glb.VEHICLE_RUNNER:
            ## Getting the attributes of the vehicle using a separate function
            print('Click to add a starting position for Vehicle')
            new_window = multiprocessing.Process(target=Intf.get_vehicle_data, args=(g_plot.out_q,))
            new_window.start()
            new_window.join()
            if not g_plot.out_q.empty():
                g_plot.vehicle_data = g_plot.out_q.get()

            ## Temporary point for representation of the clicked point
            add_point(cpt, size=Glb.RD_3, col='hotpink')
            g_plot.plotter_mode = Glb.IDEAL_PLT_MODE
            g_plot.vehicle_data.height = g_plot.vehicle_data.wheel_radius / 2
            g_plot.vehicle_data.position = [cpt[0], cpt[1], (cpt[2] + g_plot.vehicle_data.wheel_radius)]

            veh_l = g_plot.vehicle_data.length
            veh_f = g_plot.vehicle_data.front_overhang
            veh_b = g_plot.vehicle_data.back_overhang
            veh_w = g_plot.vehicle_data.width
            veh_h = g_plot.vehicle_data.height
            whl_r = g_plot.vehicle_data.wheel_radius
            whl_h = g_plot.vehicle_data.wheel_width

            veh_x = g_plot.vehicle_data.position[0]
            veh_y = g_plot.vehicle_data.position[1]
            veh_z = g_plot.vehicle_data.position[2] + 2

            ## Ignoring the wheel width effect for now
            whl_bottoms = [[veh_x - veh_l / 2.0, veh_y - veh_w / 2.0, veh_z - whl_r],  # left, bottom
                           [veh_x + veh_l / 2.0, veh_y - veh_w / 2.0, veh_z - whl_r],  # right, bottom
                           [veh_x - veh_l / 2.0, veh_y + veh_w / 2.0, veh_z - whl_r],  # left, top
                           [veh_x + veh_l / 2.0, veh_y + veh_w / 2.0, veh_z - whl_r]]  # right, top

            ## Ignoring the wheel width effect for now
            whl_centers = [[veh_x - veh_l / 2.0, veh_y - veh_w / 2.0, veh_z],  # left, bottom
                           [veh_x + veh_l / 2.0, veh_y - veh_w / 2.0, veh_z],  # right, bottom
                           [veh_x - veh_l / 2.0, veh_y + veh_w / 2.0, veh_z],  # left, top
                           [veh_x + veh_l / 2.0, veh_y + veh_w / 2.0, veh_z]]  # right, top

            whl_points = []
            connections = []
            box_coord = []
            bottom_x_adj = [-veh_b, veh_f, -veh_b, veh_f]
            for i in range(0, 4):
                box_coord.append([whl_centers[i][0] + bottom_x_adj[i],
                                  whl_centers[i][1], whl_centers[i][2] - veh_h / 2.0])

            for i in range(0, 4):
                box_coord.append([whl_centers[i][0] + bottom_x_adj[i],
                                  whl_centers[i][1], whl_centers[i][2] + veh_h / 2.0])

            num_pts = 60
            for wi, whl_center in enumerate(whl_centers):
                side_angle = 0  # np.pi / 4
                add_point(whl_center, custom_text=f'{wi}_wheel', size=Glb.RD_3, col='hotpink')
                whl_y_off = [-whl_h, -whl_h, whl_h, whl_h]
                for i in range(0, num_pts):
                    ang = 360 / num_pts * i * np.pi / 180
                    whl_rim_point_1 = [whl_center[0] + whl_r * np.math.cos(ang) * np.math.cos(side_angle),
                                       whl_center[1] + whl_r * np.math.cos(ang) * np.math.sin(side_angle),
                                       whl_center[2] + whl_r * np.math.sin(ang)]
                    whl_rim_point_2 = [whl_center[0] + whl_r * np.math.cos(ang) * np.math.cos(side_angle),
                                       whl_center[1] + whl_r * np.math.cos(ang) * np.math.sin(side_angle) + whl_y_off[
                                           wi],
                                       whl_center[2] + whl_r * np.math.sin(ang)]
                    whl_points.append(whl_rim_point_1)
                    whl_points.append(whl_rim_point_2)
                    connections.append([(i * 2 + 0) % (num_pts * 2) + wi * num_pts * 2,
                                        (i * 2 + 1) % (num_pts * 2) + wi * num_pts * 2,
                                        (i * 2 + 2) % (num_pts * 2) + wi * num_pts * 2])
                    connections.append([(i * 2 + 1) % (num_pts * 2) + wi * num_pts * 2,
                                        (i * 2 + 2) % (num_pts * 2) + wi * num_pts * 2,
                                        (i * 2 + 3) % (num_pts * 2) + wi * num_pts * 2])
                    # plt.add(vedo.Cylinder(whl_center, r=whl_r, height=whl_h, axis=(0, 1, 0)))

            whl_points.extend(box_coord)
            offset = 4 * num_pts * 2

            ''' Extend box coordinates to make the box mesh '''
            connections.extend([
                [offset + 0, offset + 1, offset + 2],
                [offset + 1, offset + 2, offset + 3],

                [offset + 0, offset + 2, offset + 4],
                [offset + 2, offset + 4, offset + 6],

                [offset + 0, offset + 1, offset + 4],
                [offset + 1, offset + 4, offset + 5],

                [offset + 4, offset + 5, offset + 6],
                [offset + 5, offset + 6, offset + 7],

                [offset + 2, offset + 3, offset + 6],
                [offset + 3, offset + 6, offset + 7],

                [offset + 1, offset + 3, offset + 5],
                [offset + 3, offset + 5, offset + 7]
            ])

            ''' Wheel mesh object along with vehicle object '''
            wheel_mesh = vedo.Mesh([whl_points, connections])
            wheel_mesh.backColor('orange4').color('orange').lineColor('black').lineWidth(1)
            plt.add(wheel_mesh)
            # mesh_rad = np.math.sqrt((veh_l+veh_f+veh_b)**2 + veh_w**2 + whl_r**2) / 2.0

            ''' Wheel bottom rectangle mesh '''
            wheel_bottom_mesh = vedo.Mesh([whl_bottoms, [(0, 1, 2), (1, 2, 3)]])
            wheel_bottom_mesh.lineColor('yellow')
            plt.add(wheel_bottom_mesh)

            wheel_mesh.rotate(15, [0, 0, 1], whl_bottoms[0])
            wheel_bottom_mesh.rotate(15, [0, 0, 1], whl_bottoms[0])
            whl_bottoms = wheel_bottom_mesh.points()

            # print(wheel_bottom_mesh.points())
            # print(wheel_bottom_mesh.pos())
            # print(whl_bottoms)

            close_meshes = []
            for i, whl_bottom in enumerate(whl_bottoms):
                close_point = cloud.closestPoint(whl_bottom, radius=3)
                mesh_i = vedo.delaunay2D(close_point).c('pink')
                close_meshes.append(mesh_i)

            ''' Find the intersection with single wheel first '''
            on_ground = []
            move_down_by = 0.4096
            accuracy_req = 0.0002
            new_whl_mesh_pos = wheel_mesh.pos()
            new_whl_bottom_pos = wheel_bottom_mesh.pos()
            while True:
                new_whl_mesh_pos[2] -= move_down_by
                new_whl_bottom_pos[2] -= move_down_by
                wheel_mesh.pos(new_whl_mesh_pos)
                wheel_bottom_mesh.pos(new_whl_bottom_pos)
                plt.render()

                print('Moving down by ', move_down_by)
                for wi, close_mesh in enumerate(close_meshes):
                    # Intersection areas to show
                    con_i = close_mesh.intersectWith(wheel_mesh)
                    con_i.c('blue')
                    int_points = con_i.points()
                    if len(int_points) > 0:
                        print('Found ', len(int_points), ' intersection points for wheel ', wi)
                        on_ground.append(wi)
                        break
                if len(on_ground) > 0:
                    if move_down_by <= accuracy_req:
                        break
                    else:
                        new_whl_mesh_pos[2] += move_down_by
                        new_whl_bottom_pos[2] += move_down_by
                        wheel_mesh.pos(new_whl_mesh_pos)
                        wheel_bottom_mesh.pos(new_whl_bottom_pos)
                        move_down_by = move_down_by / 2.0
                        on_ground = []

            whl_bottoms = wheel_bottom_mesh.points()

            ''' Now rotate around that wheel '''
            rot_index = [[0, 3], [1, 2], [2, 1], [3, 0]]
            wheel_num = on_ground[0]
            rot_axis = HpF.sub_point(whl_bottoms[rot_index[wheel_num][1]],
                                     whl_bottoms[rot_index[wheel_num][0]])
            per_axis = [1, 0 - (rot_axis[0] / rot_axis[1]), 0]
            rot_angle = -0.1
            while True:
                whl_bottoms = wheel_bottom_mesh.points()
                wheel_mesh.rotate(rot_angle, per_axis, whl_bottoms[wheel_num])
                wheel_bottom_mesh.rotate(rot_angle, per_axis, whl_bottoms[wheel_num])
                plt.render()
                print('Rotate by 0.1 degree')
                for wi, close_mesh in enumerate(close_meshes):
                    if wi == wheel_num:
                        continue
                    con_i = close_mesh.intersectWith(wheel_mesh)
                    con_i.c('blue')
                    int_points = con_i.points()
                    if len(int_points) > 0:
                        print('Found ', len(int_points), ' intersection points for wheel ', wi)
                        on_ground.append(wi)
                        break
                if len(on_ground) > 1:
                    print(on_ground)
                    break
            # for i, pt in enumerate(whl_bottoms):
            #     close_pt = cloud.closestPoint(pt, radius=mesh_rad)
            #     if len(close_pt) > 2:
            #         mesh_i = vedo.delaunay2D(close_pt).c('pink')
            #         con_i = mesh_i.intersectWith(wheel_mesh)  # Intersection areas to show
            #         con_i.c('blue')
            #         con.append(con_i)
            #         mesh.append(mesh_i)
            #         print(len(con_i.points()))
            #         plt.add(con_i)
            #         plt.add(mesh_i)

            # whl_bottom_fix = []
            # for i in range(0, 4):
            #     close_pt = find_closest_point(whl_bottom[i], num_retry=200, dist_threshold=0.3, aggressive=200)
            #     if close_pt is None:
            #         return
            #     whl_bottom_fix.append(close_pt)
            #     add_line([whl_bottom[i], close_pt])
            #
            # min_dis_pi = 0
            # for i in range(1, 4):
            #     if whl_bottom[i][2] - whl_bottom_fix[i][2] < whl_bottom[min_dis_pi][2] - whl_bottom_fix[min_dis_pi][2]:
            #         min_dis_pi = i
            #
            # whl_center = []
            # box_bottom = []
            # bottom_x_adj = [-veh_b, veh_f, -veh_b, veh_f]
            # dist_diff = whl_bottom[min_dis_pi][2] - whl_bottom_fix[min_dis_pi][2]
            # for i in range(0, 4):
            #     whl_bottom[i][2] -= dist_diff
            #     whl_center.append([whl_bottom[i][0], whl_bottom[i][1], whl_bottom[i][2] + whl_r])
            #     box_bottom.append([whl_bottom[i][0] + bottom_x_adj[i],
            #                        whl_bottom[i][1],
            #                        whl_bottom[i][2] + whl_r - veh_h / 2.0])
            #
            # for i in range(0, 4):
            #     if i != min_dis_pi:
            #         add_line([whl_bottom[min_dis_pi], whl_bottom[i]], width=2)
            #
            # num_try = -10
            #
            # pivot_point = copy.deepcopy(whl_bottom[min_dis_pi])
            # diag_point_id = 3 - min_dis_pi
            # diag_point = copy.deepcopy(whl_bottom[diag_point_id])
            # diag_angle = HpF.get_xy_angle([diag_point, pivot_point])
            # diag_dist = HpF.dist_xyz([pivot_point, diag_point])
            # side_point_ind = [[1, 2], [0, 3], [0, 3], [1, 2]]
            # side_point_1 = copy.deepcopy(whl_bottom[side_point_ind[min_dis_pi][0]])
            # side_point_2 = copy.deepcopy(whl_bottom[side_point_ind[min_dis_pi][1]])
            # side_angle = diag_angle - HpF.get_xy_angle([diag_point, side_point_1])
            # print('Side Angle = ', side_angle)
            # side_ext_dist_1 = HpF.dist_xy([diag_point, side_point_1]) * np.math.cos(side_angle)
            # side_ext_point_1 = [diag_point[0] + side_ext_dist_1 * np.math.cos(diag_angle - np.pi / 2),
            #                     diag_point[1] + side_ext_dist_1 * np.math.sin(diag_angle - np.pi / 2),
            #                     diag_point[2]]
            # side_ext_dist_2 = HpF.dist_xy([diag_point, side_point_2]) * np.math.sin(side_angle)
            # side_ext_point_2 = [diag_point[0] + side_ext_dist_2 * np.math.cos(diag_angle + np.pi / 2),
            #                     diag_point[1] + side_ext_dist_2 * np.math.sin(diag_angle + np.pi / 2),
            #                     diag_point[2]]
            # add_point(side_ext_point_1, custom_text='SEP1')
            # add_point(side_ext_point_2, custom_text='SEP2')
            # add_point(side_point_1, custom_text='SP1')
            # add_point(side_point_2, custom_text='SP2')
            # add_point(diag_point, custom_text='DP')
            # add_point(pivot_point, custom_text='PP')
            # add_line([diag_point, side_ext_point_1], width=2, col='green')
            # add_line([side_point_1, side_ext_point_1], width=2, col='green')
            # add_line([diag_point, side_ext_point_2], width=2, col='green')
            # add_line([side_point_2, side_ext_point_2], width=2, col='green')
            # while num_try < 100:
            #     z_angle = HpF.get_z_angle([pivot_point, diag_point]) - (1.0 * num_try)
            #     diag_xy_dist = diag_dist * np.math.cos(z_angle * np.pi / 180)
            #     diag_nx_point = pivot_point[0] - diag_xy_dist * np.math.cos(diag_angle * np.pi / 180)
            #     diag_ny_point = pivot_point[1] - diag_xy_dist * np.math.sin(diag_angle * np.pi / 180)
            #     diag_nz_point = pivot_point[2] + diag_dist * np.math.sin(z_angle * np.pi / 180)
            #     diag_new_point = [diag_nx_point, diag_ny_point, diag_nz_point]
            #
            #     # side_nx_point = pivot_point[0] +  + new_xy_dist * np.math.cos(diag_angle * np.pi / 180)
            #     # side_ny_point = pivot_point[1] + new_xy_dist * np.math.sin(diag_angle * np.pi / 180)
            #     # side_nz_point = pivot_point[2] + diag_dist * np.math.sin(z_angle * np.pi / 180)
            #     # side_new_point = [diag_nx_point, diag_ny_point, diag_nz_point]
            #     add_point(diag_new_point, size=Glb.RD_3, col='blue')
            #     num_try += 1
            #
            # ## Got points, calculated data. Now to add the box
            # # Vehicle center point
            # veh_cen = [veh_x + (veh_f - veh_b) / 2.0, veh_y, whl_center[min_dis_pi][2]]
            # # Vehicle wheels rep by a cylinder
            # whl_objs = [vedo.Cylinder(whl_center[i], r=whl_r, height=whl_h, axis=(0, 1, 0),
            #                           alpha=0.6).triangulate().c('purple') for i in range(0, 4)]
            # # Temp lines diagonally for the vehicle rep
            # ln_objs = [vedo.Line(whl_center[0], whl_center[3], closed=True, c='red', alpha=0.3),
            #            vedo.Line(whl_center[2], whl_center[1], closed=True, c='red', alpha=0.3)]
            # # Vehicle body rep by a box
            # box_obj = vedo.Box(veh_cen, length=(veh_l + veh_f + veh_b), width=veh_w, height=veh_h,
            #                    alpha=0.4).triangulate().c('pink')
            # mesh_rad = 1.0
            # con = []
            # mesh = []
            # for i, pt in enumerate(box_bottom):
            #     close_pt = cloud.closestPoint(pt, radius=mesh_rad)
            #     if len(close_pt) > 2:
            #         mesh_i = vedo.delaunay2D(close_pt)
            #         mesh_i.c('hotpink')
            #         con_i = mesh_i.intersectWith(box_obj)  # Intersection areas to show
            #         con.append(con_i)
            #         mesh.append(mesh_i)
            #         print(len(con_i.points()))
            # for i in range(0, 4):
            #     add_text(f'P_{i}', pos=box_bottom[i], size=1)
            # print('Cons = ', con)
            # veh_objs = []
            # veh_objs.extend(ln_objs)
            # # veh_objs.extend(whl_objs)
            # plt.add(veh_objs)

            # rot = 4
            # for i in range(-11, 10, 2):
            #     rot = i
            #      box.rotate(angle=rot, point=cpt, axis=(0, 0, 1))
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

        if len(g_plot.current_points) == 1:
            if not g_plot.tracking_mode:
                print("Tracking is ON now ... ")
                if g_plot.plotter_mode == Glb.SLOPE_AVG_MODE:
                    update_text('text2', 'SlopeAVG and Tracking: ON', )
                elif g_plot.plotter_mode == Glb.RECTANGLE_MODE:
                    update_text('text2', 'RectMode and Tracking: ON', )
                else:
                    update_text('text2', 'Vehicle mode and Tracking: ON', )
                update_text('text4', 'Select 2nd point on map')
                g_plot.tracking_mode = True

        elif len(g_plot.current_points) == 2:
            if g_plot.plotter_mode == Glb.SLOPE_AVG_MODE:
                g_plot.tracking_mode = False
                g_plot.plotter_mode = Glb.IDEAL_PLT_MODE
                update_text('text2', 'SlopeAVG: ON, Tracking: OFF')
                update_text('text3', '')
                rem_all_trackers()
                move_camera(HpF.avg_point(g_plot.current_points))
                add_line(g_plot.current_points, width=2, col='white')
                max_points = int(round(HpF.dist_xyz([g_plot.current_points[0],
                                                     g_plot.current_points[1]]) / Glb.SCALE_FACTOR))
                update_text('text5', f'Max points = {max_points}')
                num_points = int(tkinter.simpledialog.askinteger("Input Dialog",
                                                                 f"\n\tNumber of points on map,"
                                                                 f" max ({max_points}): \t\n",
                                                                 initialvalue=0,
                                                                 minvalue=0, maxvalue=max_points
                                                                 ))
                update_text('text4', f'{round(num_points)} points selected')
                get_avg_slope(num_points)
                g_plot.current_points = []
            elif g_plot.plotter_mode == Glb.RECTANGLE_MODE:
                update_text('text4', 'Make the desired rectangle')
            # elif g_plot.plotter_mode == Glb.VEHICLE_RUNNER:
            #     update_text('text4', 'Make the desired vehicle')
        elif len(g_plot.current_points) == 3:
            rect_points = HpF.get_rectangle(g_plot.current_points)
            rem_all_trackers()
            plt.remove(g_plot.plotted_points.pop())
            plt.remove(g_plot.plotted_points.pop())
            plt.remove(g_plot.plotted_points.pop())
            for vertex in range(0, 4):
                add_point(rect_points[vertex], size=Glb.RD_4, col='Green')
                add_text(f'P_{vertex}', pos=rect_points[vertex])
                add_line([rect_points[vertex], rect_points[vertex - 1]], width=3, col='lightblue')
            move_camera((rect_points[0] + rect_points[1] +
                         rect_points[2] + rect_points[3]) / 4)
            # if g_plot.plotter_mode == Glb.VEHICLE_RUNNER:
            #     g_plot.vehicle_data['coord'] = rect_points
            #     g_plot.vehicle_data['VL'] = dist_xyz(rect_points[1], rect_points[2])
            #     g_plot.vehicle_data['VW'] = dist_xyz(rect_points[0], rect_points[1])
            #     get_vehicle_data()
            # elif g_plot.plotter_mode == Glb.RECTANGLE_MODE:
            g_plot.rect_points = rect_points
            update_text('text4', 'Add the first point to draw a line')
        elif g_plot.plotter_mode == Glb.RECTANGLE_MODE and len(g_plot.current_points) >= 4:
            d_sign = 0
            if len(g_plot.current_points) == 4:
                x_p, y_p = g_plot.current_points[3][0], g_plot.current_points[3][1]
            else:
                x_p, y_p = g_plot.current_points[4][0], g_plot.current_points[4][1]
            for vertex in range(0, 4):
                x_2, y_2 = g_plot.rect_points[vertex - 0][0], g_plot.rect_points[vertex - 0][1]
                x_1, y_1 = g_plot.rect_points[vertex - 1][0], g_plot.rect_points[vertex - 1][1]
                det_val = (x_2 - x_1) * (y_p - y_1) - (x_p - x_1) * (y_2 - y_1)
                if d_sign == 0:
                    d_sign = det_val
                    continue

                if (det_val > 0 > d_sign) or (d_sign > 0 > det_val):
                    d_sign = 0
                    break
            if len(g_plot.current_points) == 4:
                if d_sign == 0:
                    print(f'Point {g_plot.current_points.pop()} lies outside the rectangle, choose again')
                    plt.remove(g_plot.plotted_points.pop())
                    rem_all_trackers()
                else:
                    update_text('text4', 'Select the 2nd point within the rectangle')
            elif len(g_plot.current_points) == 5:
                if d_sign == 0:
                    print(f'Point {g_plot.current_points.pop()} lies outside the rectangle, choose again')
                    plt.remove(g_plot.plotted_points.pop())
                else:
                    update_text('text4', 'Calculating the point star now')
                    rem_all_trackers()

                    const_dist = 30
                    perpendicular_angle = HpF.get_xy_angle([g_plot.rect_points[1], g_plot.rect_points[2]])
                    # horizontal_angle = get_angle(rect_points[0], rect_points[1])
                    # print('Angles perpendicular = ', perpendicular_angle,
                    #       ', horizontal = ', horizontal_angle)
                    g_plot.tracking_mode = False
                    g_plot.plotter_mode = Glb.IDEAL_PLT_MODE

                    num_points = int(tkinter.simpledialog.askinteger("Input a number",
                                                                     "Number of points on line",
                                                                     initialvalue=4,
                                                                     minvalue=1, maxvalue=1000
                                                                     ))
                    point_star_logging = []
                    add_line([g_plot.current_points[3], g_plot.current_points[4]],
                             width=4, col='lightgreen', elevation=2)

                    act_center_points = [np.array(g_plot.current_points[3])]
                    num_points += 1
                    for p in range(1, num_points):
                        new_center_point = (g_plot.current_points[4] * p +
                                            g_plot.current_points[3] * (num_points - p)) / num_points
                        act_center_pt = find_closest_point(new_center_point)
                        act_center_points.append(act_center_pt)
                    act_center_points.append(np.array(g_plot.current_points[4]))

                    for p, act_center_point in enumerate(act_center_points):
                        add_point(act_center_point, size=Glb.RD_4, col='Blue')
                        point_star_structure = [{'angle': perpendicular_angle + i} for i in range(-90, 94, 4)]
                        critical_angle1 = HpF.get_xy_angle([act_center_point, g_plot.rect_points[2]])
                        critical_angle2 = HpF.get_xy_angle([act_center_point, g_plot.rect_points[3]])

                        swap_index = 0
                        if critical_angle1 > critical_angle2:
                            swap_index = 2
                            temp = critical_angle1
                            critical_angle1 = critical_angle2
                            critical_angle2 = temp

                        # print('Critical angles = ', critical_angle1, critical_angle2)
                        for i in range(0, len(point_star_structure)):
                            new_angle = point_star_structure[i]['angle']
                            point_star_structure[i]['time'] = datetime.now().strftime("%b-%d-%Y %H:%M:%S")
                            # act_circle_point[2] += 0.2
                            x_value = const_dist * np.math.cos(new_angle * np.pi / 180)
                            y_value = const_dist * np.math.sin(new_angle * np.pi / 180)
                            new_circle_point = [act_center_point[0] + x_value, act_center_point[1] + y_value,
                                                act_center_point[2]]
                            act_circle_point = find_closest_point(new_circle_point)
                            if act_circle_point is None:
                                print('Error finding the point ..')
                                point_star_structure[i]['point'] = None
                                continue

                            if new_angle < critical_angle1:
                                int_point = HpF.get_xy_intersection(act_circle_point, act_center_point,
                                                                    g_plot.rect_points[1 + swap_index],
                                                                    g_plot.rect_points[2 - swap_index])
                            elif new_angle < critical_angle2:
                                int_point = HpF.get_xy_intersection(act_circle_point, act_center_point,
                                                                    g_plot.rect_points[2],
                                                                    g_plot.rect_points[3])
                            else:
                                int_point = HpF.get_xy_intersection(act_circle_point, act_center_point,
                                                                    g_plot.rect_points[0 + swap_index],
                                                                    g_plot.rect_points[3 - swap_index])

                            if HpF.dist_xy([act_circle_point, act_center_point]) > HpF.dist_xy(
                                    [int_point, act_center_point]):
                                point_star_structure[i]['point'] = int_point
                                point_star_structure[i]['slope'] = HpF.get_slope(int_point, act_center_point)
                                point_star_structure[i]['valid'] = False
                                point_star_structure[i]['Distance'] = HpF.dist_xyz([int_point, act_center_point])
                            else:
                                point_star_structure[i]['point'] = act_circle_point
                                point_star_structure[i]['slope'] = HpF.get_slope(act_circle_point, act_center_point)
                                point_star_structure[i]['valid'] = True
                                point_star_structure[i]['Distance'] = HpF.dist_xyz([act_circle_point, act_center_point])
                                # add_point(act_circle_point, size=Glb.RD_4, col='White')
                                # add_line([act_circle_point, act_center_point], width=3, col='White')

                        max_slope_index = 0
                        max_slope_value = 0

                        lines_to_plot = []
                        last_point = []

                        for i, star_point in enumerate(point_star_structure):
                            point_star_logging.append({
                                'SN': i + 1,
                                'Point Num': p + 1,
                                'Title': 'Point star value',
                                'Center Point Rel': act_center_point,
                                'Circle Point Rel': star_point['point'],
                                'Center Point Abs': act_center_point + g_plot.geo_xyz,
                                'Circle Point Abs': star_point['point'] + g_plot.geo_xyz,
                                'Slope': star_point['slope'],
                                'Angle': star_point['angle'],
                                'Timestamp': star_point['time'],
                                'Validity': star_point['valid'],
                                'Distance': star_point['Distance']
                            })
                            if star_point['valid']:
                                # points_to_plot.append(star_point['point'])
                                if len(last_point) > 0:
                                    lines_to_plot.append([last_point, star_point['point']])
                                last_point = star_point['point']
                                if abs(max_slope_value) < abs(star_point['slope']):
                                    max_slope_index = i
                                    max_slope_value = star_point['slope']

                        point_star_logging.append({
                            'SN': len(point_star_structure) + 1,
                            'Point Num': p + 1,
                            'Title': 'Point star maximum',
                            'Center Point Rel': act_center_point,
                            'Circle Point Rel': point_star_structure[max_slope_index]['point'],
                            'Center Point Abs': act_center_point + g_plot.geo_xyz,
                            'Circle Point Abs': point_star_structure[max_slope_index]['point'] + g_plot.geo_xyz,
                            'Slope': point_star_structure[max_slope_index]['slope'],
                            'Angle': point_star_structure[max_slope_index]['angle'],
                            'Timestamp': point_star_structure[max_slope_index]['time'],
                            'Validity': point_star_structure[max_slope_index]['valid'],
                            'Distance': point_star_structure[max_slope_index]['Distance']
                        })

                        # print('Max slope at ', max_slope_index, ' val = ', point_star_structure[max_slope_index])
                        add_timer_task(f'Star_Point_Plotter_{p}', task_type='add_line',
                                       task_data=lines_to_plot, meta={'width': 1, 'col': 'orange', 'elevation': 2})

                        add_point(point_star_structure[max_slope_index]['point'], size=Glb.RD_3, col='White')
                        add_line([point_star_structure[max_slope_index]['point'], act_center_point], width=4,
                                 col='White', elevation=2)
                    log_to_csv(point_star_logging, 'Star_slopes')
                    g_plot.current_points = []


def mouse_track(event):
    global g_plot

    if g_plot.tracking_mode == Glb.IDEAL_PLT_MODE:
        return

    # Track the mouse if a point has already been selected
    if not event.actor:
        # print('No actor found while tracking ... ')
        return

    mouse_point = event.picked3d

    # For normal sloping related calculations #
    # Same functionality in len(g_plot.current_points) == 1 statement
    # if not g_plot.rectangle_mode:
    #     for line in g_plot.plotted_trackers:
    #         plt.remove(line)
    #     g_plot.plotted_trackers = []
    #     add_ruler([g_plot.current_points[0], mouse_point], width=3, col='red', size=TEXT_SIZE)
    #     update_text('text3', f'Dist: {dist_xyz(g_plot.current_points[0], mouse_point):.3f}')
    #     return

    # For the Rectangle Mode operation #
    if len(g_plot.current_points) == 1 or len(g_plot.current_points) == 4:
        if len(g_plot.plotted_trackers) > 0:
            plt.remove(g_plot.plotted_trackers.pop())
        add_ruler([g_plot.current_points[-1], mouse_point], width=3, col='yellow', size=Glb.TEXT_SIZE)
        update_text('text3', f'Dist: {HpF.dist_xyz([g_plot.current_points[-1], mouse_point]):.3f}')
        return

    if len(g_plot.current_points) == 2:
        rem_all_trackers()
        rect_points = HpF.get_rectangle([g_plot.current_points[0], g_plot.current_points[1], mouse_point])
        for i in range(0, 4):
            add_ruler([rect_points[i], rect_points[i - 1]], width=3, col='white', size=Glb.TEXT_SIZE)
        return


# The get_line_of_points takes the two endpoints, then does its best to get the pt along the path of the line
# that are on the ground of the point cloud Does this by iterating through the pt that make up the line in
# space, then getting the closest point that is actually a part of the mesh to that point
def add_point(pos, size=Glb.RD_2, col='red', silent=True, is_text=False, custom_text=''):
    global g_plot
    new_point = vedo.Point(pos, r=size, c=col)  # Point to be added, default radius and default color
    plt.add(new_point)
    g_plot.plotted_points.append(new_point)
    if is_text or len(custom_text) > 0:
        pos2 = [pos[0], pos[1], pos[2] + 2]
        if len(custom_text) == 0:
            custom_text = ','.join(['%.3f' % e for e in (pos - g_plot.min_xyz)])
        new_text = vedo.Text3D(txt=custom_text, s=1, pos=pos2, depth=0.1, alpha=1.0, c='w')
        plt.add([new_text])

    # plt.render()
    if not silent:
        print(f'Added point: {pos - g_plot.min_xyz}')
    return new_point


def add_text(text, pos, silent=True, size=2):
    pos[2] += 1
    tx1 = vedo.Text3D(txt=text, s=size, pos=pos, depth=0.1, alpha=1.0)
    plt.add([tx1])
    # plt.render()
    if not silent:
        print(f'Text Rendered at {pos - g_plot.min_xyz}')
    return tx1


def add_line(points, col='red', width=3, silent=True, elevation=0):
    global g_plot
    new_line = None
    if len(points) >= 2:
        new_line = vedo.Line([points[0][0], points[0][1], points[0][2] + (elevation * 0.04)],
                             [points[1][0], points[1][1], points[1][2] + (elevation * 0.04)],
                             lw=width, c=col, alpha=1.0)
        plt.add([new_line])
        g_plot.plotted_lines.append(new_line)
        if not silent:
            print(f'Added {col} line bw {points[0] - g_plot.min_xyz} and {points[1] - g_plot.min_xyz}')
    else:
        print('Invalid number of points')
    return new_line


def add_lines(points, col='yellow', width=4, silent=True):
    if len(points) < 2:
        print('Invalid number of pt')
        return None
    new_lines = []
    # with concurrent.futures.ThreadPoolExecutor() as executor:
    #     results = [executor.map(add_line, ([points[i - 1], points[i]], col, width, silent))
    #                for i in range(1, len(points))]
    for i in range(1, len(points)):
        # threading.Thread(target=add_line, args=([points[i - 1], points[i]], col, width, silent)).start()
        new_lines.append(add_line([points[i - 1], points[i]], col=col, width=width, silent=silent))
    return new_lines


def add_ruler(points, col='white', width=4, size=2):
    global g_plot
    if len(points) >= 2:
        # distance = dist_xyz(points[0], points[1])
        # line_text = ''
        # if distance > 50:
        #     line_text = f'{dist_xyz(points[0], points[1]):.2f}'
        # elif distance > 25:
        #     line_text = f'{dist_xyz(points[0], points[1]):.1f}'
        start = [points[0][0], points[0][1], points[0][2] + 1]
        ended = [points[1][0], points[1][1], points[1][2] + 1]
        new_line = vedo.Ruler(start, ended, lw=width, c=col, alpha=1.0, s=size)
        plt.add([new_line])
        g_plot.plotted_trackers.append(new_line)
        return new_line
    else:
        print('Invalid number of pt')


def update_text(text_id, value, rel_pos=None, size=Glb.TEXT_SIZE):
    global text_objects
    if rel_pos is None:
        rel_pos = [5, 5, 5]
    if text_id in text_objects.keys():
        plt.remove(text_objects[text_id]['text'])
        rel_pos = text_objects[text_id]['pos']
    new_text = add_text(value, pos=g_plot.min_xyz + rel_pos, silent=True, size=size)
    text_objects[text_id] = {
        'text': new_text,
        'pos': rel_pos
    }
    plt.add(new_text)


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


def print_point(point):
    print(','.join(['%.3f' % e for e in (point - g_plot.min_xyz)]))


# Get the average slope of from point to point for a specified number of pt on the line
def get_avg_slope(num_points):
    global g_plot, cloud, all_tasks
    update_text('text3', 'Enter num pt:')

    if num_points == 0:
        points_to_use = g_plot.current_points
    else:
        x_unit = (g_plot.current_points[1][0] - g_plot.current_points[0][0]) / (num_points + 1)
        y_unit = (g_plot.current_points[1][1] - g_plot.current_points[0][1]) / (num_points + 1)
        cur_point = g_plot.current_points[0]
        z_offset = 0
        points_to_use = []
        bad_point_count = made_better = 0
        acceptable_dist = 0.2
        for i in range(0, num_points):
            new_approx_point = [cur_point[0] + x_unit, cur_point[1] + y_unit, cur_point[2] + z_offset]
            # add_point(new_approx_point, size=Glb.RD_4, col='white', silent=True)
            new_actual_point = cloud.closestPoint(new_approx_point)
            xy_dist_temp = HpF.dist_xy([new_approx_point, new_actual_point])
            if xy_dist_temp < acceptable_dist:
                points_to_use.append(new_actual_point)
                z_offset = new_actual_point[2] - new_approx_point[2]
            else:
                bad_point_count += 1
                new_approx_point = [cur_point[0] + (x_unit * 1.1), cur_point[1] + (y_unit * 1.1),
                                    cur_point[2] + z_offset]
                new_actual_points = cloud.closestPoint(new_approx_point, radius=acceptable_dist)
                if len(new_actual_points) > 1:
                    made_better += 1
                    points_to_use.append(new_actual_points[0])
                    z_offset = new_actual_points[0][2] - new_approx_point[2]
            cur_point = new_approx_point
        print('Bad points = ', bad_point_count)

        if len(points_to_use) < 1:
            print('Error in point selection. Aborting')
            return
        points_to_use.insert(0, g_plot.current_points[0])
        points_to_use.append(g_plot.current_points[1])
    # Loop through pt and plot them

    update_text('text3', f'Rendering {len(points_to_use)} pt')
    print(f'Rendering {len(points_to_use)} on map ', end='')
    # st = '.'
    # for p in points_to_use:
    #     add_point(p, size=Glb.RD_3, col='g', silent=True)
    #     update_text('text6', st)
    #     st += '.'
    #     print('.', end='')
    # time.sleep(0.3)
    print(' Done!')
    lines_to_use = []
    for i in range(len(points_to_use) - 1):
        lines_to_use.append([points_to_use[i], points_to_use[i + 1]])

    add_timer_task(f'Add {len(points_to_use)} on map', task_type='add_point',
                   task_data=points_to_use, meta={'col': 'green', 'size': Glb.RD_3})
    add_timer_task(f'Adding {len(lines_to_use)} on map', task_type='add_line',
                   task_data=lines_to_use, meta={'col': 'yellow', 'elevation': 2})
    # point1 = ', '.join(['%.3f' % e for e in points_to_use[0]])
    # print_text = ''

    total_slope = 0
    slopes_bw_points = []
    # slopes_bw_points = {'point_1': points_to_use[0:-1], 'point_2': points_to_use[1:],
    #                     'Title': [], 'Slope': [],
    #                     'Distance': [], 'Timestamp': []}
    #
    # for ind in range(0, len(slopes_bw_points['point_1'])):
    #     slopes_bw_points['Distance'].append(
    #         dist_xyz(slopes_bw_points['point_1'][ind], slopes_bw_points['point_2'][ind]))

    for pt in range(1, len(points_to_use)):
        # point2 = ','.join(['%.3f' % e for e in points_to_use[pt]])
        xyz_dist = HpF.dist_xyz([points_to_use[pt - 1], points_to_use[pt - 0]])
        slope_xy = HpF.get_slope(points_to_use[pt - 1], points_to_use[pt - 0])
        if abs(slope_xy) < 1000:
            total_slope += slope_xy
            slopes_bw_points.append({
                'SN': pt,
                'Title': 'Incremental Slope',
                'Point1_Rel': points_to_use[pt - 1],
                'Point2_Rel': points_to_use[pt - 0],
                # 'X1': points_to_use[pt - 1][0],
                # 'Y1': points_to_use[pt - 1][1],
                # 'Z1': points_to_use[pt - 1][2],
                # 'X2': points_to_use[pt - 0][0],
                # 'Y2': points_to_use[pt - 0][1],
                # 'Z2': points_to_use[pt - 0][2],
                'Point1_Abs': points_to_use[pt - 1] + g_plot.geo_xyz,
                'Point2_Abs': points_to_use[pt - 0] + g_plot.geo_xyz,
                'Slope': slope_xy,
                'Distance': xyz_dist,
                'Timestamp': datetime.now().strftime("%b-%d-%Y %H:%M:%S")
            })
        # print_text += point1 + ', ' + point2 + '\n'
        # point1 = point2
    # print_text = 'X1, Y1, Z1, X2, Y2, Z2, Slope, Distance \n'
    # print_text += '\n'.join([ (e['Point1_Rel'], e['Point2_Rel'],
    #                           e['Slope'], e['Distance']) for e in slopes_bw_points])
    # print(print_text)
    average_slope = total_slope / len(slopes_bw_points)

    slopes_bw_points.append({
        'SN': len(points_to_use),
        'Title': 'Slope BW First and Last',
        'Point1_Rel': points_to_use[1 - 1],
        'Point2_Rel': points_to_use[0 - 1],
        'Point1_Abs': points_to_use[1 - 1] + g_plot.geo_xyz,
        'Point2_Abs': points_to_use[0 - 1] + g_plot.geo_xyz,
        # 'X1': points_to_use[0][0],
        # 'Y1': points_to_use[0][1],
        # 'Z1': points_to_use[0][2],
        # 'X2': points_to_use[-1][0],
        # 'Y2': points_to_use[-1][1],
        # 'Z2': points_to_use[-1][2],
        'Slope': HpF.get_slope(points_to_use[0], points_to_use[-1]),
        'Distance': HpF.dist_xyz([points_to_use[0], points_to_use[-1]]),
        'Timestamp': datetime.now().strftime("%b-%d-%Y %H:%M:%S")
    })

    slopes_bw_points.append({
        'SN': len(points_to_use),
        'Title': 'Average Slope',
        'Point1_Rel': points_to_use[1 - 1],
        'Point2_Rel': points_to_use[0 - 1],
        'Point1_Abs': points_to_use[1 - 1] + g_plot.geo_xyz,
        'Point2_Abs': points_to_use[0 - 1] + g_plot.geo_xyz,
        # 'X1': points_to_use[0][0],
        # 'Y1': points_to_use[0][1],
        # 'Z1': points_to_use[0][2],
        # 'X2': points_to_use[-1][0],
        # 'Y2': points_to_use[-1][1],
        # 'Z2': points_to_use[-1][2],
        'Slope': average_slope,
        'Distance': HpF.dist_xyz([points_to_use[0], points_to_use[-1]]),
        'Timestamp': datetime.now().strftime("%b-%d-%Y %H:%M:%S")
    })
    log_to_csv(slopes_bw_points, 'Slope')
    print(f'Average slope between {len(points_to_use)} points = {average_slope}, \n List of slopes for indices: ')
    update_text('text4', f'Avg slope = {average_slope:.3f}')
    update_text('text5', 'Press z again to enter slope mode')
    return average_slope


def log_to_csv(dict_to_write, name='Slope'):
    dir_name = f'Output_{datetime.now().strftime("%Y%m%d")}'
    os.makedirs(dir_name, exist_ok=True)
    csv_file_name = f'{name}_{datetime.now().strftime("%Y%m%d%H%M%S")}_{len(dict_to_write)}_points.csv'
    try:
        with open(dir_name + '\\' + csv_file_name, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=[e for e in dict_to_write[0].keys()])
            writer.writeheader()
            for data in dict_to_write:
                writer.writerow(data)
    except IOError:
        print("I/O error")


def reset_plot():
    global g_plot, cloud
    print('Removing all objects from map')
    plt.clear()
    plt.axes = 1
    # plt.add([mesh, cloud]).render()
    plt.add([cloud]).render()
    update_text('text2', 'SlopeAVG and Tracking: OFF')
    update_text('text3', '')
    update_text('text4', '')
    g_plot.initialized = False
    g_plot.current_points = []
    g_plot.tracking_mode = False


# def get_list(num_elements, arr):
#     arr_len = len(arr)
#     return [arr[(i * arr_len // num_elements) + (arr_len // (2 * num_elements))] for i in range(num_elements)]


def my_camera_reset():
    plt.camera.SetPosition([2321420.115, 6926160.299, 995.694])
    plt.camera.SetFocalPoint([2321420.115, 6926160.299, 702.312])
    plt.camera.SetViewUp([0.0, 1.0, 0.0])
    plt.camera.SetDistance(293.382)
    plt.camera.SetClippingRange([218.423, 388.447])
    # plt.render()
    print('Camera Reset Done')


# def slider_y(widget, event):
#     global g_plot
#     value = widget.GetRepresentation().GetValue()
#     value = (value ** 1.5) / (max_points ** 0.5)
#     g_plot.smooth_factor = round(value)
#     update_text('text4', f'{round(g_plot.smooth_factor)} points selected')
#     # update_text('text5', f'Max points = {max_points}')


def rem_all_trackers():
    global g_plot
    for line in g_plot.plotted_trackers:
        plt.remove(line)
    g_plot.plotted_trackers = []


def move_camera(point):
    global g_plot, plt
    # if elevation == 0:
    #     elevation = g_plot.cam_center[2]
    # new_cam_pos = [point[0], point[1], elevation]
    # focal_pos = point
    # new_cam = dict(pos=new_cam_pos,
    #                focalPoint=focal_pos,
    #                viewup=(0, 1.00, 0),
    #                clippingRange=(218.423, 388.447)
    #                )
    plt.flyTo(point)
    # plt.show(g_plot.show_ele_list, interactorStyle=0, bg='white', axes=1, zoom=1.0, interactive=True, camera=new_cam)


def get_file_names(required_files):
    global g_plot
    file_names = {}
    if required_files is None or len(required_files) == 0:
        return file_names

    use_defaults = True
    root = tkinter.Tk()
    root.withdraw()
    file_types = {
        'PLY': {'ext': ('.ply', '.PLY'), 'title': 'PLY File', 'desc': 'Point-cloud file', 'default': 't3.ply'},
        'TIF': {'ext': ('.tif', '.tiff'), 'title': 'TIF File', 'desc': 'Tagged Image File', 'default': '3_1.tif'},
        'PNG': {'ext': ('.png', '.jpg', '.jpeg'), 'title': 'Image File', 'desc': 'Image Files', 'default': '3_1.png'},
        'LAS': {'ext': ('.las', '.LAS'), 'title': 'LAS File', 'desc': 'LAS point file', 'default': '3_1.las'},
        'TFW': {'ext': ('.tfw', '.TFW'), 'title': 'TFW GIS File', 'desc': 'World coordinate file', 'default': '3_1.tfw'}
    }

    if len(sys.argv) < 1 + len(required_files):
        titles = ['[' + file_types[file_type]['title'] + ']' for file_type in required_files]
        if not use_defaults:
            print('Default Usage:  ', os.path.basename(__file__), ', '.join(titles))
        for i, file_type in enumerate(required_files):
            if use_defaults:
                file_name = file_types[file_type]['default']
            else:
                print(f'No {file_type} file specified: opening prompt')
                file_name = tkinter.filedialog.askopenfilename(initialdir=os.getcwd(),
                                                               title=f'Select the {file_type} File',
                                                               filetypes=[(file_types[file_type]['desc'],
                                                                           file_types[file_type]['ext'])])
            file_names[file_type] = file_name
    else:
        for i, file_type in enumerate(required_files):
            file_names[file_type] = sys.argv[i + 1]

    for file_t in file_names:
        if not os.path.isfile(file_names[file_t]):
            print(f'Invalid {file_t} file path: {file_names[file_t]}')
            exit(1)

    root.destroy()
    return file_names


def button_func():
    print('Pressed')


def toggle_state(queue_obj: multiprocessing.Queue, value):
    d = {
        'time': time.time(),
        'value': value
    }
    queue_obj.put(d)
    print(queue_obj.qsize())


vedo.settings.enableDefaultKeyboardCallbacks = False
plt = vedo.Plotter(pos=[0, 0], size=[600, 1080])
temp_file = open('temp_file', mode='w+')
temp_file.close()
cloud = vedo.load('temp_file')


def plt_main(inp_q, out_q):
    global cloud, plt, g_plot
    print(f'Program started :')

    g_plot.inp_q = inp_q
    g_plot.out_q = out_q
    # [ply_file, pic_name, las_file] = get_file_names()
    req_files = ['PLY', 'TFW']
    file_names = get_file_names(req_files)
    print(f'Selected files: {file_names}')

    ply_file = file_names['PLY']
    tfw_file = file_names['TFW']

    ################################################################################################
    # st = time.time()
    # tif_img = tifffile.TiffFile(tif_file)
    # tif_tags = tif_img.pages[0].geotiff_tags
    # scale_fact = tif_tags['ProjLinearUnitSizeGeoKey']
    # g_plot.geo_xyz = tif_tags['ModelTiepoint'][3:]
    # print(f'Loaded cloud {tif_file} in {time.time() - st} sec')

    ################################################################################################
    # st = time.time()
    # pic = Picture(pic_name)
    # print(f'Loaded picture {pic_name} in {time.time() - st} sec')

    ################################################################################################
    st = time.time()
    tfw_file_pt = open(tfw_file)
    lines = tfw_file_pt.readlines()
    for i in range(len(lines)):
        lines[i] = lines[i].rstrip('\r\n')
    g_plot.scale_f = 0.30480060960121924
    g_plot.geo_xyz = [float(lines[4]), float(lines[5]), 0.0]
    print(f'Loaded cloud {tfw_file} in {time.time() - st} sec')
    ################################################################################################

    st = time.time()
    cloud = vedo.load(ply_file).pointSize(4.0).scale(
        (1 / g_plot.scale_f, 1 / g_plot.scale_f, 1 / g_plot.scale_f))
    g_plot.min_xyz = np.min(cloud.points(), axis=0)
    g_plot.max_xyz = np.max(cloud.points(), axis=0)
    cloud = cloud.pos(x=0 - g_plot.min_xyz[0], y=0 - g_plot.min_xyz[1], z=0 - g_plot.min_xyz[2])
    # cloud.cmap('terrain').addScalarBar()
    print(f'Loaded cloud {ply_file} in {time.time() - st} sec')
    ################################################################################################
    g_plot.geo_xyz[2] = g_plot.min_xyz[2]
    g_plot.geo_xyz[1] = g_plot.geo_xyz[1] + (g_plot.min_xyz[1] - g_plot.max_xyz[1])
    g_plot.max_xyz = g_plot.max_xyz - g_plot.min_xyz
    g_plot.min_xyz = g_plot.min_xyz - g_plot.min_xyz
    print(f'Min X = {g_plot.min_xyz[0]}, Y = {g_plot.min_xyz[1]}, Z = {g_plot.min_xyz[2]}')
    print(f'Max X = {g_plot.max_xyz[0]}, Y = {g_plot.max_xyz[1]}, Z = {g_plot.max_xyz[2]}')
    print(f'Geo X = {g_plot.geo_xyz[0]}, Y = {g_plot.geo_xyz[1]}, Z = {g_plot.geo_xyz[2]}')

    ################################################################################################
    # st = time.time()
    # new_mesh = delaunay2D(cloud.points()).alpha(0.3).c('grey')  # Some new_mesh object with low alpha
    # dim = pic.dimensions()
    # range_xyz = g_plot.max_xyz - g_plot.min_xyz
    # scale_fact = [range_xyz[0] / dim[0], range_xyz[1] / dim[1], 1]
    # pic = pic.scale(scale_fact).pos(g_plot.min_xyz[0] - 1, g_plot.min_xyz[1] + 0.2,
    #                                 g_plot.min_xyz[2]).rotateZ(2)
    # print(f'Mesh created in {time.time() - st} sec for {len(cloud.points())} points')

    ################################################################################################
    plt.addCallback('KeyPress', on_key_press)
    plt.addCallback('LeftButtonPress', on_left_click)
    plt.addCallback('RightButtonPress', on_right_click)
    plt.addCallback('MouseMove', mouse_track)
    plt.addCallback('timer', handle_timer)
    plt.addCallback('Enter', enter_callback)
    plt.addCallback('Leave', leave_callback)
    print('Once the program launches, Use the following keymap:'
          '\n\t \'z\' or \'Z\'  for Slope mode'
          '\n\t \'v\' or \'V\'  for Vehicle Mode'
          '\n\t \'r\' or \'R\'  for Rectangle Mode'
          '\n\t \'u\' or \'z\'  for Resetting the plot'
          '\n\t \'c\' or \'z\'  for Clearing everything'
          '\n\t \'Esc\' to Close everything')

    st = time.time()
    g_plot.cloud_center = cloud.centerOfMass()  # Center of mass for the whole cloud
    print(f'Center of mass = {g_plot.cloud_center}, calc in {time.time() - st} sec')
    g_plot.cam_center = [g_plot.cloud_center[0], g_plot.cloud_center[1], g_plot.cloud_center[2] + 150]
    g_plot.show_ele_list = [cloud]

    cam = dict(pos=g_plot.cam_center,
               focalPoint=g_plot.cloud_center,
               viewup=(0, 1.00, 0),
               clippingRange=(218.423, 388.447)
               )
    plt.show(g_plot.show_ele_list, interactorStyle=0, bg='white', axes=1, zoom=1.0, interactive=True,
             camera=cam)


def key_press(event):
    global g_plot
    g_plot.last_key_press = event.char
    print(event)


def add_rectangle(points):
    if len(points) < 3:
        print('Insufficient points')
        return


def find_closest_point(point, num_retry=60, dist_threshold=1.0, aggressive=2.0):
    fact = 1.0
    aggressive = aggressive ** 0.1111
    dist_found = 0.0
    min_dist = 9999999.9
    closest_pt_yet = []
    ## 2^0.1111 is about 1.08
    for rt in range(0, num_retry):
        # rand_point = [(xyz + (random.random() - 0.5)*fact) for xyz in point]
        rand_point = [point[0], point[1], point[2] - (random.random() - 0.25) * fact]
        close_point = cloud.closestPoint(rand_point)
        fact *= aggressive
        dist_found = HpF.dist_xy([close_point, rand_point])
        if min_dist > dist_found:
            min_dist = dist_found
            closest_pt_yet = close_point
        if dist_found < dist_threshold:
            # print('Found cp in ', rt, ' tries')
            return close_point

    fact = 1.0
    for rt in range(num_retry, num_retry * 2):
        # rand_point = [(xyz + (random.random() - 0.5)*fact) for xyz in point]
        rand_point = [point[0], point[1], point[2] - (random.random() - 0.75) * fact]
        close_point = cloud.closestPoint(rand_point)
        fact *= aggressive
        dist_found = HpF.dist_xy([close_point, rand_point])
        if min_dist > dist_found:
            min_dist = dist_found
            closest_pt_yet = close_point
        if dist_found < dist_threshold:
            # print('Found cp in inv dir for ', rt, ' tries')
            return close_point

    print('Failed to find a close point for ', point, ', min dist = ', min_dist)
    return closest_pt_yet


class LocalPlotter:
    plotter_mode = Glb.VEHICLE_RUNNER
    # slope_avg_mode = False
    # rectangle_mode = False
    # vehicle_mode = False
    tracking_mode = False
    # slider_selected = False
    initialized = False
    min_xyz: []
    max_xyz: []
    geo_xyz: []
    cloud_center: []
    cam_center: []
    scale_f = 1.0
    last_key_press = None
    smooth_factor = 0
    inp_q: multiprocessing.Queue
    out_q: multiprocessing.Queue
    gui_q: multiprocessing.Queue
    timerID = None
    current_points = []
    plotted_trackers = []
    plotted_points = []
    plotted_lines = []
    rect_points = []
    show_ele_list = []
    vehicle = vedo.Box()
    vehicle_data = Intf.VehicleData()


''' All the global variables declared '''
g_plot = LocalPlotter()
text_objects = {
}
all_tasks = {
}
''' End of variable declarations '''


################################################################################################
############################## MAIN LIKE SECTION ###############################################

# gui_thread = threading.Thread(target=gui_main)
# print('Starting the GUI Thread')
# gui_thread.start()

# plotter_thread = threading.Thread(target=plotter_main)
# print('Starting plotter thread')
# plotter_thread.start()

################################################################################################


def main():
    print(vedo.printInfo(vedo))
    inp_q = multiprocessing.Queue()
    out_q = multiprocessing.Queue()

    plt_process = multiprocessing.Process(target=plt_main, args=(inp_q, out_q))
    plt_process.start()

    # gui_process = multiprocessing.Process(target=gui_main, args=(inp_q, out_q))
    # gui_process.start()
    # gui_process.join()
    plt_process.join()


if __name__ == '__main__':
    main()
    exit()
