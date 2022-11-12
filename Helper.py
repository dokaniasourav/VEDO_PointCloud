import numpy as np


def dist_xyz(points):
    if len(points[0]) != 3 or len(points[1]) != 3:
        print('Bad Value of pt in dist_xyz')
        return None

    return np.math.sqrt((points[0][0] - points[1][0]) ** 2 +
                        (points[0][1] - points[1][1]) ** 2 +
                        (points[0][2] - points[1][2]) ** 2)


def dist_xy(points):
    if len(points[0]) < 2 or len(points[1]) < 2:
        print('Bad Value of pt in dist_xy')
        return None

    return np.math.sqrt((points[0][0] - points[1][0]) ** 2 +
                        (points[0][1] - points[1][1]) ** 2)


def get_xy_angle(points, no_change=False):
    yy_diff = points[1][1] - points[0][1]
    xx_diff = points[1][0] - points[0][0]
    angle_measure = np.math.acos(xx_diff / dist_xy(points)) * (180 / np.pi)
    if no_change:
        return angle_measure

    if yy_diff < 0:
        return 360 - angle_measure
    else:
        return angle_measure
    # return angle_measure


def get_z_angle(points, no_change=False):
    xy_dist = dist_xy(points)
    xyz_dist = dist_xyz(points)
    zz_diff = points[1][2] - points[0][2]
    angle_measure = np.math.acos(xy_dist / xyz_dist) * (180 / np.pi)
    if no_change:
        return angle_measure

    if zz_diff < 0:
        return 360 - angle_measure
    else:
        return angle_measure
    # return angle_measure


def get_slope(point1, point2):
    xy_dist = dist_xy([point1, point2])
    zz_dist = (point2[2] - point1[2])
    if xy_dist < 0.001:
        print('Points selected are too close')
        xy_dist = 0.001
    return zz_dist / xy_dist


def get_xy_intersection(a1, a2, b1, b2):
    """
    a1, a2, b1, b2: [x, y] of points in line A and line B
    """
    s = np.vstack([a1[0:2], a2[0:2],
                   b1[0:2], b2[0:2]])  # s for stacked
    h = np.hstack((s, np.ones((4, 1))))  # h for homogeneous
    l1 = np.cross(h[0], h[1])  # get first line
    l2 = np.cross(h[2], h[3])  # get second line
    x, y, z = np.cross(l1, l2)  # point of intersection
    if z == 0:  # lines are parallel
        print('Could not find line intersection')
        return [0.0, 0.0]

    return np.array([x / z, y / z, (a1[2] + a2[2]) / 2])


def get_rectangle(points):
    if len(points) != 3:
        print('Bad input in get_rect')
        return []
    point_1 = np.array(points[0])
    point_2 = np.array(points[1])
    point_3 = np.array(points[2])

    point_12 = point_1 - point_2
    point_31 = point_3 - point_1
    point_32 = point_3 - point_2

    cosine_1 = np.dot(point_12, point_31) / (np.linalg.norm(point_12) * np.linalg.norm(point_31))
    cosine_2 = np.dot(point_12, point_32) / (np.linalg.norm(point_12) * np.linalg.norm(point_32))

    new_point_1 = point_3 - (point_12 * (dist_xyz([point_1, point_3]) * cosine_1)) / dist_xyz([point_1, point_2])
    new_point_2 = point_3 - (point_12 * (dist_xyz([point_2, point_3]) * cosine_2)) / dist_xyz([point_1, point_2])

    max_z = max(points[1][2], points[0][2])
    points[1][2] = points[0][2] = new_point_1[2] = new_point_2[2] = max_z

    return [points[1], points[0], new_point_1, new_point_2]


def sub_point(point1, point2):
    return [point1[0] - point2[0], point1[1] - point2[1], point1[2] - point2[2]]


def add_point(points):
    return [(points[1][0] + points[0][0]),
            (points[1][1] + points[0][1]),
            (points[1][2] + points[0][2])]


def avg_point(points):
    return [(points[1][0] + points[0][0]) / 2.0,
            (points[1][1] + points[0][1]) / 2.0,
            (points[1][2] + points[0][2]) / 2.0]


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


