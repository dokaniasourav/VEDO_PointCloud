import os
import sys
import csv
import time

import vedo
import copy
import scipy
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


# Constantly checking if any meaningful key is selected
def on_key_press(event):
    global plt, g_plot
    g_plot.last_key_press = event.keyPressed
    if event.keyPressed in ['c', 'C']:
        for point in g_plot.plotted_points:
            plt.remove(point, render=True)
        for p_trac in g_plot.plotted_trackers:
            plt.remove(p_trac, render=True)
        for p_line in g_plot.plotted_lines:
            plt.remove(p_line, render=True)
        for p_text in g_plot.plotted_lines:
            plt.remove(p_text, render=True)
        plt.sliders = g_plot.current_points = []
        g_plot.plotted_trackers = []
        g_plot.plotted_points = []
        g_plot.plotted_lines = []
        g_plot.plotted_texts = []
        g_plot.plotter_mode = Glb.IDEAL_PLT_MODE
        print('==== Cleared all elements on plot ====')
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
        elif event.keyPressed in ['S', 's']:
            print("=== ENTER RECTANGLE MODE ====")
            update_text('text5', 'Rectangle mode is ON')
            g_plot.plotter_mode = Glb.RECTANGLE_MODE
        elif event.keyPressed in ['V', 'v']:
            print("=== ENTER VEHICLE MODE ====")
            update_text('text5', 'Vehicle mode is ON')
            g_plot.plotter_mode = Glb.VEHICLE_RUNNER
            if g_plot.gp_int_state == 0:
                state_vehicle([0.1, 0.1])

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
        # all_tasks['timer_id'] = plt.timer_callback('create', dt=10)
        g_plot.initialized = True
    if g_plot.timerID is not None:
        plt.timer_callback('destroy', timerId=g_plot.timerID)
        g_plot.timerID = None


def leave_callback(event):
    global g_plot, all_tasks
    # if 'timer_id' in all_tasks.keys():
    #     return
    # if g_plot.timerID is None:
    #     g_plot.timerID = plt.timer_callback('create', dt=500)


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
        plt.timer_callback('destroy', timerId=timer_id)
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
            'timer': plt.timer_callback('create', dt=10),
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

    if event.picked3d is None:
        return

    if g_plot.plotter_mode != Glb.IDEAL_PLT_MODE:
        cpt2 = vedo.vector(list(event.picked3d))
        cpt = find_closest_point(cpt2)
        if cpt is not None:
            # Adding the valid points on CPT list
            g_plot.current_points.append(cpt)
        else:
            # Cant do much if point is not found
            print('Could not find valid point on left click')
            return
    else:
        return

    if g_plot.plotter_mode == Glb.SLOPE_AVG_MODE:
        state_slope_avg(cpt)
    elif g_plot.plotter_mode == Glb.RECTANGLE_MODE:
        state_rectangle(cpt)
    elif g_plot.plotter_mode == Glb.VEHICLE_RUNNER:
        state_vehicle(cpt)
    else:
        print('Internal Error!')


def state_slope_avg(cpt):
    global g_plot
    add_point(cpt, size=Glb.RD_2, col='red')

    if len(g_plot.current_points) == 1:
        g_plot.tracking_mode = True             # TURN ON TRACKING
        print("Tracking turned ON")
        update_text('text2', 'SlopeAVG and Tracking: ON', )
        update_text('text4', 'Select 2nd point on map')

    elif len(g_plot.current_points) == 2:
        g_plot.tracking_mode = False                # TURN OFF TRACKING
        g_plot.plotter_mode = Glb.IDEAL_PLT_MODE    # Done with Slope mode
        rem_all_trackers()

        update_text('text2', 'SlopeAVG: ON, Tracking: OFF')
        update_text('text3', '')
        move_camera(HpF.avg_points(g_plot.current_points))
        add_line(g_plot.current_points, width=2, col='white')
        max_points = int(round(HpF.dist_xyz([g_plot.current_points[0],
                                             g_plot.current_points[1]]) / Glb.SCALE_FACTOR))
        update_text('text5', f'Max points = {max_points}')

        root = tkinter.Tk()
        root.withdraw()
        num_points = int(tkinter.simpledialog.askinteger("Input Dialog",
                                                         f"\n\tNumber of points on map,"
                                                         f" max ({max_points}): \t\n",
                                                         initialvalue=10,
                                                         minvalue=0, maxvalue=max_points
                                                         ))
        update_text('text4', f'{round(num_points)} points selected')
        get_avg_slope(num_points)
        root.destroy()
        g_plot.current_points = []


def state_rectangle(cpt):
    global g_plot

    num_cur_points = len(g_plot.current_points)
    add_point(cpt, size=Glb.RD_3, col='yellow', custom_text=f'{num_cur_points}_P')

    if num_cur_points == 1:
        g_plot.tracking_mode = True             # Turn ON Tracking mode
        print("Tracking is ON now ... ")
        update_text('text2', 'RectMode and Tracking: ON')
        update_text('text4', 'Select 2nd point on map')

    elif num_cur_points == 2:
        update_text('text4', 'Make the desired rectangle')

    elif num_cur_points == 3:
        rect_points = HpF.get_rectangle(g_plot.current_points)
        rem_all_trackers()
        rect_points_real = []
        for pt in range(0, 3):
            plt.remove(g_plot.plotted_points.pop())
            plt.remove(g_plot.plotted_texts.pop())
        for vtx in range(0, 4):
            close_pt = find_closest_point(rect_points[vtx])
            add_point(close_pt, size=Glb.RD_4, col='Green')
            add_text(f'{vtx}_V', pos=close_pt)
            rect_points_real.append(close_pt)
        for vtx in range(0, 4):
            add_line([rect_points_real[vtx], rect_points_real[vtx - 1]], width=3, col='lightblue')
        move_camera((rect_points[0] + rect_points[1] +
                     rect_points[2] + rect_points[3]) / 4)
        g_plot.rect_points = rect_points_real
        update_text('text4', 'Add the first point to draw a line')
    elif num_cur_points >= 4:
        d_sign = 0
        if num_cur_points == 4:
            x_p = g_plot.current_points[3][0]
            y_p = g_plot.current_points[3][1]
        else:
            x_p = g_plot.current_points[4][0]
            y_p = g_plot.current_points[4][1]
        for vtx in range(0, 4):
            x_2, y_2 = g_plot.rect_points[vtx - 0][0], g_plot.rect_points[vtx - 0][1]
            x_1, y_1 = g_plot.rect_points[vtx - 1][0], g_plot.rect_points[vtx - 1][1]
            det_val = (x_2 - x_1) * (y_p - y_1) - (x_p - x_1) * (y_2 - y_1)
            if d_sign == 0:
                d_sign = det_val
                continue
            if (det_val > 0 > d_sign) or (d_sign > 0 > det_val):
                d_sign = 0
                break
        if num_cur_points == 4:
            if d_sign == 0:
                print(f'Point {g_plot.current_points.pop()} lies outside the rectangle, choose again')
                plt.remove(g_plot.plotted_points.pop())
                plt.remove(g_plot.plotted_texts.pop())
                rem_all_trackers()
            else:
                update_text('text4', 'Select the 2nd point within the rectangle')
        elif num_cur_points == 5:
            if d_sign == 0:
                print(f'Point {g_plot.current_points.pop()} lies outside the rectangle, choose again')
                plt.remove(g_plot.plotted_points.pop())
            else:
                g_plot.tracking_mode = False
                g_plot.plotter_mode = Glb.IDEAL_PLT_MODE

                update_text('text4', 'Calculating the point star now')
                rem_all_trackers()

                const_dist = 30
                perpendicular_angle = HpF.get_xy_angle([g_plot.rect_points[1], g_plot.rect_points[2]])
                # horizontal_angle = get_angle(rect_points[0], rect_points[1])
                # print('Angles perpendicular = ', perpendicular_angle,
                #       ', horizontal = ', horizontal_angle)

                root = tkinter.Tk()
                root.withdraw()
                num_points = int(tkinter.simpledialog.askinteger("Input a number",
                                                                 "Number of points on line",
                                                                 initialvalue=8,
                                                                 minvalue=1, maxvalue=1000
                                                                 ))
                root.destroy()

                point_star_logging = []
                add_line([g_plot.current_points[3], g_plot.current_points[4]],
                         width=4, col='lightgreen', elevation=2)

                act_center_points = [np.array(g_plot.current_points[3])]
                num_points += 1
                for point in range(1, num_points):
                    new_center_point = (g_plot.current_points[4] * point +
                                        g_plot.current_points[3] * (num_points - point)) / num_points
                    act_center_pt = find_closest_point(new_center_point)
                    act_center_points.append(act_center_pt)
                act_center_points.append(np.array(g_plot.current_points[4]))

                # Angle between points is 4 degrees
                angle_between_points = 4
                for point, act_center_point in enumerate(act_center_points):
                    add_point(act_center_point, size=Glb.RD_4, col='Blue')
                    point_star_structure = [{'angle': perpendicular_angle + i}
                                            for i in range(-90, 94, angle_between_points)]
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
                            'Point Num': point + 1,
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
                        'Point Num': point + 1,
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
                    add_timer_task(f'Star_Point_Plotter_{point}', task_type='add_line',
                                   task_data=lines_to_plot, meta={'width': 1, 'col': 'orange', 'elevation': 2})

                    add_point(point_star_structure[max_slope_index]['point'], size=Glb.RD_3, col='White',
                              custom_text=str(point))
                    add_line([point_star_structure[max_slope_index]['point'], act_center_point], width=4,
                             col='White', elevation=2)
                log_to_csv(point_star_logging, 'Star_slopes')
                g_plot.current_points = []


def state_vehicle(cpt):
    global g_plot

    ''' Only called when initializing for the first time from a key press = V'''
    if g_plot.gp_int_state == 0:
        update_text('text2', 'Vehicle mode and Tracking: ON')
        new_window = multiprocessing.Process(target=Intf.get_vehicle_data, args=(g_plot.out_q,))
        new_window.start()
        new_window.join()
        if not g_plot.out_q.empty():
            g_plot.vehicle_data = g_plot.out_q.get()

        g_plot.vehicle_data.height = g_plot.vehicle_data.wheel_radius / 2.0

        g_plot.gp_int_state = 1

    elif g_plot.gp_int_state == 1:

        ''' Wheel bottom mesh and vehicular body mesh '''

        ## 1. Specify the mesh position
        g_plot.vehicle_data.position = cpt
        add_point(cpt, size=Glb.RD_4, col='purple', is_text=True, custom_text='Point A')

        ## 2. Call the function for creating the 2 mesh objects
        g_plot.vehicle_data.vehicle_mesh = make_vehicle_mesh(g_plot.vehicle_data)
        plt.add(g_plot.vehicle_data.vehicle_mesh)

        ## 3. Render the current plot
        plt.render()
        print('Add a second point to track the vehicle')

        ## 4.
        g_plot.gp_int_state = 2
        g_plot.tracking_mode = True
        print('Tracking mode is ON')

    elif g_plot.gp_int_state == 2:
        g_plot.tracking_mode = False
        add_point(cpt, size=Glb.RD_4, col='purple', is_text=True, custom_text='Point B')
        two_points = g_plot.current_points[1:]
        g_plot.current_points = []
        list_of_points = get_point_list(two_points, 5)
        for point in list_of_points:
            add_point(point, size=Glb.RD_3)

        vehicle_mesh = g_plot.vehicle_data.vehicle_mesh
        wheel_bottom_mesh = make_wheel_bottom_mesh(g_plot.vehicle_data)
        g_plot.vehicle_data.bottom_mesh = wheel_bottom_mesh

        vehicle_mesh.pos(HpF.sub_points(two_points[0], g_plot.vehicle_data.position))
        wheel_bottom_mesh.pos(HpF.sub_points(two_points[0], g_plot.vehicle_data.position))
        plt.render()
        # along_line_angle = HpF.get_xy_angle(two_points)

        whl_bottoms = wheel_bottom_mesh.points()
        avg_wheel_bottom = HpF.avg_points(whl_bottoms)
        # print('Angle = ', along_line_angle, ' around = ', avg_wheel_bottom)

        for i in range(0, 360):
            vehicle_mesh.rotate(1, [0, 0, 1], two_points[0])
            wheel_bottom_mesh.rotate(1, [0, 0, 1], two_points[0])
            plt.render()

        whl_r = g_plot.vehicle_data.wheel_radius
        veh_l = g_plot.vehicle_data.length
        g_plot.plotter_mode = Glb.IDEAL_PLT_MODE

        for sim_point1 in two_points:
            sim_point = HpF.add_points(sim_point1, [0, 0, 10])
            # print('Sim for ', sim_point)
            # print('Vehicle pos = ', g_plot.vehicle_data.position)
            vehicle_mesh.pos(HpF.sub_points(sim_point, g_plot.vehicle_data.position))
            wheel_bottom_mesh.pos(HpF.sub_points(sim_point, g_plot.vehicle_data.position))
            plt.render()
            close_meshes = []
            close_points = []
            max_height = 0
            ## Making the bottom intersection mesh
            whl_bottoms = wheel_bottom_mesh.points()
            # print('Wheel bottoms = ', whl_bottoms)
            for wi, whl_bottom in enumerate(whl_bottoms):
                close_point = find_closest_point(whl_bottom)
                ground_height = HpF.dist_xyz([close_point, whl_bottom])
                print(f'Dist {wi+1} = {ground_height}, point = ', close_point)
                if ground_height > max_height:
                    max_height = ground_height
                close_points.append(close_point)
                add_point(close_point, size=Glb.RD_4)

                close_mesh_points = cloud.closestPoint(close_point, radius=whl_r*1.5)
                mesh_i = vedo.delaunay2d(close_mesh_points).c('pink')
                close_meshes.append(mesh_i)
                plt.add(mesh_i)


            '''
                Find the intersection with single wheel first 
            '''
            on_ground = []
            move_down_by = 0.4096
            accuracy_req = 0.0003
            new_whl_mesh_pos = vehicle_mesh.pos()
            new_whl_bottom_pos = wheel_bottom_mesh.pos()
            print('Translation of vehicle along Z Axis ')
            total_translation_dist = 0
            while True:
                if total_translation_dist > (max_height + whl_r):
                    print('Translation out of range')
                    return
                new_whl_mesh_pos[2] -= move_down_by
                new_whl_bottom_pos[2] -= move_down_by
                vehicle_mesh.pos(new_whl_mesh_pos)
                wheel_bottom_mesh.pos(new_whl_bottom_pos)
                total_translation_dist += move_down_by
                plt.render()

                for wi, close_mesh in enumerate(close_meshes):
                    con_i = close_mesh.intersectWith(vehicle_mesh)
                    con_i.c('blue')
                    int_points = con_i.points()
                    if len(int_points) > 0:
                        on_ground.append(wi)
                        break
                if len(on_ground) > 0:
                    if move_down_by <= accuracy_req:
                        print('On ground = ', on_ground)
                        break
                    else:
                        new_whl_mesh_pos[2] += move_down_by
                        new_whl_bottom_pos[2] += move_down_by
                        vehicle_mesh.pos(new_whl_mesh_pos)
                        wheel_bottom_mesh.pos(new_whl_bottom_pos)
                        total_translation_dist -= move_down_by
                        move_down_by = move_down_by / 2.0
                        on_ground = []

            print('Moved down by ', total_translation_dist)
            whl_bottoms = wheel_bottom_mesh.points()

            '''
                Now rotate around that first touching wheel
            '''
            rot_index = [[0, 3], [1, 2], [2, 1], [3, 0]]
            wheel_num = on_ground[0]
            rot_axis = HpF.sub_points(whl_bottoms[rot_index[wheel_num][1]],
                                      whl_bottoms[rot_index[wheel_num][0]])
            per_axis = [1, 0 - (rot_axis[0] / rot_axis[1]), 0]
            st_rot_angle = 1.024
            rot_angle = st_rot_angle
            '''
                Dir testing of the Vehicle's rotation angle
            '''
            # Get initial distance
            whl_bottoms = wheel_bottom_mesh.points()
            dist_before_rotation = HpF.dist_xyz([whl_bottoms[rot_index[wheel_num][1]],
                                                 close_points[rot_index[wheel_num][1]]])
            ## Test the rotation with the angle
            vehicle_mesh.rotate(rot_angle, per_axis, whl_bottoms[wheel_num])
            wheel_bottom_mesh.rotate(rot_angle, per_axis, whl_bottoms[wheel_num])
            whl_bottoms = wheel_bottom_mesh.points()
            plt.render()

            ## Re-calculate the distance and check
            dist_after_rotation = HpF.dist_xyz([whl_bottoms[rot_index[wheel_num][1]],
                                                close_points[rot_index[wheel_num][1]]])
            if dist_after_rotation > dist_before_rotation:
                rot_angle = 0 - rot_angle
                print('Changed rotation direction')

            rot_accu_req = 0.01
            total_rotation = 0
            print('Rotate around one wheel')
            while True:
                if abs(total_rotation) > 90:
                    print('Error in simulation')
                    return
                whl_bottoms = wheel_bottom_mesh.points()
                vehicle_mesh.rotate(rot_angle, per_axis, whl_bottoms[wheel_num])
                wheel_bottom_mesh.rotate(rot_angle, per_axis, whl_bottoms[wheel_num])
                total_rotation += rot_angle
                plt.render()
                # print(rot_angle, ' -- dist = ',
                #       HpF.dist_xyz([whl_bottoms[rot_index[wheel_num][1]],
                #                     close_points[rot_index[wheel_num][1]]]))
                for wi, close_mesh in enumerate(close_meshes):
                    if wi == wheel_num:
                        continue
                    con_i = close_mesh.intersectWith(vehicle_mesh)
                    con_i.c('blue')
                    int_points = con_i.points()
                    if len(int_points) > 0:
                        # print('\n Found ', len(int_points), ' intersection points for wheel ', wi)
                        on_ground.append(wi)
                        break
                if len(on_ground) > 1:
                    if abs(rot_angle) > rot_accu_req:
                        whl_bottoms = wheel_bottom_mesh.points()
                        vehicle_mesh.rotate(0 - rot_angle, per_axis, whl_bottoms[wheel_num])
                        wheel_bottom_mesh.rotate(0 - rot_angle, per_axis, whl_bottoms[wheel_num])
                        total_rotation -= rot_angle
                        plt.render()
                        rot_angle = rot_angle / 2.0
                        on_ground = [wheel_num]
                    else:
                        print('On ground = ', on_ground, ' total rotation = ', total_rotation)
                        break

            '''
                And finally around two wheels
            '''
            rot_axis = HpF.sub_points(whl_bottoms[on_ground[0]],
                                      whl_bottoms[on_ground[1]])
            rot_angle = st_rot_angle

            rem_wheels = []
            for i in range(0, 4):
                if i not in on_ground:
                    rem_wheels.append(i)

            # Get initial distance
            whl_bottoms = wheel_bottom_mesh.points()

            dist_1 = HpF.dist_xyz([whl_bottoms[rem_wheels[0]], close_points[rem_wheels[0]]])
            dist_2 = HpF.dist_xyz([whl_bottoms[rem_wheels[1]], close_points[rem_wheels[1]]])
            # print('D1 = ', dist_1, ' and D2 = ', dist_2)

            ## Test the rotation with the angle
            vehicle_mesh.rotate(rot_angle, rot_axis, whl_bottoms[wheel_num])
            wheel_bottom_mesh.rotate(rot_angle, rot_axis, whl_bottoms[wheel_num])
            whl_bottoms = wheel_bottom_mesh.points()
            plt.render()

            ## Re-calculate the distance and check
            dist_11 = HpF.dist_xyz([whl_bottoms[rem_wheels[0]], close_points[rem_wheels[0]]])
            dist_22 = HpF.dist_xyz([whl_bottoms[rem_wheels[1]], close_points[rem_wheels[1]]])
            dist_111 = dist_1 - dist_11
            dist_222 = dist_2 - dist_22
            print('D1 diff = ', dist_111, ' and D2 diff = ', dist_222)

            # Diagonal wheels possible are 0, 3 or 1, 2 which both sum to 3
            if (rem_wheels[0] + rem_wheels[1]) != 3:
                if dist_111 < 0 and dist_222 < 0:
                    rot_angle = 0 - rot_angle
                    print('Invert rot angle')

            print('Rotate around 2 wheels ')
            total_rotation = 0
            while True:
                if abs(total_rotation) > 90:
                    print('Error in simulation')
                    return
                whl_bottoms = wheel_bottom_mesh.points()
                vehicle_mesh.rotate(rot_angle, rot_axis, whl_bottoms[wheel_num])
                wheel_bottom_mesh.rotate(rot_angle, rot_axis, whl_bottoms[wheel_num])
                total_rotation += rot_angle
                plt.render()
                # dist_1 = HpF.dist_xyz([whl_bottoms[rem_wheels[0]], close_points[rem_wheels[0]]])
                # dist_2 = HpF.dist_xyz([whl_bottoms[rem_wheels[1]], close_points[rem_wheels[1]]])
                # print(rot_angle, ' -- dist = ', dist_1, dist_2)
                for wi, close_mesh in enumerate(close_meshes):
                    if wi in on_ground:
                        continue
                    con_i = close_mesh.intersectWith(vehicle_mesh)
                    con_i.c('blue')
                    int_points = con_i.points()
                    if len(int_points) > 0:
                        # print('\n Found ', len(int_points), ' intersection points for wheel ', wi)
                        on_ground.append(wi)
                        break
                if len(on_ground) > 2:
                    if abs(rot_angle) > rot_accu_req:
                        whl_bottoms = wheel_bottom_mesh.points()
                        vehicle_mesh.rotate(0 - rot_angle, rot_axis, whl_bottoms[wheel_num])
                        wheel_bottom_mesh.rotate(0 - rot_angle, rot_axis, whl_bottoms[wheel_num])
                        total_rotation -= rot_angle
                        plt.render()
                        rot_angle = rot_angle / 2.0
                        on_ground = [on_ground[0], on_ground[1]]
                    else:
                        print('On ground = ', on_ground, ' total rotation = ', total_rotation)
                        break

            close_mesh_points = cloud.closestPoint(cpt, radius=veh_l*2)
            mesh_i = vedo.delaunay2d(close_mesh_points).c('pink')
            con_i = vehicle_mesh.intersectWith(mesh_i).c('red')
            print(con_i.points())
            plt.add(con_i)


def state_vehicle_2(cpt):
    global g_plot

    new_window = multiprocessing.Process(target=Intf.get_vehicle_data, args=(g_plot.out_q,))
    new_window.start()
    new_window.join()
    if not g_plot.out_q.empty():
        g_plot.vehicle_data = g_plot.out_q.get()
    else:
        return

    g_plot.vehicle_data.height = g_plot.vehicle_data.wheel_radius / 2.0
    g_plot.vehicle_data.position = HpF.add_points(cpt, [0, 0, 0])

    ''' Make vehicular body mesh and add it to the plot '''
    g_plot.vehicle_data.vehicle_mesh = make_vehicle_mesh(g_plot.vehicle_data)
    plt.add(g_plot.vehicle_data.vehicle_mesh)

    vehicle_pos = g_plot.vehicle_data.vehicle_mesh.pos()
    print('vehicle_pos = ', vehicle_pos)
    print('CPT = ', cpt)

    for i in range(0, 90):
        g_plot.vehicle_data.vehicle_mesh.rotate(1, [0, 0, 1], cpt)
        vehicle_pos = g_plot.vehicle_data.vehicle_mesh.pos()
        vehicle_org = g_plot.vehicle_data.vehicle_mesh.caption()
        print(vehicle_pos, vehicle_org)
        plt.render()

    plt.render()


def make_vehicle_mesh(vehicle_data: Intf.VehicleData) -> list[vedo.Mesh]:
    if not vehicle_data:
        print('Invalid Vehicle Data Entry')
    ''' Amount of offset to be added when rendering the vehicle can be defined here '''

    first_time_offset = 2.0
    veh_l = vehicle_data.length
    veh_f = vehicle_data.front_overhang
    veh_b = vehicle_data.back_overhang
    veh_w = vehicle_data.width
    veh_h = vehicle_data.height
    whl_r = vehicle_data.wheel_radius
    whl_w = vehicle_data.wheel_width

    veh_x = vehicle_data.position[0]
    veh_y = vehicle_data.position[1]
    veh_z = vehicle_data.position[2] + first_time_offset

    box_end_points = [
                    [veh_x - veh_l / 2.0, veh_y - veh_w / 2.0, veh_z + whl_r],  # left, bottom
                    [veh_x + veh_l / 2.0, veh_y - veh_w / 2.0, veh_z + whl_r],  # right, bottom
                    [veh_x - veh_l / 2.0, veh_y + veh_w / 2.0, veh_z + whl_r],  # left, top
                    [veh_x + veh_l / 2.0, veh_y + veh_w / 2.0, veh_z + whl_r]]  # right, top

    connections = []
    mesh_points = []
    bottom_x_adj = [-veh_b, veh_f, -veh_b, veh_f]
    for i in range(0, 4):
        mesh_points.append(HpF.add_points(box_end_points[i], [bottom_x_adj[i], 0, 0 - veh_h/2.0]))

    txt_obj = []
    for i in range(0, 4):
        mesh_points.append(HpF.add_points(box_end_points[i], [bottom_x_adj[i], 0, 0 + veh_h / 2.0]))
        txt_obj.append(vedo.Text3D(txt=f'{i + 1}_whl', s=0.3,
                                   pos=HpF.add_points(box_end_points[i], [0, 0, whl_r+0.1])))

    # num_pts = 60
    # for wi, whl_center in enumerate(box_end_points):
    #     side_angle = 0  # np.pi / 4
    #     whl_y_off = [-whl_h, -whl_h, whl_h, whl_h]
    #     for i in range(0, num_pts):
    #         ang = 360 / num_pts * i * np.pi / 180
    #         whl_rim_point_1 = [whl_center[0] + whl_r * np.math.cos(ang) * np.math.cos(side_angle),
    #                            whl_center[1] + whl_r * np.math.cos(ang) * np.math.sin(side_angle),
    #                            whl_center[2] + whl_r * np.math.sin(ang)]
    #         whl_rim_point_2 = [whl_center[0] + whl_r * np.math.cos(ang) * np.math.cos(side_angle),
    #                            whl_center[1] + whl_r * np.math.cos(ang) * np.math.sin(side_angle) + whl_y_off[wi],
    #                            whl_center[2] + whl_r * np.math.sin(ang)]
    #         whl_points.append(whl_rim_point_1)
    #         whl_points.append(whl_rim_point_2)
    #         connections.append([(i * 2 + 0) % (num_pts * 2) + wi * num_pts * 2,
    #                             (i * 2 + 1) % (num_pts * 2) + wi * num_pts * 2,
    #                             (i * 2 + 2) % (num_pts * 2) + wi * num_pts * 2])
    #         connections.append([(i * 2 + 1) % (num_pts * 2) + wi * num_pts * 2,
    #                             (i * 2 + 2) % (num_pts * 2) + wi * num_pts * 2,
    #                             (i * 2 + 3) % (num_pts * 2) + wi * num_pts * 2])
            # plt.add(vedo.Cylinder(whl_center, r=whl_r, height=whl_h, axis=(0, 1, 0)))
    # whl_points.extend(mesh_points)
    # offset = 4 * num_pts * 2

    offset = 0
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
    vehicle_mesh = vedo.Mesh([mesh_points, connections])
    vehicle_mesh.backcolor('orange4').color('orange').linecolor('black').linewidth(1)

    ## Not ignoring the wheel width effect
    whl_centers = [[veh_x - veh_l / 2.0, veh_y - (veh_w/2.0 - whl_w/2.0), veh_z + whl_r],  # left, bottom
                   [veh_x + veh_l / 2.0, veh_y - (veh_w/2.0 - whl_w/2.0), veh_z + whl_r],  # right, bottom
                   [veh_x - veh_l / 2.0, veh_y + (veh_w/2.0 + whl_w/2.0), veh_z + whl_r],  # left, top
                   [veh_x + veh_l / 2.0, veh_y + (veh_w/2.0 + whl_w/2.0), veh_z + whl_r]]  # right, top

    wheel_meshes = []
    for wi, whl_center in enumerate(whl_centers):
        wheel_mesh = vedo.Cylinder(pos=whl_center, r=whl_r, height=whl_w, axis=[0, 1, 0], res=24)
        wheel_meshes.append(wheel_mesh)

    return [vedo.merge(vehicle_mesh, txt_obj), vedo.merge(wheel_meshes)]


def mouse_track(event):
    global g_plot

    if not g_plot.tracking_mode:
        return

    # Track the mouse if a point has already been selected
    if not event.actor:
        # print('No actor found while tracking ... ')
        return

    mouse_point = event.picked3d

    if g_plot.plotter_mode == Glb.VEHICLE_RUNNER:
        close_mouse_point = find_closest_point(mouse_point)
        new_pos = HpF.sub_points(close_mouse_point, g_plot.vehicle_data.position)
        if g_plot.gp_int_state == 1:
            g_plot.vehicle_data.vehicle_mesh.pos(new_pos)
            plt.render()
        elif g_plot.gp_int_state == 2:
            if len(g_plot.plotted_trackers) > 0:
                plt.remove(g_plot.plotted_trackers.pop())
            add_ruler([g_plot.current_points[1], close_mouse_point], width=3, col='yellow', size=Glb.TEXT_SIZE)
            g_plot.vehicle_data.vehicle_mesh.pos(new_pos)
            plt.render()


    # For normal sloping related calculations #
    # Same functionality in len(g_plot.current_points) == 1 statement
    # if not g_plot.rectangle_mode:
    #     for line in g_plot.plotted_trackers:
    #         plt.remove(line)
    #     g_plot.plotted_trackers = []
    #     add_ruler([g_plot.current_points[0], mouse_point], width=3, col='red', size=TEXT_SIZE)
    #     update_text('text3', f'Dist: {dist_xyz(g_plot.current_points[0], mouse_point):.3f}')
    #     return

    elif g_plot.plotter_mode == Glb.RECTANGLE_MODE:
        if len(g_plot.current_points) == 2:
            rem_all_trackers()
            rect_points = HpF.get_rectangle([g_plot.current_points[0], g_plot.current_points[1], mouse_point])
            for i in range(0, 4):
                add_ruler([rect_points[i], rect_points[i - 1]], width=3, col='white', size=Glb.TEXT_SIZE)
            return

        # For the Rectangle Mode operation #
        if len(g_plot.current_points) == 1 or len(g_plot.current_points) == 4:
            if len(g_plot.plotted_trackers) > 0:
                plt.remove(g_plot.plotted_trackers.pop())
            add_ruler([g_plot.current_points[-1], mouse_point], width=3, col='yellow', size=Glb.TEXT_SIZE)
            update_text('text3', f'Dist: {HpF.dist_xyz([g_plot.current_points[-1], mouse_point]):.3f}')
            return

    elif g_plot.plotter_mode == Glb.SLOPE_AVG_MODE:
        # For the Slope Average operation #
        if len(g_plot.current_points) == 1:
            if len(g_plot.plotted_trackers) > 0:
                plt.remove(g_plot.plotted_trackers.pop())
            add_ruler([g_plot.current_points[0], mouse_point], width=3, col='yellow', size=Glb.TEXT_SIZE)
            update_text('text3', f'Dist: {HpF.dist_xyz([g_plot.current_points[0], mouse_point]):.3f}')
            return


# The get_line_of_points takes the two endpoints, then does its best to get the pt along the path of the line
# that are on the ground of the point cloud Does this by iterating through the pt that make up the line in
# space, then getting the closest point that is actually a part of the mesh to that point
def add_point(pos: list[float], size=Glb.RD_2, col='red', silent=True, is_text=False, custom_text=''):
    global g_plot
    new_point = vedo.Point(pos, r=size, c=col)  # Point to be added, default radius and default color
    plt.add(new_point)
    g_plot.plotted_points.append(new_point)
    if is_text or len(custom_text) > 0:
        if len(custom_text) == 0:
            custom_text = ','.join(['%.3f' % e for e in (HpF.sub_points(pos, g_plot.min_xyz))])
        add_text(text=custom_text, pos=pos, size=0.8, col=col)

    if not silent:
        print(f'Added point: {HpF.sub_points(pos, g_plot.min_xyz)}')
    return new_point


def add_text(text: str, pos: list[float], silent=True, size=1.0, col='floralwhite', keep=True):
    global g_plot
    pos[2] += 1
    new_txt = vedo.Text3D(txt=text, s=size, pos=pos, depth=0.1, alpha=1.0, c=col)
    plt.add([new_txt])
    if keep:
        g_plot.plotted_texts.append(new_txt)
    if not silent:
        print(f'Text Rendered at {HpF.sub_points(pos, g_plot.min_xyz)}')
    return new_txt


def add_line(points: list[list[float]], col='red', width=3, silent=True, elevation=0):
    global g_plot
    new_line = None
    if len(points) >= 2:
        new_line = vedo.Line([points[0][0], points[0][1], points[0][2] + (elevation * 0.04)],
                             [points[1][0], points[1][1], points[1][2] + (elevation * 0.04)],
                             lw=width, c=col, alpha=1.0)
        plt.add([new_line])
        g_plot.plotted_lines.append(new_line)
        if not silent:
            print(f'Added {col} line bw {HpF.sub_points(points[0], g_plot.min_xyz)} and '
                  f'{HpF.sub_points(points[1], g_plot.min_xyz)}')
    else:
        print('Invalid number of points')
    return new_line


def add_lines(points: list[list[float]], col='yellow', width=4, silent=True):
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


def add_ruler(points: list[list[float]], col='white', width=4, size=2):
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


def update_text(text_id: str, value: str, rel_pos=None, size=Glb.TEXT_SIZE):
    global text_objects
    if rel_pos is None:
        rel_pos = [5, 5, 5]
    if text_id in text_objects.keys():
        plt.remove(text_objects[text_id]['text'])
        rel_pos = text_objects[text_id]['pos']
    new_text = add_text(value, pos=g_plot.min_xyz + rel_pos, silent=True, size=size, keep=False)
    text_objects[text_id] = {
        'text': new_text,
        'pos': rel_pos
    }
    plt.add(new_text)


def print_point(point):
    print(','.join(['%.3f' % e for e in (point - g_plot.min_xyz)]))


# Get the average slope of from point to point for a specified number of pt on the line

def get_point_list(end_points: list[list[float]], num_points: int):
    global g_plot, cloud
    points_to_use = [end_points[0]]

    z_offset = 0
    x_unit = (end_points[1][0] - end_points[0][0]) / (num_points + 1)
    y_unit = (end_points[1][1] - end_points[0][1]) / (num_points + 1)
    cur_point = end_points[0]

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
    if bad_point_count > 0:
        print('Bad points = ', bad_point_count)

    if len(points_to_use) < 1:
        print('Error in point selection. Aborting')
        return []
    points_to_use.append(end_points[1])
    return points_to_use


def get_avg_slope(num_points: int):
    global g_plot, cloud, all_tasks
    update_text('text3', 'Enter num pt:')

    points_to_use = get_point_list(g_plot.current_points, num_points)

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


def my_camera_reset():
    plt.camera.SetPosition([2321420.115, 6926160.299, 995.694])
    plt.camera.SetFocalPoint([2321420.115, 6926160.299, 702.312])
    plt.camera.SetViewUp([0.0, 1.0, 0.0])
    plt.camera.SetDistance(293.382)
    plt.camera.SetClippingRange([218.423, 388.447])
    # plt.render()
    print('Camera Reset Done')


def rem_all_trackers():
    global g_plot, plt
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
    plt.fly_to(point)
    # plt.show(g_plot.show_ele_list, interactorStyle=0, bg='white', axes=1, zoom=1.0, interactive=True, camera=new_cam)


def button_func():
    print('Pressed')


vedo.settings.enable_default_keyboard_callbacks = False
plt = vedo.Plotter(pos=[0, 0], size=[800, 1080])
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
    file_names = Intf.get_file_names(req_files)
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
    # new_mesh = delaunay2d(cloud.points()).alpha(0.3).c('grey')  # Some new_mesh object with low alpha
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
    # print('Once the program launches, Use the following keymap:'
    #       '\n\t \'z\' or \'Z\'  for Slope mode'
    #       '\n\t \'v\' or \'V\'  for Vehicle Mode'
    #       '\n\t \'r\' or \'R\'  for Rectangle Mode'
    #       '\n\t \'u\' or \'z\'  for Resetting the plot'
    #       '\n\t \'c\' or \'z\'  for Clearing everything'
    #       '\n\t \'Esc\' to Close everything'

    bu = plt.addButton(
        button_func,
        pos=(0.1, 0.1),  # x,y fraction from bottom left corner
        states=["click to hide", "click to show"],
        c=["w", "w"],
        bc=["dg", "dv"],  # colors of states
        font="courier",  # arial, courier, times
        size=25,
        bold=True,
        italic=False,
    )

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
    plt.show(g_plot.show_ele_list, bg='white', axes=1, zoom=1.0, interactive=True,
             camera=cam)


def find_closest_point(point: list[float], num_retry=60, dist_threshold=0.2, aggressive=2.0):
    fact = 1.0
    aggressive = aggressive ** 0.1111  # 2^0.1111 ~= 1.08
    # dist_found = 0.0
    min_dist = 9999999.9
    closest_pt_yet = []
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
            if rt > (num_retry * 3 / 4):
                print('Found cp in ', rt, ' tries')
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
            if rt > (num_retry * 3 / 4):
                print('Found cp in inv dir ', rt, ' tries')
            return close_point

    print('Failed to find a close point for ', point, ', min dist = ', min_dist)
    return closest_pt_yet


class LocalPlotter:
    plotter_mode = Glb.IDEAL_PLT_MODE
    tracking_mode = False
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
    plotted_texts = []
    rect_points = []
    show_ele_list = []
    vehicle = vedo.Box()
    gp_int_state = 0
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
