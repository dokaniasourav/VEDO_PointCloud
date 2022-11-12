"""Add a square button with N possible internal states
to a rendering window that calls an external function"""
import vedo


# add a button to the current renderer (e.i. nr1)
def button_func():
    mesh.alpha(1 - mesh.alpha())  # toggle mesh transparency
    bu.switch()                 # change to next status
    vedo.printc(bu.status(), box="_", dim=True)


plt = vedo.Plotter(pos=[0, 0], size=[600, 1080])

mesh = vedo.Mesh(vedo.dataurl+"magnolia.vtk").c("v").flat()

bu = plt.addButton(
    button_func,
    pos=(0.7, 0.05),  # x,y fraction from bottom left corner
    states=["click to hide", "click to show"],
    c=["w", "w"],
    bc=["dg", "dv"],  # colors of states
    font="courier",   # arial, courier, times
    size=10,
    bold=True,
    italic=False,
)

plt.show(mesh, __doc__).close()
