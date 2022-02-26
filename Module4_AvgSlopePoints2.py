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

'''Get average slop of points along a path: 

1. Select 'z' to enter slope avg mode 
2. Select an existing point to be the origin
3. Your mouse will be tracked at this point, and you can click another point to determine the line which 
   you would like to get points from 
4. You will be asked how many points you will want to contribute to the average 
   slope, and you can specify an number less than the number of available points, or select all 
5. Now the points used to calculate the average will be shown in yellow, and in the terminal it will print the average 
   slope along their connected line '''


# Constantly checking if any meaningful key is selected
def on_key_press(evt):
    global two_points, line, plt, slope_avg_mode
    printc(f'{evt.keyPressed} pressed: ')
    if evt.keyPressed in ['c', 'C']:
        # clear points and lines
        plt.remove([two_points, line], render=True)
        two_points = []
        line = None
        printc("==== Cleared all points ====", c="r")
    elif evt.keyPressed == 'Escape':
        plt.clear()
        exit()
    elif evt.keyPressed  in ['z', 'Z']:
        # Enter slope average mode
        print("========ENTER SLOPE AVG MODE========")
        update_text('text1', 'SlopeAVG: ON')
        slope_avg_mode = True
    elif evt.keyPressed in ['u', 'U']:
        reset_plot()
    elif evt.keyPressed == 't':
        my_camera_reset()
    # elif evt.keyPressed in [str(e) for e in range(0,9)]:
    #     handle_inp()


def on_left_click(event):
    global first_pt, second_pt, two_points, line, last_pt, tracking_mode, slope_avg_mode, initialized

    if not initialized:
        update_text('text1', 'SlopeAVG: OFF', [2, 5, 5])
        update_text('text2', 'Tracking: OFF', [2, 10, 5])
        update_text('text3', '', [2, 15, 5])
        update_text('text4', '_________', [max_xyz[0], max_xyz[1], min_xyz[2]])
        add_point(max_xyz, col='red', is_text=True)
        initialized = True
        # plt.addButton(button_action, pos=(min_xyz[0] + 5, min_xyz[1] + 5, min_xyz[2] + 2),
        #               states=["Start drawing line", "End"],
        #               c=["w", "y"], bc=["dg", "dv"],  # colors of states
        #               size=50, bold=True)
        # plt.render()

    if event.picked3d is None:
        return

    if slope_avg_mode:
        cpt = vector(list(event.picked3d))  # Make a vector of list, IDK why
        two_points.append(cpt)
        add_point(cpt, size=RD_1, col='red')
        if len(two_points) == 1:
            last_pt = cpt

            # Select the first point
            first_pt = np.array([cpt[0], cpt[1], cpt[2]])
            print("Tracking started ... ")
            if not tracking_mode:
                plt.addCallback('MouseMove', mouse_track)
                update_text('text2', 'Tracking: ON', )
                update_text('text3', 'Select 2nd point')
                tracking_mode = True
        elif len(two_points) == 2:
            # Select second point and connect them with a line
            plt.removeCallback('MouseMove')
            tracking_mode = False
            slope_avg_mode = False
            update_text('text1', 'SlopeAVG: OFF')
            update_text('text2', 'Tracking: OFF')
            update_text('text3', '')
            plt.remove(tracker_line)
            add_line(two_points, width=2, col='white')
            second_pt = np.array([cpt[0], cpt[1], cpt[2]])
            # Get actual points
            point_list = get_line_of_points(two_points)
            print(f'Number of points on the line: {len(point_list)} bw {two_points}')
            # for pt in point_list:
            #     print(pt)
                # print('(', ', '.join(['%.2f' % e for e in (pt - min_xyz)]), ')')

            # plt.addSlider3D(
            #     slider_y,
            #     pos1=[min_xyz[0] + 5, min_xyz[1], min_xyz[2] + 10],
            #     pos2=[max_xyz[0] - 5, min_xyz[1], min_xyz[2] + 10],
            #     xmin=0,
            #     xmax=len(point_list),
            #     s=0.04,
            #     c="r",
            #     title="Select a value for number of points",
            # )

            avg_slope_on_line = get_avg_slope(point_list)  # Get the average slope of points
            print(f'Average slope of line: {avg_slope_on_line}')
            update_text('text4', f'Slope: {avg_slope_on_line:.3f}\n'
                                 f'Distance {dist_xyz(two_points[0], two_points[1]):.3f}')
            two_points = []

        plt.interactive = True
        plt.render()

        # except Exception as e:
        #     # The points selected by the clicks must be already existing points
        #     print(f'Error occurred: {e}')


def dist_xyz(point1, point2):
    if len(point1) != 3 or len(point2) != 3:
        print('Bad Value of points in dist_xyz')
        return None

    return sqrt((point1[0] - point2[0]) ** 2 +
                    (point1[1] - point2[1]) ** 2 +
                    (point1[2] - point2[2]) ** 2)


def dist_xy(point1, point2):
    if len(point1) < 2 or len(point1) < 2:
        print('Bad Value of points in dist_xy')
        return None

    return sqrt((point1[0] - point2[0]) ** 2 +
                (point1[1] - point2[1]) ** 2)


def mouse_track(event):
    global last_pt

    # Track the mouse if a point has already been selected
    if not event.actor:
        # print('No actor found while tracking ... ')
        return

    mouse_point = event.picked3d
    add_ruler([last_pt, mouse_point], width=3, col='red', size=3)
    update_text('text3', f'Dist: {dist_xyz(last_pt, mouse_point):.3f}')
    return


# The get_line_of_points takes the two endpoints, then does its best to get the points along the path of the line
# that are on the ground of the point cloud Does this by iterating through the points that make up the line in
# space, then getting the closest point that is actually a part of the mesh to that point

def add_point(pos, size=RD_1, col='red', silent=False, is_text=False):
    new_point = Point(pos, r=size, c=col)  # Point to be added, default radius and default color
    plt.add([new_point])
    if is_text:
        pos2 = [pos[0], pos[1], pos[2] + 2]
        new_text = Text3D(txt=','.join(['%.2f' % e for e in (pos - min_xyz)]),
                          s=2, pos=pos2, depth=0.1, alpha=1.0, c='w')
        plt.add([new_text])

    plt.render()
    if not silent:
        print(f'Added point: {pos - min_xyz}')
    return new_point


def add_text(text, pos, silent=False, size=2):
    pos[2] += 1
    tx1 = Text3D(txt=text, s=size, pos=pos, depth=0.1, alpha=1.0)
    plt.add([tx1])
    plt.render()
    if not silent:
        print(f'Text Rendered at {pos - min_xyz}')
    return tx1


def add_line(points, col='red', width=5, silent=False):
    new_line = None
    if len(points) >= 2:
        new_line = Line(points[0], points[1], closed=False, lw=width, c=col, alpha=1.0)
        plt.add([new_line])
        plt.render()
        if not silent:
            print(f'Added {col} line bw {points[0] - min_xyz} and {points[1] - min_xyz}')
    else:
        print('Invalid number of points')
    return new_line


def add_lines(points, col='yellow', width=4, silent=True):
    if len(points) < 2:
        print('Invalid number of points')
        return None
    new_lines = []
    for i in range(1, len(points)):
        new_lines.append(add_line([points[i-1], points[i]], col=col, width=width, silent=silent))
    return new_lines


def add_ruler(points, col='white', width=5, size=2):
    global tracker_line
    if len(points) >= 2:
        plt.remove(tracker_line)
        line_text = f'Dist: {dist_xyz(points[0], points[1]):.2f}'
        start = [points[0][0], points[0][1], points[0][2] + 1]
        ended = [points[1][0], points[1][1], points[1][2] + 1]
        tracker_line = Ruler(start, ended, lw=width, c=col, alpha=1.0, s=size, label=line_text)
        plt.add([tracker_line])
        # print(f'Added ruler')
        plt.render()
        # print(f'Added {col} line bw {points[0]} and {points[1]}')
    else:
        print('Invalid number of points')


def update_text(text_id, value, rel_pos=None):
    global all_objects
    if rel_pos is None:
        rel_pos = [5, 5, 5]
    if text_id in all_objects.keys():
        plt.remove(all_objects[text_id]['text'])
        rel_pos = all_objects[text_id]['pos']
    new_text = add_text(value, pos=min_xyz+rel_pos, silent=True)
    all_objects[text_id] = {
        'text': new_text,
        'pos': rel_pos
    }
    plt.add(new_text)
    plt.render()


def print_point(point, acc=2):
    print(','.join([f'%ds.{acc}f' % e for e in (point - min_xyz)]))


# noinspection DuplicatedCode
def get_line_of_points(point_values):
    # Calculates a unit of direction along line
    x_len = point_values[1][0] - point_values[0][0]
    y_len = point_values[1][1] - point_values[0][1]

    # magnitude is the distance in XY plane
    magnitude = math.sqrt((x_len ** 2) + (y_len ** 2))
    x_unit = x_len / magnitude
    y_unit = y_len / magnitude

    # Plot starting point
    # add_point(point_values[0], col='yellow')

    cur_point = point_values[0]
    line_pts = [cur_point]
    # Iterate through points in line and save them in list
    while round(cur_point[0]) != round(point_values[1][0]) and\
            round(cur_point[1]) != round(point_values[1][1]):
        cur_point = [cur_point[0] + x_unit, cur_point[1] + y_unit, cur_point[2]]
        line_pts.append(cloud.closestPoint(cur_point))
    line_pts.append(point_values[1])

    print(f'Get line of points, Input = {point_values}')
    for i in range(1, len(line_pts)):
        print(f' XX = {(line_pts[i][0]-line_pts[i-1][0]):.2f},'
              f' YY = {(line_pts[i][1]-line_pts[i-1][1]):.2f},'
              f' ZZ = {(line_pts[i][2]-line_pts[i-1][2]):.2f}')

    return line_pts


# slope calculation
def get_slope(pt1, pt2, run):
    try:
        slope = (pt2[2] - pt1[2]) / (pt2[run] - pt1[run])
    except:
        slope = (pt2[2] - pt1[2]) / 0.00001
    if slope == math.inf or slope == math.inf * -1 or slope == math.nan:
        slope = 0
    return slope


# Get the average slope of from point to point for a specified number of points on the line
def get_avg_slope(line_pts):
    global first_pt, second_pt, smooth_factor
    # Determine if y or x is longer on the line
    # first_point_x = line_pts[0][0]
    # last_point_x = line_pts[-1][0]
    # x_range = abs(first_point_x - last_point_x)
    #
    # first_point_y = line_pts[0][1]
    # last_point_y = line_pts[-1][1]
    # y_range = abs(first_point_y - last_point_y)

    # Get correct 2-d slope where z is the slopes "rise" and the longer of x and y will be the "run"
    try:
        update_text('text3', 'Enter num points: ')
        smooth_factor = int(input(f'Enter the number of points bw 1 and {len(line_pts) - 1}'))
        # "How many points (+/- 1 due to divisibility)" \
        # " between the start and end do you want to contribute" \
        # " to the avg(num <= to length/ or 'all'). "
        if smooth_factor >= len(line_pts):
            smooth_factor = len(line_pts) - 1
    except Exception as e:
        print(f'Error occurred: {e}')
        smooth_factor = len(line_pts) - 1

    if smooth_factor == 0:
        pts_to_use = [first_pt, second_pt]
    else:
        try:
            # Get a step factor to end up with the specified number of points
            # step_factor = len(line_pts) // (smooth_factor + 1)
            step_factor = round(len(line_pts) / (smooth_factor + 1))
            pts_to_use = line_pts[0::step_factor]
            print(f'Smooth factor = {smooth_factor}, steps = {step_factor}')
        except Exception as e:
            print(f'Error occurred: {e}')
            step_factor = round(len(line_pts) / smooth_factor)
            pts_to_use = line_pts[0::step_factor]

        # pts_to_use = pts_to_use[1:-1]   # Remove the first and last points
        if len(pts_to_use) < 2:
            print('Error in point selection. Aborting')
            return
        print(f'Using {len(pts_to_use)} for calculation, points are {pts_to_use}')
    # Loop through points and plot them

    print(f'Rendering {len(pts_to_use)} on map')
    update_text('text3', f'Rendering {len(pts_to_use)} points')
    for p in pts_to_use:
        add_point(p, size=RD_3, col='g', silent=True)
        plt.render()
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
            xy_dist = 0.000001
        slopes_bw_points[i]['Slope'] = (z_dist / xy_dist)
        total_slope += (z_dist / xy_dist)

    print_text = 'X1, Y1, Z1, X2, Y2, Z2, Slope \n'
    print_text += '\n'.join(['%.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f' %
                             (e['X1'], e['Y1'], e['Z1'], e['X2'], e['Y2'], e['Z2'], e['Slope'])
                             for e in slopes_bw_points])

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
        with open(csv_file, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=['X1', 'Y1', 'Z1', 'X2', 'Y2', 'Z2', 'Slope'])
            writer.writeheader()
            for data in slopes_bw_points:
                writer.writerow(data)
    except IOError:
        print("I/O error")

    result = total_slope / len(slopes_bw_points)

    # pd_slope_array.to_csv(f'calc_slope_{result}.csv')
    print(f'Average slope between {len(pts_to_use)} points = {result}, \n List of slopes for indices: ')
    # print(pd_slope_array)
    return result


def reset_plot():
    global line, two_points, tracking_mode
    print('Removing all objects from map')
    plt.removeCallback('MouseMove')
    plt.clear()
    plt.axes = 1
    plt.add([mesh, cloud]).render()
    update_text('text1', 'SlopeAVG: OFF')
    update_text('text2', 'Tracking: OFF')
    update_text('text3', '')
    line = None
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
    plt.render()
    print('Camera Reset Done')


def slider_y(widget, event):
    value = widget.GetRepresentation().GetValue()
    # mesh.y(value)  # set y coordinate position
    print(f'Slider action val = {value}')


''' All the global variables declared '''
line = None
two_points = []
tracker_line = None
tracking_mode = False
first_pt = None
second_pt = None
slope_avg_mode = False
last_pt = [0, 0, 0]
initialized = False
all_objects = {
}
''' End of variable declarations '''

# settings.enableDefaultKeyboardCallbacks = False

print(f'Program started :')
start_time = time.time()
filename = sys.argv[1]
cloud = load(sys.argv[1]).pointSize(3.5)
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
# print('Once the program launches, press \'h\' for list of default commands')
plt.show([mesh, cloud], interactorStyle=0, bg='white', axes=1, zoom=1.5, interactive=True)  # , camera=cam)
exit()



# interactive()
# print('Finished execution')
