import numpy as np
from vedo import *

num = 200

# Create a scalar field: the distance from point (15,15,15)
POW = 2
X, Y, Z = np.mgrid[:num, :num, :num]
scalar_field = ((X-(num/2))**POW + (Y-(num/2))**POW + (Z-(num/2))**POW)/((num/4)**POW)

# print(scalar_field)
# Create the Volume from the numpy object
vol = Volume(scalar_field)

# Generate the surface that contains all voxels in range [1,2]
lego = vol.legosurface(1,2).addScalarBar()

show(lego, axes=True)

circle = fitCircle([[0,0,0], [1,1,0], [3,2,1]])