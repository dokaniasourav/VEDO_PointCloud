from vedo import *
import numpy as np
from datetime import datetime
from pandas import DataFrame
import math
import sys
import time
import csv

RD_1 = 20
RD_2 = 15
RD_3 = 10

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
    global two_points, plt, slope_avg_mode, last_key_press, rectangle_mode
    last_key_press = evt.keyPressed
    if evt.keyPressed in ['c', 'C']:
        # clear pt and lines
        plt.remove(plt.actors, render=True)
        plt.sliders = []
        plt.actors = []
        two_points = []
        plt.render()
        printc("==== Cleared all pt ====", c="r")
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


def on_left_click(event):
    global first_pt, second_pt, two_points, last_pt, tracking_mode, slope_avg_mode
    global initialized, slider_selected, line_of_points, smooth_factor

    if not initialized:
        update_text('text1', '', [2, -15, 5])
        update_text('text2', 'SlopeAVG and Tracking: OFF', [2, -10, 5])
        update_text('text3', '', [2, -20, 5])
        update_text('text4', 'Press z to enter slope mode',
                    [3, max_xyz[1] - min_xyz[1] + 15, 5])
        update_text('text5', '', [3, max_xyz[1] - min_xyz[1] + 10, 5])
        update_text('text6', '', [3, max_xyz[1] - min_xyz[1] + 5, 5])
        # add_point(max_xyz, col='red', is_text=True)
        initialized = True
        # plt.addButton(button_action, pos=(min_xyz[0] + 5, min_xyz[1] + 5, min_xyz[2] + 2),
        #               states=["Start drawing line", "End"],
        #               c=["w", "y"], bc=["dg", "dv"],  # colors of states
        #               size=50, bold=True)
        # plt.render()

    if event.picked3d is None:
        return

    if slider_selected:
        # Get actual pt
        plt.sliders = []
        plt.render()
        print(f'Number of pt on the line: {len(line_of_points)}')
        update_text('text4', f'Please wait ...')
        get_avg_slope()
        slider_selected = False
        two_points = []
        line_of_points = []

    if slope_avg_mode:
        cpt = vector(list(event.picked3d))
        two_points.append(cpt)
        add_point(cpt, size=RD_1, col='red')
        if len(two_points) == 1:
            last_pt = cpt
            # Select the first point
            first_pt = np.array([cpt[0], cpt[1], cpt[2]])
            if not tracking_mode:
                # plt.addCallback('MouseMove', mouse_track)
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
            for line in tracker_line:
                plt.remove(line)
            add_line(two_points, width=2, col='white')
            second_pt = np.array([cpt[0], cpt[1], cpt[2]])
            set_line_of_points(two_points)
            plt.addSlider3D(
                slider_y,
                pos1=[min_xyz[0] + 10, max_xyz[1] + 5, min_xyz[2] + 10],
                pos2=[max_xyz[0] - 15, max_xyz[1] + 5, min_xyz[2] + 10],
                xmin=0, xmax=len(line_of_points),
                s=0.04, c="blue",
                title="Select a value for number of pt",
                showValue=False
            )
            update_text('text4', 'Select no of points on slider')
            update_text('text5', f'Max points = {len(line_of_points)}, click anywhere on map to finish selection')
            all_objects['slider'] = plt.actors[-1:]
            smooth_factor = 0
            slider_selected = True

        # plt.interactive = True
        # plt.render()

        # except Exception as e:
        #     # The pt selected by the clicks must be already existing pt
        #     print(f'Error occurred: {e}')

    # if rectangle_mode:
    #     cpt = vector(list(event.picked3d))
    #     add_point(cpt)
    #     two_points.append(cpt)
    #     if len(two_points) == 1:
    #         update_text('text3', 'Add next 2 points')
    #         if not tracking_mode:
    #             update_text('text2', 'Tracking: ON')
    #             update_text('text4', 'Select 2nd point')
    #             tracking_mode = True
    #     elif len(two_points) == 2:
    #         update_text('text4', 'Add one more point')


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
    global two_points, tracking_mode, rectangle_mode, tracker_line

    if not tracking_mode:
        return

    # Track the mouse if a point has already been selected
    if not event.actor:
        # print('No actor found while tracking ... ')
        return

    mouse_point = event.picked3d
    if not rectangle_mode:
        for line in tracker_line:
            plt.remove(line)
        add_ruler([two_points[0], mouse_point], width=3, col='red', size=3)
        update_text('text3', f'Dist: {dist_xyz(last_pt, mouse_point):.3f}')
        return

    if len(two_points) == 1:
        for line in tracker_line:
            plt.remove(line)
        add_ruler([two_points[0], mouse_point], width=3, col='yellow', size=3)
        update_text('text3', f'Dist: {dist_xyz(last_pt, mouse_point):.3f}')
        return

    if len(two_points) == 2:
        for line in tracker_line:
            plt.remove(line)
        add_ruler([two_points[0], two_points[1]], width=3, col='yellow', size=3)
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
        new_text = Text3D(txt=','.join(['%.3f' % e for e in (pos - min_xyz)]),
                          s=2, pos=pos2, depth=0.1, alpha=1.0, c='w')
        plt.add([new_text])

    # plt.render()
    if not silent:
        print(f'Added point: {pos - min_xyz}')
    return new_point


def add_text(text, pos, silent=False, size=2):
    pos[2] += 1
    tx1 = Text3D(txt=text, s=size, pos=pos, depth=0.1, alpha=1.0)
    plt.add([tx1])
    # plt.render()
    if not silent:
        print(f'Text Rendered at {pos - min_xyz}')
    return tx1


def add_line(points, col='red', width=5, silent=False):
    new_line = None
    if len(points) >= 2:
        new_line = Line(points[0], points[1], closed=False, lw=width, c=col, alpha=1.0)
        plt.add([new_line])
        # plt.render()
        if not silent:
            print(f'Added {col} line bw {points[0] - min_xyz} and {points[1] - min_xyz}')
    else:
        print('Invalid number of pt')
    return new_line


def add_lines(points, col='yellow', width=4, silent=True):
    if len(points) < 2:
        print('Invalid number of pt')
        return None
    new_lines = []
    for i in range(1, len(points)):
        new_lines.append(add_line([points[i - 1], points[i]], col=col, width=width, silent=silent))
    return new_lines


def add_ruler(points, col='white', width=5, size=2):
    global tracker_line
    if len(points) >= 2:
        line_text = f'Dist: {dist_xyz(points[0], points[1]):.2f}'
        start = [points[0][0], points[0][1], points[0][2] + 1]
        ended = [points[1][0], points[1][1], points[1][2] + 1]
        new_line = Ruler(start, ended, lw=width, c=col, alpha=1.0, s=size, label=line_text)
        plt.add([new_line])
        tracker_line.append(new_line)
        return new_line
    else:
        print('Invalid number of pt')


def update_text(text_id, value, rel_pos=None, size=3):
    global all_objects
    if rel_pos is None:
        rel_pos = [5, 5, 5]
    if text_id in all_objects.keys():
        plt.remove(all_objects[text_id]['text'])
        rel_pos = all_objects[text_id]['pos']
    new_text = add_text(value, pos=min_xyz + rel_pos, silent=True, size=size)
    all_objects[text_id] = {
        'text': new_text,
        'pos': rel_pos
    }
    plt.add(new_text)


def print_point(point, acc=2):
    print(','.join([f'%ds.{acc}f' % e for e in (point - min_xyz)]))


# noinspection DuplicatedCode
def set_line_of_points(point_values):
    global line_of_points
    # Calculates a unit of direction along line
    x_len = point_values[1][0] - point_values[0][0]
    y_len = point_values[1][1] - point_values[0][1]

    # magnitude is the distance in XY plane
    magnitude = math.sqrt((x_len ** 2) + (y_len ** 2))
    x_unit = x_len / magnitude
    y_unit = y_len / magnitude

    # print(f'X unit = {x_unit} and Y unit = {y_unit}')
    bad_point_count = 0
    made_better = 0
    z_offset = 0
    cur_point = point_values[0]
    line_of_points = [cur_point]
    # Iterate through pt in line and save them in list
    while round(cur_point[0]) != round(point_values[1][0]) and \
            round(cur_point[1]) != round(point_values[1][1]):
        new_approx_point = [cur_point[0] + x_unit, cur_point[1] + y_unit, cur_point[2] + z_offset]
        new_actual_point = cloud.closestPoint(cur_point)
        xyz_dist_temp = dist_xyz(cur_point, new_actual_point)
        if 4 > xyz_dist_temp > 0.001:
            line_of_points.append(new_actual_point)
            z_offset = new_actual_point[2] - new_approx_point[2]
        else:
            # print(f'Distance: {xyz_dist_temp}, for point {new_approx_point}. Got {new_actual_point}')
            bad_point_count += 1
            new_actual_points = cloud.closestPoint(cur_point, radius=2, N=1)
            if len(new_actual_points) > 1:
                if 4 > dist_xyz(cur_point, new_actual_points[0]) > 0.001:
                    made_better += 1
                    line_of_points.append(new_actual_points[0])
                    z_offset = new_actual_points[0][2] - new_approx_point[2]

        cur_point = new_approx_point
    print(f'Got {bad_point_count} bad points, replaced {made_better}')
    # print(f'Get line of pt, Input = {point_values}')
    # for i in range(1, len(line_pts)):
    #     print(f' XX = {(line_pts[i][0] - line_pts[i - 1][0]):.2f},'
    #           f' YY = {(line_pts[i][1] - line_pts[i - 1][1]):.2f},'
    #           f' ZZ = {(line_pts[i][2] - line_pts[i - 1][2]):.2f}')


# Get the average slope of from point to point for a specified number of pt on the line
def get_avg_slope():
    global first_pt, second_pt, smooth_factor, line_of_points

    update_text('text3', 'Enter num pt:')
    if smooth_factor >= len(line_of_points):
        smooth_factor = len(line_of_points) - 1

    if smooth_factor == 0:
        pts_to_use = [first_pt, second_pt]
    else:
        step_factor = round(len(line_of_points) / (smooth_factor + 1))
        pts_to_use = line_of_points[0::step_factor]
        # print(f'Smooth factor = {smooth_factor}, steps = {step_factor}')
        if len(pts_to_use) < 2:
            print('Error in point selection. Aborting')
            return
        pts_to_use.append(second_pt)
    # Loop through pt and plot them

    update_text('text3', f'Rendering {len(pts_to_use)} pt')
    print(f'Rendering {len(pts_to_use)} on map ', end='')
    st = '.'
    for p in pts_to_use:
        add_point(p, size=RD_3, col='g', silent=True)
        update_text('text6', st)
        st += '.'
        print('.', end='')
    print(' Done!')
    update_text('text6', '')
    add_lines(pts_to_use)
    slopes_bw_points = []

    for pt in range(1, len(pts_to_use)):
        slopes_bw_points.append({
            'X1': pts_to_use[pt - 1][0],
            'Y1': pts_to_use[pt - 1][1],
            'Z1': pts_to_use[pt - 1][2],
            'X2': pts_to_use[pt - 0][0],
            'Y2': pts_to_use[pt - 0][1],
            'Z2': pts_to_use[pt - 0][2],
            'Slope': math.nan
        })

    total_slope = 0
    for i, pt in enumerate(slopes_bw_points):
        # Range should be define by net distance, not XY maximum
        xy_dist = math.sqrt(((pt['X1'] - pt['X2']) ** 2) + ((pt['Y1'] - pt['Y2']) ** 2))
        z_dist = abs(pt['Z1'] - pt['Z2'])
        if xy_dist == 0:
            xy_dist = 0.001
        slopes_bw_points[i]['Slope'] = (z_dist / xy_dist)
        total_slope += (z_dist / xy_dist)

    print_text = 'X1, Y1, Z1, X2, Y2, Z2, Slope \n'
    print_text += '\n'.join(['%.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f' %
                             (e['X1'], e['Y1'], e['Z1'], e['X2'], e['Y2'], e['Z2'], e['Slope'])
                             for e in slopes_bw_points])

    update_text('text5', 'Press z again to enter slope mode')
    print(print_text)

    slope_2 = {
        'X1': [],
        'Y1': [],
        'Z1': [],
        'X2': [],
        'Y2': [],
        'Z2': [],
        'Slope': []
    }
    for e in slopes_bw_points:
        for key in slope_2.keys():
            slope_2[key].append(e[key])

    csv_file = f'Slope_{datetime.now().strftime("%Y%m%d%H%M%S")}.csv'
    try:
        with open(csv_file, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=['X1', 'Y1', 'Z1', 'X2', 'Y2', 'Z2', 'Slope'])
            writer.writeheader()
            for data in slopes_bw_points:
                writer.writerow(data)
    except IOError:
        print("I/O error")

    result = total_slope / len(slopes_bw_points)

    # pd_slope_array.to_csv(f'calc_slope_{result}.csv')
    print(f'Average slope between {len(pts_to_use)} pt = {result}, \n List of slopes for indices: ')
    update_text('text4', f'Avg slope = {result:.3f}')
    # print(pd_slope_array)
    return result


def reset_plot():
    global two_points, tracking_mode
    print('Removing all objects from map')
    # plt.removeCallback('MouseMove')
    plt.clear()
    plt.axes = 1
    plt.add([mesh, cloud]).render()
    update_text('text2', 'SlopeAVG and Tracking: OFF')
    update_text('text3', '')
    update_text('text4', '')
    two_points = []
    tracking_mode = False


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
    # value = (value*value)/len(line_of_points)
    smooth_factor = round(value)
    update_text('text4', f'{round(smooth_factor)} points selected')
    # update_text('text5', f'Max points = {len(line_of_points)}')


''' All the global variables declared '''
two_points = []
last_key_press = None
tracker_line = []
slider_selected = False
smooth_factor = 0
first_pt = None
second_pt = None

slope_avg_mode = False
tracking_mode = False
rectangle_mode = False

last_pt = [0, 0, 0]
line_of_points = []
initialized = False
all_objects = {
}
''' End of variable declarations '''

# settings.enableDefaultKeyboardCallbacks = False

print(f'Program started :')
start_time = time.time()
if len(sys.argv) < 2:
    filename = 'Hump_1.ply'
    print(f'No file specified, Using the default file name: {filename}')
else:
    filename = sys.argv[1]

cloud = load(filename).pointSize(3.5)
print(f'Loaded file {filename} in {time.time() - start_time} sec')

start_time = time.time()
cloud_center = cloud.centerOfMass()  # Center of mass for the whole cloud

print(f'Center of mass = {cloud_center}, calc in {time.time() - start_time} sec')

min_xyz = np.min(cloud.points(), axis=0)
max_xyz = np.max(cloud.points(), axis=0)
dif_xyz = np.subtract(cloud.points(), min_xyz)

cloud.legend('My cloud map')
start_time = time.time()
mesh = delaunay2D(cloud.points()).alpha(0.3).c('grey')  # Some mesh object with low alpha
print(f'Mesh created in {time.time() - start_time} sec for {len(cloud.points())} points')

cloud_center_1 = (cloud_center[0], cloud_center[1], cloud_center[2] + 450)
# cloud_center_2 = [cloud_center[0], cloud_center[1], cloud_center[2]+50]
cam = dict(pos=cloud_center_1,
           focalPoint=cloud_center,
           viewup=(0, 1.00, 0),
           # distance=293.382,
           clippingRange=(218.423, 388.447))

plt = Plotter(pos=[0, 0], size=[500, 1080])
plt.addCallback('KeyPress', on_key_press)
plt.addCallback('LeftButtonPress', on_left_click)
plt.addCallback('MouseMove', mouse_track)
print('Once the program launches, Use the following keymap:'
      '\t\n \'z\'   for starting slope mode'
      '\t\n \'c\'   to clear everything'
      '\t\n \'u\'   to reset the plot'
      '\t\n \'Esc\' to close the plot'
      '\t\n \'h\'   for the default help menu'
      )
plt.show([mesh, cloud], interactorStyle=0, bg='white', axes=1, zoom=1.5, interactive=True)  # , camera=cam)

print('Finished execution')
exit()
