import vedo
import multiprocessing
import Interface as Intf


class LocalPlotter:
    plotter_mode: int
    tracking_mode: bool
    initialized = False
    min_xyz: []
    max_xyz: []
    geo_xyz: []
    cloud_center: []
    cam_center: []
    scale_f = 1.0
    last_key_press = None
    smooth_factor = 0
    inp_q: multiprocessing.Queue
    out_q: multiprocessing.Queue
    gui_q: multiprocessing.Queue
    timerID = None
    current_points: list[list[float]] = []
    plotted_trackers = []
    plotted_points = []
    plotted_lines = []
    plotted_texts = []
    rect_points = []
    show_ele_list = []
    gp_int_state = 0
    mesh_objects: Intf.AllMeshObjects
