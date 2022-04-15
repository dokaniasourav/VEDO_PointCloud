from vtkplotter import Mesh
import numpy as np

x = np.array([
 [-0.93333333, -0.93333333, -0.93333333, -0.93333333],
 [-0.93333333, -0.93333333, -0.93333333, -0.93333333],
 [-1.,         -1.,         -1.,         -1.        ],
 [-1.,         -1.,         -1.,         -1.        ]])

y = np.array([
 [1., 1., 1., 1.],
 [1., 1., 1., 1.],
 [1., 1., 1., 1.],
 [1., 1., 1., 1.]])

z = np.array([
 [-1.,         -0.93333333, -0.86666667, -0.8       ],
 [-0.93333333, -0.86666667, -0.8,        -0.73333333],
 [-0.93333333, -0.86666667, -0.8,        -0.73333333],
 [-1.,         -0.93333333, -0.86666667, -0.8       ]])

colormat = np.array([
 [0.11484721, 0.11484721, 0.11484721],
 [0.11648363, 0.11648363, 0.11648363],
 [0.12010454, 0.12010454, 0.12010454],
 [0.12384401, 0.12384401, 0.12384401]])

colormat *= np.array([1,2,3,4]).reshape(-1, 1) # just to make greys more visible

verts = np.hstack([x.reshape(-1,1,order='F'),
                   y.reshape(-1,1,order='F'),
                   z.reshape(-1,1,order='F')])
faces = np.arange(0,len(verts), 1)
faces = np.split(faces, 4) # this describes the faces (by vertex index)

# the optional reverse() flips the orientation of cells
m = Mesh([verts,faces]).reverse().cellIndividualColors(colormat).lw(2)
m.rotateZ(10).rotateX(20) # just to make the axes visible
m.show(axes=8, elevation=60, bg='wheat', bg2='lightblue')