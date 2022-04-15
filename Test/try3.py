import numpy as np
import laspy
from vedo import *

filename = '../3_1.las'
with laspy.open(filename, mode='r') as fh:
    # print('Points from Header:', fh.header.point_count)
    # las = fh.read()
    # print(las)
    # print('Points from data:', len(las.points))
    # print('Classification = ', np.unique(las.classification))
    for points in fh.chunk_iterator(10):
        print(points.array)
        print(points.point_format)
        print(points.scales)
        # for point in points:
        #     print(point)
        break
    fh.close()

# filename = '3_1.las'
# cloud = load(filename)
# print(cloud.points())
# min_xyz = np.min(cloud.points(), axis=0)
# max_xyz = np.max(cloud.points(), axis=0)
# print(min_xyz, max_xyz)