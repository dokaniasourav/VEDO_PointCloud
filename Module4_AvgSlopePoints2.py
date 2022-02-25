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
    global two_points, line, plt, slope_avg_mode, tracking_mode
    printc(f'{evt.keyPressed} pressed: ', end='')
    if evt.keyPressed == 'c':
        # clear points and lines
        plt.remove([two_points, line], render=True)
        two_points = []
        line = None
        printc("==== Cleared all points ====", c="r")
    elif evt.keyPressed == 'z':
        # Enter slope average mode
        print("========ENTER SLOPE AVG MODE========")
        add_text('Slope AVG Mode', pos=min_xyz)
        slope_avg_mode = True
    elif evt.keyPressed == 'u':
        reset_plot()
    elif evt.keyPressed == 't':
        print('Camera Reset Done')
        my_camera_reset()


def on_left_click(event):
    global first_pt, second_pt, two_points, line, last_pt, tracking_mode, slope_avg_mode
    if event.picked3d is None:
        return
    # printc(f'Clicked at {event.picked3d}')
    if slope_avg_mode:
        try:
            cpt = vector(list(event.picked3d))  # Make a vector of list, IDK why
            two_points.append(cpt)
            add_point(cpt, size=RD_1, col='red')
            last_pt = cpt
            if len(two_points) == 2:
                # Select second point and connect them with a line
                plt.removeCallback('MouseMove')
                tracking_mode = False
                slope_avg_mode = False
                add_line(two_points, width=4, col='green')
                second_pt = np.array([cpt[0], cpt[1], cpt[2]])
                # plt.render()

                # Get actual points
                point_list = get_line_of_points(two_points)
                print(f'Number of points on the line: {len(point_list)} bw {two_points}')

                for pt in point_list:
                    print('(', ', '.join(['%.2f' % e for e in (pt - min_xyz)]), ')')

                avg_slope_on_line = get_avg_slope(point_list)  # Get the average slope of points
                print(f'Average slope of line: {avg_slope_on_line}')
                two_points = []

            elif len(two_points) == 1:
                # Select the first point
                first_pt = np.array([cpt[0], cpt[1], cpt[2]])
                print("START TRACKING")
                if not tracking_mode:
                    plt.addCallback('MouseMove', mouse_track)
                    tracking_mode = True
                # add_point(last_pt)
            plt.render()

        except Exception as e:
            # The points selected by the clicks must be already existing points
            print(f'Error occurred: {e}')


def mouse_track(event):
    global last_pt

    # Track the mouse if a point has already been selected
    if not event.actor:
        # print('No actor found while tracking ... ')
        return

    mouse_point = event.picked3d
    add_ruler([last_pt, mouse_point], width=3, col='red', size=3)
    return


# The get_line_of_points takes the two endpoints, then does its best to get the points along the path of the line
# that are on the ground of the point cloud Does this by iterating through the points that make up the line in
# space, then getting the closest point that is actually a part of the mesh to that point

def add_point(pos, size=RD_1, col='red', silent=False):
    new_point = Point(pos, r=size, c=col)  # Point to be added, default radius and default color
    pos2 = [pos[0], pos[1], pos[2] + 1]
    new_text = Text3D(txt=','.join(['%.2f' % e for e in (pos - min_xyz)]), s=2, pos=pos2, depth=0.1, alpha=1.0)
    plt.add([new_point, new_text])
    plt.render()
    if not silent:
        print(f'Added point: {pos}')


def add_text(text, pos, silent=False):
    pos[2] += 1
    tx1 = Text3D(txt=text, s=2, pos=pos, depth=0.1, alpha=1.0)
    plt.add([tx1])
    plt.render()
    if not silent:
        print(f'Text Rendered at {pos}')


def add_line(points, col='red', width=5, silent=False):
    print(f'Added line')
    if len(points) >= 2:
        new_line = Line(points[0], points[1], closed=False, lw=width, c=col, alpha=1.0)
        plt.add([new_line])
        plt.render()
        if not silent:
            print(f'Added {col} line bw {points[0]} and {points[1]}')
    else:
        print('Invalid number of points')


def add_ruler(points, col='red', width=5, size=3):
    global tracker_line
    if len(points) >= 2:
        plt.remove(tracker_line)
        tracker_line = Ruler(points[0], points[1], lw=width, c=col, alpha=1.0, s=size)
        plt.add([tracker_line])
        # print(f'Added ruler')
        plt.render()
        # print(f'Added {col} line bw {points[0]} and {points[1]}')
    else:
        print('Invalid number of points')


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
    add_point(point_values[0], col='black')

    cur_point = point_values[0]
    line_pts = [cur_point]
    # Iterate through points in line and save them in list
    while round(cur_point[0]) != round(point_values[1][0]) and round(cur_point[1]) != round(point_values[1][1]):
        cur_point = [cur_point[0] + x_unit, cur_point[1] + y_unit, cur_point[2]]
        line_pts.append(cloud.closestPoint(cur_point))
    line_pts.append(point_values[1])
    print(f'Get line of points, Input = {point_values} and output = {line_pts}')
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
    global first_pt, second_pt
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
        # pts_to_use.append(line_pts[-1])
        # Add starting and end points
        # pts_to_use = [np.asarray(first_pt)] + pts_to_use
        # pts_to_use[:0] = np.asarray(first_pt)
        # pts_to_use.append(np.asarray(second_pt))
    # Loop through points and plot them

    print(f'Rendering {len(pts_to_use)} on map')
    for p in pts_to_use:
        add_point(p, size=RD_2, col='g')
        plt.render()

    # Save the data on the point locations in the 2 dimensions of interest
    # pts_to_use_df = pd.DataFrame(pts_to_use, columns=['x', 'y', 'z'])
    # print(f'Points to use df = {pts_to_use_df}')
    slopes_bw_points = []

    for pt in range(1, len(pts_to_use)):
        slopes_bw_points.append({
            'x1': pts_to_use[pt - 1][0],
            'y1': pts_to_use[pt - 1][1],
            'z1': pts_to_use[pt - 1][2],
            'x2': pts_to_use[pt - 0][0],
            'y2': pts_to_use[pt - 0][1],
            'z2': pts_to_use[pt - 0][2],
            'sp': math.nan
        })

    total_slope = 0
    for i, pt in enumerate(slopes_bw_points):
        # Range should be define by net distance, not XY maximum
        xy_dist = math.sqrt(((pt['x1'] - pt['x2']) ** 2) + ((pt['y1'] - pt['y2']) ** 2))
        z_dist = abs(pt['z1'] - pt['z2'])
        if xy_dist == 0:
            xy_dist = 0.000001
        slopes_bw_points[i]['sp'] = (z_dist / xy_dist)
        total_slope += (z_dist / xy_dist)

    print_text = 'x1, y1, z1, x2, y2, z2, sp \n'
    print_text += '\r\n'.join(['%.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f' %
                               (e['x1'], e['y1'], e['z1'], e['x2'], e['y2'], e['z2'], e['sp'])
                               for e in slopes_bw_points])

    print(print_text)
    f = open(f'Slope_{datetime.now().strftime("%Y%m%d%H%M%S")}.csv', 'w')
    f.write(print_text)
    f.close()
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
    line = None
    two_points = []
    tracking_mode = False


def my_camera_reset():
    plt.camera.SetPosition([2321420.115, 6926160.299, 995.694])
    plt.camera.SetFocalPoint([2321420.115, 6926160.299, 702.312])
    plt.camera.SetViewUp([0.0, 1.0, 0.0])
    plt.camera.SetDistance(293.382)
    plt.camera.SetClippingRange([218.423, 388.447])
    plt.render()
    print("OK Camera should reset")


''' All the global variables declared '''
line = None
two_points = []
tracker_line = None
tracking_mode = False
first_pt = None
second_pt = None
slope_avg_mode = False
last_pt = False
''' End of variable declarations '''

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

print('Once the program launches, press \'h\' for list of default commands')
plt.show([mesh, cloud], interactorStyle=0, bg='white', axes=1, zoom=1.5, interactive=True)  # , camera=cam)
exit()

# interactive()
# print('Finished execution')
