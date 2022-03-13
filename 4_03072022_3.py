import os.path
from vedo import *
import vedo
import numpy as np
from datetime import datetime
import sys
import time
import csv
import dill
import concurrent.futures
import threading

RD_1 = 20
RD_2 = 15
RD_3 = 10
RD_4 = 8

TEXT_SIZE = 1
TEXT_SPACING = 2
SCALE_FACTOR = 0.2

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
def on_key_press(evt):
    global two_points, plt, slope_avg_mode, last_key_press, rectangle_mode, plotted_points, plotted_lines, tracker_lines
    last_key_press = evt.keyPressed
    if not initialized:
        initialize_text()

    if evt.keyPressed in ['c', 'C']:
        # clear pt and lines
        for point in plotted_points:
            plt.remove(point, render=True)
        for t_line in tracker_lines:
            plt.remove(t_line, render=True)
        for p_line in plotted_lines:
            plt.remove(p_line, render=True)
        plt.sliders = plt.actors = two_points = []
        plotted_points = plotted_lines = tracker_lines = []
        printc("==== Cleared all points on plot ====", c="r")
        for i in range(1, 6):
            update_text(f'text{i}', '')
        update_text('text4', 'Cleared everything on the plot')
    elif evt.keyPressed == 'Escape':
        plt.clear()
        exit()
    elif evt.keyPressed in ['z', 'Z']:
        # Enter slope average mode
        print("=== ENTER SLOPE AVG MODE ====")
        update_text('text5', 'Slope averaging is ON')
        slope_avg_mode = True
    elif evt.keyPressed in ['u', 'U']:
        reset_plot()
    elif evt.keyPressed == 't':
        my_camera_reset()
    # elif evt.keyPressed in ['R', 'r']:
    #     rectangle_mode = True
    # elif evt.keyPressed in [str(e) for e in range(0,9)]:
    #     handle_inp()


def initialize_text():
    global initialized
    update_text('text1', '', [2, -2 * TEXT_SPACING, 5])
    update_text('text2', 'SlopeAVG and Tracking: OFF', [2, -3 * TEXT_SPACING, 5])
    update_text('text3', '', [2, -4 * TEXT_SPACING, 5])
    update_text('text4', 'Press z to enter slope mode',
                [3, xyz_cloud.max_xyz[1] - xyz_cloud.min_xyz[1] + 3 * TEXT_SPACING, 5])
    update_text('text5', '', [3, xyz_cloud.max_xyz[1] - xyz_cloud.min_xyz[1] + 2 * TEXT_SPACING, 5])
    update_text('text6', '', [3, xyz_cloud.max_xyz[1] - xyz_cloud.min_xyz[1] + 1 * TEXT_SPACING, 5])
    initialized = True


def on_left_click(event):
    global two_points, last_pt, tracking_mode, slope_avg_mode, cloud
    global initialized, slider_selected, max_points, smooth_factor

    if not initialized:
        initialize_text()

    if event.picked3d is None:
        return

    if slider_selected:
        # Get actual pt
        plt.sliders = []
        plt.render()
        print(f'Number of pt on the line: {max_points}')
        update_text('text4', f'Please wait ...')
        get_avg_slope()
        slider_selected = False
        two_points = []

    if slope_avg_mode:
        cpt1 = vector(list(event.picked3d))
        cpt = cloud.closestPoint(cpt1)
        if dist_xy(cpt, cpt1) > 2:
            print('LONG DIST DETECTED bw ', cpt, ' and ', cpt1)
            return
        two_points.append(cpt)
        add_point(cpt, size=RD_1, col='red')
        if len(two_points) == 1:
            last_pt = cpt
            # Select the first point
            if not tracking_mode:
                print("Tracking is ON now ... ")
                update_text('text2', 'SopeAVG and Tracking: ON', )
                update_text('text4', 'Select 2nd point on map')
                tracking_mode = True
        elif len(two_points) == 2:
            # Select second point and connect them with a line
            # plt.removeCallback('MouseMove')
            tracking_mode = False
            slope_avg_mode = False
            update_text('text2', 'SlopeAVG: ON, Tracking: OFF')
            update_text('text3', '')
            for line in tracker_lines:
                plt.remove(line)
            add_line(two_points, width=2, col='white')
            max_points = int(round(dist_xyz(two_points[0], two_points[1]) / SCALE_FACTOR))
            plt.addSlider3D(
                slider_y,
                pos1=[xyz_cloud.min_xyz[0] + 5, xyz_cloud.max_xyz[1] + TEXT_SPACING, xyz_cloud.min_xyz[2] + 5],
                pos2=[xyz_cloud.max_xyz[0] - 5, xyz_cloud.max_xyz[1] + TEXT_SPACING, xyz_cloud.min_xyz[2] + 5],
                xmin=0, xmax=max_points,
                s=0.01, c="blue", t=1.5,
                title="Select a value for number of pt",
                showValue=False
            )
            update_text('text4', 'Select no of points on slider')
            update_text('text5', f'Max points = {max_points}, click anywhere on map to finish selection')
            all_objects['slider'] = plt.actors[-1:]
            smooth_factor = 0
            slider_selected = True


def dist_xyz(point1, point2):
    if len(point1) != 3 or len(point2) != 3:
        print('Bad Value of pt in dist_xyz')
        return None

    return sqrt((point1[0] - point2[0]) ** 2 +
                (point1[1] - point2[1]) ** 2 +
                (point1[2] - point2[2]) ** 2)


def dist_xy(point1, point2):
    if len(point1) < 2 or len(point1) < 2:
        print('Bad Value of pt in dist_xy')
        return None

    return sqrt((point1[0] - point2[0]) ** 2 +
                (point1[1] - point2[1]) ** 2)


def add_rectangle(points):
    if len(points) < 3:
        print('Insufficient points')
        return


def mouse_track(event):
    global two_points, tracking_mode, rectangle_mode, tracker_lines

    if not tracking_mode:
        return

    # Track the mouse if a point has already been selected
    if not event.actor:
        # print('No actor found while tracking ... ')
        return

    mouse_point = event.picked3d
    if not rectangle_mode:
        for line in tracker_lines:
            plt.remove(line)
        add_ruler([two_points[0], mouse_point], width=3, col='red', size=TEXT_SIZE)
        update_text('text3', f'Dist: {dist_xyz(last_pt, mouse_point):.3f}')
        return

    if len(two_points) == 1:
        for line in tracker_lines:
            plt.remove(line)
        add_ruler([two_points[0], mouse_point], width=3, col='yellow', size=TEXT_SIZE)
        update_text('text3', f'Dist: {dist_xyz(last_pt, mouse_point):.3f}')
        return

    if len(two_points) == 2:
        for line in tracker_lines:
            plt.remove(line)
        add_ruler([two_points[0], two_points[1]], width=3, col='yellow', size=TEXT_SIZE)
        # Calculating distance of new point from the line drawn:

        # add_ruler([mouse_point[0], ]], width=3, col='yellow', size=3)
        update_text('text3', f'Dist: {dist_xyz(last_pt, mouse_point):.3f}')
        return


# The get_line_of_points takes the two endpoints, then does its best to get the pt along the path of the line
# that are on the ground of the point cloud Does this by iterating through the pt that make up the line in
# space, then getting the closest point that is actually a part of the mesh to that point


def add_point(pos, size=RD_1, col='red', silent=False, is_text=False):
    new_point = Point(pos, r=size, c=col)  # Point to be added, default radius and default color
    plt.add([new_point])
    if is_text:
        pos2 = [pos[0], pos[1], pos[2] + 2]
        new_text = Text3D(txt=','.join(['%.3f' % e for e in (pos - xyz_cloud.min_xyz)]),
                          s=2, pos=pos2, depth=0.1, alpha=1.0, c='w')
        plt.add([new_text])

    # plt.render()
    if not silent:
        print(f'Added point: {pos - xyz_cloud.min_xyz}')
    plotted_points.append(new_point)
    return new_point


def add_text(text, pos, silent=False, size=2):
    pos[2] += 1
    tx1 = Text3D(txt=text, s=size, pos=pos, depth=0.1, alpha=1.0)
    plt.add([tx1])
    # plt.render()
    if not silent:
        print(f'Text Rendered at {pos - xyz_cloud.min_xyz}')
    return tx1


def add_line(points, col='red', width=5, silent=False):
    new_line = None
    if len(points) >= 2:
        new_line = Line([points[0][0], points[0][1], points[0][2] + 0.01],
                        [points[1][0], points[1][1], points[1][2] + 0.01],
                        lw=width, c=col, alpha=1.0)
        plt.add([new_line])
        # plt.render()
        if not silent:
            print(f'Added {col} line bw {points[0] - xyz_cloud.min_xyz} and {points[1] - xyz_cloud.min_xyz}')
    else:
        print('Invalid number of pt')
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
    global tracker_lines
    if len(points) >= 2:
        # distance = dist_xyz(points[0], points[1])
        # line_text = ''
        # if distance > 50:
        #     line_text = f'{dist_xyz(points[0], points[1]):.2f}'
        # elif distance > 25:
        #     line_text = f'{dist_xyz(points[0], points[1]):.1f}'
        start = [points[0][0], points[0][1], points[0][2] + 1]
        ended = [points[1][0], points[1][1], points[1][2] + 1]
        new_line = Ruler(start, ended, lw=width, c=col, alpha=1.0, s=size)
        plt.add([new_line])
        tracker_lines.append(new_line)
        return new_line
    else:
        print('Invalid number of pt')


def update_text(text_id, value, rel_pos=None, size=TEXT_SIZE):
    global all_objects
    if rel_pos is None:
        rel_pos = [5, 5, 5]
    if text_id in all_objects.keys():
        plt.remove(all_objects[text_id]['text'])
        rel_pos = all_objects[text_id]['pos']
    new_text = add_text(value, pos=xyz_cloud.min_xyz + rel_pos, silent=True, size=size)
    all_objects[text_id] = {
        'text': new_text,
        'pos': rel_pos
    }
    plt.add(new_text)


def print_point(point):
    print(','.join(['%.3f' % e for e in (point - xyz_cloud.min_xyz)]))


# Get the average slope of from point to point for a specified number of pt on the line
def get_avg_slope():
    global two_points, smooth_factor, max_points, cloud
    update_text('text3', 'Enter num pt:')
    if smooth_factor >= max_points:
        smooth_factor = max_points - 1

    if smooth_factor == 0:
        points_to_use = two_points
    else:
        x_unit = (two_points[1][0] - two_points[0][0]) / (smooth_factor + 1)
        y_unit = (two_points[1][1] - two_points[0][1]) / (smooth_factor + 1)
        cur_point = two_points[0]
        z_offset = 0
        points_to_use = []
        bad_point_count = made_better = 0
        acceptable_dist = 0.2
        for i in range(0, smooth_factor):
            new_approx_point = [cur_point[0] + x_unit, cur_point[1] + y_unit, cur_point[2] + z_offset]
            # add_point(new_approx_point, size=RD_4, col='white', silent=True)
            new_actual_point = cloud.closestPoint(new_approx_point)
            xy_dist_temp = dist_xy(new_approx_point, new_actual_point)
            if xy_dist_temp < acceptable_dist:
                points_to_use.append(new_actual_point)
                z_offset = new_actual_point[2] - new_approx_point[2]
            else:
                bad_point_count += 1
                new_approx_point = [cur_point[0] + x_unit * 1.1, cur_point[1] + y_unit * 1.1, cur_point[2] + z_offset]
                new_actual_points = cloud.closestPoint(new_approx_point, radius=acceptable_dist)
                if len(new_actual_points) > 1:
                    made_better += 1
                    points_to_use.append(new_actual_points[0])
                    z_offset = new_actual_points[0][2] - new_approx_point[2]
            cur_point = new_approx_point
        print('Bad points = ', bad_point_count)

        if len(points_to_use) < 2:
            print('Error in point selection. Aborting')
            return
        points_to_use.insert(0, two_points[0])
        points_to_use.append(two_points[1])
    # Loop through pt and plot them

    update_text('text3', f'Rendering {len(points_to_use)} pt')
    print(f'Rendering {len(points_to_use)} on map ', end='')
    st = '.'
    for p in points_to_use:
        add_point(p, size=RD_3, col='g', silent=True)
        update_text('text6', st)
        st += '.'
        print('.', end='')
    time.sleep(0.3)
    print(' Done!')
    update_text('text6', '')
    plotted_lines.extend(add_lines(points_to_use))
    slopes_bw_points = []
    # point1 = ', '.join(['%.3f' % e for e in points_to_use[0]])
    # print_text = ''

    total_slope = 0
    for pt in range(1, len(points_to_use)):
        # point2 = ','.join(['%.3f' % e for e in points_to_use[pt]])
        xy_dist = dist_xy(points_to_use[pt - 1], points_to_use[pt - 0])
        zz_dist = (points_to_use[pt - 1][2] - points_to_use[pt - 0][2])
        if xy_dist > 0.02:
            slope_xy = (zz_dist / xy_dist)
            total_slope += slope_xy
            slopes_bw_points.append({
                'X1': points_to_use[pt - 1][0],
                'Y1': points_to_use[pt - 1][1],
                'Z1': points_to_use[pt - 1][2],
                'X2': points_to_use[pt - 0][0],
                'Y2': points_to_use[pt - 0][1],
                'Z2': points_to_use[pt - 0][2],
                'Slope': slope_xy,
                'Distance': dist_xyz(points_to_use[pt - 1], points_to_use[pt - 0])
            })

        # print_text += point1 + ', ' + point2 + '\n'
        # point1 = point2

    print_text = 'X1, Y1, Z1, X2, Y2, Z2, Slope, Distance \n'
    print_text += '\n'.join(['%.3f, %.3f, %.3f, %.3f, %.3f, %.3f, %.3f, %.3f' %
                             (e['X1'] - xyz_cloud.min_xyz[0], e['Y1'] - xyz_cloud.min_xyz[1],
                              e['Z1'] - xyz_cloud.min_xyz[2],
                              e['X2'] - xyz_cloud.min_xyz[0], e['Y2'] - xyz_cloud.min_xyz[1],
                              e['Z2'] - xyz_cloud.min_xyz[2],
                              e['Slope'], e['Distance']) for e in slopes_bw_points])

    update_text('text5', 'Press z again to enter slope mode')
    print(print_text)

    # slope_2 = {
    #     'X1': [],
    #     'Y1': [],
    #     'Z1': [],
    #     'X2': [],
    #     'Y2': [],
    #     'Z2': [],
    #     'Slope': []
    # }
    # for e in slopes_bw_points:
    #     for key in slope_2.keys():
    #         slope_2[key].append(e[key])

    csv_file = f'Slope_{datetime.now().strftime("%Y%m%d%H%M%S")}.csv'
    try:
        with open(csv_file, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=[e for e in slopes_bw_points[0].keys()])
            writer.writeheader()
            for data in slopes_bw_points:
                writer.writerow(data)
    except IOError:
        print("I/O error")

    result = total_slope / len(slopes_bw_points)

    # pd_slope_array.to_csv(f'calc_slope_{result}.csv')
    print(f'Average slope between {len(points_to_use)} pt = {result}, \n List of slopes for indices: ')
    update_text('text4', f'Avg slope = {result:.3f}')
    # print(pd_slope_array)
    return result


def reset_plot():
    global two_points, tracking_mode, initialized, cloud
    print('Removing all objects from map')
    plt.clear()
    plt.axes = 1
    # plt.add([mesh, cloud]).render()
    plt.add([cloud]).render()
    update_text('text2', 'SlopeAVG and Tracking: OFF')
    update_text('text3', '')
    update_text('text4', '')
    initialized = False
    two_points = []
    tracking_mode = False


# def get_list(num_elements, arr):
#     arr_len = len(arr)
#     return [arr[(i * arr_len // num_elements) + (arr_len // (2 * num_elements))] for i in range(num_elements)]


def button_action(button):
    global slope_avg_mode
    slope_avg_mode = (not slope_avg_mode)
    button.switch()  # change to next status


def my_camera_reset():
    plt.camera.SetPosition([2321420.115, 6926160.299, 995.694])
    plt.camera.SetFocalPoint([2321420.115, 6926160.299, 702.312])
    plt.camera.SetViewUp([0.0, 1.0, 0.0])
    plt.camera.SetDistance(293.382)
    plt.camera.SetClippingRange([218.423, 388.447])
    # plt.render()
    print('Camera Reset Done')


def slider_y(widget, event):
    global smooth_factor
    value = widget.GetRepresentation().GetValue()
    value = (value ** 1.5) / (max_points ** 0.5)
    smooth_factor = round(value)
    update_text('text4', f'{round(smooth_factor)} points selected')
    # update_text('text5', f'Max points = {max_points}')


def handle_timer(event):
    print('To do list of tasks here')


class XYZCloud:
    min_xyz: []
    max_xyz: []


''' All the global variables declared '''
two_points = []
last_key_press = None
tracker_lines = []
plotted_points = []
plotted_lines = []
slider_selected = False
smooth_factor = 0
cloud: vedo.io
plt: vedo.Plotter
xyz_cloud = XYZCloud()

slope_avg_mode = False
tracking_mode = False
rectangle_mode = False

last_pt = [0, 0, 0]
max_points = 0
initialized = False
all_objects = {
}
''' End of variable declarations '''


def main():
    # settings.enableDefaultKeyboardCallbacks = False
    global cloud, plt, xyz_cloud

    print(f'Program started :')
    start_time = time.time()
    if len(sys.argv) < 2:
        # filename = 'Hump_1.ply'
        filename = 't3.ply'
        print(f'No file specified, Using the default file name: {filename}')
    else:
        filename = sys.argv[1]
        if not os.path.isfile(filename):
            print('File ', filename, ' does not exist')

    cloud = load(filename).pointSize(3.5)
    print(f'Loaded file {filename} in {time.time() - start_time} sec')

    start_time = time.time()
    cloud_center = cloud.centerOfMass()  # Center of mass for the whole cloud

    print(f'Center of mass = {cloud_center}, calc in {time.time() - start_time} sec')

    xyz_cloud.min_xyz = np.min(cloud.points(), axis=0)
    xyz_cloud.max_xyz = np.max(cloud.points(), axis=0)
    # dif_xyz = np.subtract(cloud.points(), xyz_cloud.min_xyz)
    print(xyz_cloud.max_xyz - xyz_cloud.min_xyz)

    start_time = time.time()
    # mesh = delaunay2D(cloud.points()).alpha(0.3).c('grey')  # Some mesh object with low alpha
    # dump_filename = filename+'__mesh_dump.txt'
    # if os.path.isfile(dump_filename) and os.path.getsize(dump_filename) > 10000:
    #     print('Found dump file from previous iteration, reusing...')
    #     file_d = open(dump_filename, 'wb')
    #     mesh = dill.load(file_d)
    #     file_d.close()
    # else:
    #     mesh = delaunay2D(cloud.points()).alpha(0.3).c('grey')  # Some mesh object with low alpha
    #     file_d = open(dump_filename, 'wb')
    #     dill.dump(mesh, file_d)
    #     file_d.close()
    cloud.legend('My cloud map')
    print(f'Mesh created in {time.time() - start_time} sec for {len(cloud.points())} points')

    plt = Plotter(pos=[0, 0], size=[800, 1080])
    plt.addCallback('KeyPress', on_key_press)
    plt.addCallback('LeftButtonPress', on_left_click)
    plt.addCallback('MouseMove', mouse_track)
    plt.addCallback('timer', handle_timer)

    print('Once the program launches, Use the following keymap:'
          '\t\n \'z\'   for starting slope mode'
          '\t\n \'c\'   to clear everything'
          '\t\n \'u\'   to reset the plot'
          '\t\n \'Esc\' to close the plot'
          '\t\n \'h\'   for the default help menu'
          )

    cam = dict(pos=(cloud_center[0], cloud_center[1], cloud_center[2] + 100),
               focalPoint=cloud_center,
               viewup=(0, 1.00, 0),
               clippingRange=(218.423, 388.447),
               viewAngle=60
               )
    plt.show([cloud], interactorStyle=0, bg='white', axes=1, zoom=1.5, interactive=True, camera=cam)
    print('Finished execution')
    exit()


if __name__ == "__main__":
    main()
