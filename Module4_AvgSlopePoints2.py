from vedo import *
import numpy as np
from pandas import DataFrame
import math
import sys

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
    global all_points, line, plt, slope_avg_mode, tracking_mode
    printc(f'{evt.keyPressed} pressed: ', end='')
    if evt.keyPressed == 'c':
        # clear points and lines
        plt.remove([all_points, line], render=True)
        all_points = []
        line = None
        printc("==== Cleared all points ====", c="r")
    elif evt.keyPressed == 'z':
        # Enter slope average mode
        print("========ENTER SLOPE AVG MODE========")
        slope_avg_mode = True
    elif evt.keyPressed == 'u':
        print('Removing all objects from the map')
        plt.clear()
        plt.add([mesh, cloud]).render()
        # Resets the used global variables
        line = None
        all_points = []
        plt.removeCallback('MouseMove')
        tracking_mode = False
    elif evt.keyPressed == 't':
        print('Camera Reset Done')
        my_camera_reset()


def on_left_click(event):
    global first_pt, second_pt, all_points, line, last_pt, tracking_mode
    printc(f'Clicked at {event.picked3d}')
    if slope_avg_mode:
        try:
            cpt = vector(list(event.picked3d))  # Make a vector of list, IDK why
            print(f'Added point {cpt}')

            all_points.append(cpt)
            last_pt = Point(cpt, r=25, c='red')  # Point to be added, radius is 30 and red color
            plt.add([last_pt])
            print(f'Added last point: {all_points}')
            if len(all_points) == 2:
                # Select second point and connect them with a line
                line = Line(all_points[-2], all_points[-1], closed=False, lw=5, c='red')
                print(f'Added red line')
                line.legend('Base Line number 1')
                plt.add([line])
                second_pt = np.array([cpt[0], cpt[1], cpt[2]])
                plt.render()
                plt.removeCallback('MouseMove')
                tracking_mode = False

                # Get actual points
                print(f'Getting the line of points bw {all_points}')
                point_list = get_line_of_points(all_points)
                print(f'Number of points on the line: {len(point_list)}', end='')

                print("Getting average slope from the points")
                avg_slope_on_line = get_avg_slope(point_list)  # Get the average slope of points
                print(f'Average slope of line: {avg_slope_on_line}')
                all_points = []

            elif len(all_points) == 1:
                # Select the first point
                first_pt = np.array([cpt[0], cpt[1], cpt[2]])
                print("START TRACKING")
                if not tracking_mode:
                    plt.addCallback('MouseMove', mouse_track)
                    tracking_mode = True
            plt.render()

        except Exception as e:
            # The points selected by the clicks must be already existing points
            print(f'Error occurred: {e}')


def mouse_track(event):
    global tracking_mode, tracker_line, last_pt
    # if not tracking_mode:
    #     return

    # Track the mouse if a point has already been selected
    if not event.actor:
        return
    mouse_point = event.picked3d
    try:
        # Continuously replace the tracker line
        plt.remove(tracker_line)
    except Exception as e:
        # The points selected by the clicks must be already existing points
        print(f'Error occurred: {e}')
        print('First tracker line')
        slope = last_pt
    tracker_line = Ruler(last_pt, mouse_point, lw=3, s=3)

    plt.add([tracker_line])
    plt.render()
    return


# The get_line_of_points takes the two endpoints, then does its best to get the points along the path of the line
# that are on the ground of the point cloud Does this by iterating through the points that make up the line in
# space, then getting the closest point that is actually a part of the mesh to that point

# noinspection DuplicatedCode
def get_line_of_points(point_values):
    # Calculates a unit of direction along line
    x_dir = point_values[1][0] - point_values[0][0]
    y_dir = point_values[1][1] - point_values[0][1]

    # magnitude is the distance in XY plane
    magnitude = math.sqrt((x_dir ** 2) + (y_dir ** 2))
    x_unit = x_dir / magnitude
    y_unit = y_dir / magnitude

    # Plot starting point
    start_pt = Point(point_values[0], r=30, c='black')
    plt.add([start_pt])
    plt.render()
    print('Added point 1 in black')

    cur_point = point_values[0]
    line_pts = []
    # Iterate through points in line and save them in list
    while round(cur_point[0]) != round(point_values[1][0]) and round(cur_point[1]) != round(point_values[1][1]):
        cur_point = [cur_point[0] + x_unit, cur_point[1] + y_unit, cur_point[2]]
        # cur_point_as_pt = Point(cur_point, r=30, c="purple")
        line_pt = cloud.closestPoint(cur_point)
        line_pts.append(line_pt)
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

        print(f'Using {len(pts_to_use)} for calculation, points are {pts_to_use}')
        pts_to_use = pts_to_use[1:-1]   # Remove the first and last points
        # pts_to_use.append(line_pts[-1])
        # Add starting and end points
        pts_to_use = [np.asarray(first_pt)] + pts_to_use
        # pts_to_use[:0] = np.asarray(first_pt)
        pts_to_use.append(np.asarray(second_pt))
    # Loop through points and plot them

    print(f'Rendering {len(pts_to_use)} on map')
    for p in pts_to_use:
        cur = Point(p, r=20).c("g")
        plt.add([cur])
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

    print(slopes_bw_points)
    pd_slope_array = DataFrame(slopes_bw_points, columns=['x1', 'y1', 'z1', 'x2', 'y2', 'z2', 'sp'], dtype=float)
    # slopes_bw_points.append(get_slope(pts_to_use[pt - 1], pts_to_use[pt], run))

    # if x_range >= y_range:
    #     pts_to_use_df['y'] = np.nan
    #     run = 0
    #     # Get slope between x and z axis where x is "run"
    #     for pt in range(1, len(pts_to_use)):
    #         slopes_bw_points.append(get_slope(pts_to_use[pt - 1], pts_to_use[pt], run))
    # else:
    #     pts_to_use_df["x"] = np.nan
    #     run = 1
    #     # Get slope between y and z axis where y is "run"
    #     for pt in range(1, len(pts_to_use)):
    #         slopes_bw_points.append(get_slope(pts_to_use[pt - 1], pts_to_use[pt], run))
    # pts_to_use_df.to_csv("pts_used_in_avg_slope_calc.csv")
    # Takes the slope between each point in sequence and averages them
    result = total_slope / len(slopes_bw_points)
    pd_slope_array.to_csv(f'calc_slope_{result}.csv')
    print(f'Average slope between {len(pts_to_use)} points = {result}, \n List of slopes for indices: ')
    print(pd_slope_array)
    return result


def get_perpendicular(pt1, pt2, pt3):
    v1 = np.array([pt2[0] - pt1[0], pt2[1] - pt1[1], pt2[2] - pt1[2]])
    v2 = np.array([pt2[0] - pt3[0], pt2[1] - pt3[1], pt2[2] - pt3[2]])
    return np.cross(v1, v2)


def distance_between_points(pt1, pt2):
    return math.sqrt(((pt1[0] - pt2[0]) ** 2) + ((pt1[1] - pt2[1]) ** 2) + ((pt1[2] - pt2[2]) ** 2))


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
all_points = []
tracker_line = None
tracking_mode = False
first_pt = None
second_pt = None
slope_avg_mode = False
last_pt = False
''' End of variable declarations '''

cloud = load(sys.argv[1]).pointSize(3.5)
cloud_center = cloud.centerOfMass()  # Center of mass for the whole cloud
print("CLOUD CENTER = ", end='')
print(cloud_center)
z_center = cloud_center[2]
mesh = delaunay2D(cloud.points()).alpha(0.1).c("white")  # Some mesh object with low alpha

cam = dict(pos=(cloud_center),
           focalPoint=(2321420.115, 6926160.299, 702.312),
           viewup=(0, 1.00, 0),
           distance=293.382,
           clippingRange=(218.423, 388.447))

plt = Plotter(pos=[0, 0], size=[500, 1080], )
plt.addCallback('KeyPress', on_key_press)
plt.addCallback('LeftButtonPress', on_left_click)
# plt.addCallback('RightButtonPress', onRightClick)
# plt.addCallback('MouseMove', mouseTrack)
# plt.removeCallback(mouseTrack)
print("Once the program launches, press 'h' for list of default commands")
plt.show([mesh, cloud], interactorStyle=0, bg='white', axes=1, zoom=1.5)  # , camera = cam)
interactive()
