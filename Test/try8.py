# """Simulation of a block connected to a spring in a viscous medium"""
# from vedo import *
#
# settings.allowInteraction = True  # allow mouse interaction while playing
#
#
# L = 0.1    # spring x position at rest
# x0 = 0.85  # initial x-coordinate of the block
# k = 25     # spring constant
# m = 20     # block mass
# b = 0.5    # viscosity friction (proportional to velocity)
# dt = 0.15  # time step
#
# # initial conditions
# v = vector(0, 0, 0.2)
# x = vector(x0, 0, 0)
# xr = vector(L, 0, 0)
# sx0 = vector(-0.8, 0, 0)
# offx = vector(0, 0.3, 0)
#
# plt = Plotter(size=(1050, 600))
# plt += Box(pos=(0, -0.1, 0), length=2.0, width=0.02, height=0.5)  # surface
# plt += Box(pos=(-0.82, 0.15, 0), length=0.04, width=0.50, height=0.3)  # wall
#
# block = Cube(pos=x, side=0.2, c="tomato")
# block.addTrail(offset=[0, 0.2, 0], lw=2, n=500)
#
# spring = Spring(sx0, x, r=0.06, thickness=0.01)
#
# plt += [block, spring, __doc__]
#
# pb = ProgressBar(0, 1200, c="r")
# for i in pb.range():
#     F = -k * (x - xr) - b * v  # Force and friction
#     a = F / m  # acceleration
#     v = v + a * dt  # velocity
#     x = x + v * dt + 1 / 2 * a * dt ** 2  # position
#
#     block.pos(x)  # update block position and trail
#     spring.stretch(sx0, x)  # stretch helix accordingly
#
#     plt.show(elevation=0.1, azimuth=0.1, interactive=False, zoom=1.5)
#     if plt.escaped: break # if ESC is hit during the loop
#     pb.print()
#
# plt.interactive().close()

"""Visualize scalar values interactively
by hovering the mouse on a mesh
Press c to clear the path"""

# """Modify a spline interactively.
# - Drag points with mouse
# - Add points by clicking on the line
# - Remove them by selecting&pressing DEL
# --- PRESS q TO PROCEED ---"""
# from vedo import Circle, show
#
# # Create a set of points in space
# pts = Circle(res=8).extrude(zshift=0.5).pointSize(4)
#
# # Visualize the points
# plt = show(pts, __doc__, interactive=False, axes=1)
#
# # Add the spline tool using the same points and interact with it
# sptool = plt.addSplineTool(pts, closed=True)
# plt.interactive()
#
# # Switch off the tool
# sptool.off()
#
# # Extract and visualize the resulting spline
# sp = sptool.spline().lw(4)
# show(sp, "My spline is ready!", interactive=True, resetcam=False).close()

from vedo import *

settings.useDepthPeeling = True

car = Mesh(dataurl+"porsche.ply").alpha(0.2)

line = [(-9.,0.,0.), (0.,1.,0.), (9.,0.,0.)]
tube = Tube(line).triangulate().c("violet",0.2)

contour = car.intersectWith(tube).lineWidth(4).c('black')

show(car, tube, contour, __doc__, axes=7).close()
