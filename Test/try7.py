import numpy as np
import laspy
from vedo import *

filename = 't3.ply'
cloud = load(filename)
min_xyz = np.min(cloud.points(), axis=0)
max_xyz = np.max(cloud.points(), axis=0)
range_xyz = max_xyz - min_xyz
print(range_xyz)
# settings.useParallelProjection = True
plt = Plotter(pos=[0, 0], size=[800, 1080])
pic = Picture('3_1.png')
dim = pic.dimensions()
print(dim)
scale_fact = [range_xyz[0]/dim[0], range_xyz[1]/dim[1], 1]
pic = pic.scale(scale_fact).pos(min_xyz[0]-1, min_xyz[1]+0.2, min_xyz[2]).rotateZ(2)
# plt.addCallback('Enter', mouse_track)
# plt.addCallback('timer', handle_timer)
# plt.addScaleIndicator(units='um', c='blue4')
# plt.addCallback('LeftButtonPress', on_left_click)
# timer = plt.timerCallback(action='create')
# plt.addCallback('Error', handle_error)
# plt.addCallback('Warning', handle_warning)
# plt.addCallback('Enter', handle_entry)
# plt.addCallback('Leave', handle_entry)

cloud_center = cloud.centerOfMass()
cam = dict(pos=(cloud_center[0], cloud_center[1], cloud_center[2] + 200),
           focalPoint=cloud_center,
           viewup=(0, 1.00, 0),
           clippingRange=(218.423, 388.447)
           )
plt.show([pic, cloud], interactorStyle=0, bg='white', axes=1, zoom=1.0,
         interactive=True, camera=cam)