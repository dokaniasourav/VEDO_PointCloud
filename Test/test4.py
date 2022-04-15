import numpy as np
from vedo import *

num = 50

# Create a scalar field: the distance from point (15,15,15)
X, Y, Z = np.mgrid[:num, :num, :num]
scalar_field = ((X-(num/2))**2 + (Y-(num/2))**2 + (Z-(num/2))**2)/((num/2)*(num/2))

print(scalar_field)
# Create the Volume from the numpy object
vol = Volume(scalar_field)

# Generate the surface that contains all voxels in range [1,2]
lego = vol.legosurface(1,2).addScalarBar()

show(lego, axes=True)