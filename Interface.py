import multiprocessing
import tkinter
import time
import copy
import sys
import os

import tkinter.filedialog
import vedo

import Helper as HpF


class MeshObject:
    mesh: vedo.Mesh
    name: str
    rotation: list[float]
    disp_location: list[float]
    mesh_location: list[float]

    def __init__(self, name: str, pos: list[float]):
        self.name = name
        self.rotation = [0.0, 0.0, 0.0]
        self.disp_location = copy.copy(pos)
        self.mesh_location = copy.copy(pos)

    def move(self, position: list[float]):
        if len(position) == 3:
            self.disp_location = position
            new_pos = HpF.sub_points(position, self.mesh_location)
            self.mesh.pos(new_pos)
        else:
            raise ValueError('Incorrect arguments for update position')

    def rotate(self, angle: float, axis: list[float], point: list[float]):
        if abs(angle) < 0.000001:
            return
        if len(axis) == len(point) == 3:
            self.mesh.rotate(angle=angle, axis=axis, point=point)
            self.mesh_location = HpF.sub_points(self.disp_location, self.mesh.pos())
        else:
            raise ValueError('Invalid dimensions for either angle, axis or point')


class VehicleData:

    def __init__(self, output_dict: dict[str, str]):

        print(output_dict)
        self.valid_data = True
        if 'WheelWidth' not in output_dict:
            self.valid_data = False
            return

        self.num_wheels: int = 4
        self.wheel_width: float = float(output_dict['WheelWidth'])
        self.wheel_radius: float = float(output_dict['WheelRadius'])

        self.width: float = float(output_dict['VehicleWidth'])
        self.length: float = float(output_dict['VehicleLength'])
        self.back_overhang: float = float(output_dict['BackOverhang'])
        self.front_overhang: float = float(output_dict['FrontOverhang'])

        _num_points = float(output_dict['NumberOfPoints'])
        self.num_of_points: int = int(round(_num_points))

        self.height: float = self.wheel_radius/2.0
    # disp_location: list[list[float]]
    # mesh_location: list[list[float]]
    # mesh_rotation: list[float]
    # path_points = list[float]
    # path_lines = list[float]
    # vehicle_mesh: list[vedo.Mesh]


class AllMeshObjects:
    data: VehicleData
    total: int
    meshes: dict[int, MeshObject]

    def __init__(self, data: VehicleData):
        self.data = data
        self.total = 0

    def add_mesh_obj(self, id_num: int, mesh_obj: MeshObject):
        if hasattr(self, 'meshes'):
            self.meshes[id_num] = mesh_obj
        else:
            self.meshes = dict({
                id_num: mesh_obj
            })
        self.total += 1

    def add_mesh(self, id_num: int, mesh: vedo.Mesh):
        self.meshes[id_num].mesh = mesh

    def get_mesh(self, id_num: int):
        if id_num in self.meshes.keys():
            return self.meshes[id_num].mesh
        else:
            print('Mesh object not found')
            return None

    def get_display_loc(self, id_num: int) -> list[float]:
        return self.meshes[id_num].disp_location

    def get_mesh_location(self, id_num: int) -> list[float]:
        return self.meshes[id_num].mesh_location

    def get_points(self, id_num: int) -> list[list[float]]:
        if id_num in self.meshes.keys():
            return self.meshes[id_num].mesh.points()
        else:
            print('Mesh object not found')
            return [[]]

    def move(self, id_num: int, position: list[float]):
        self.meshes[id_num].move(position)

    def rotate(self, id_num: int, angle: float, axis: list[float], point: list[float]):
        self.meshes[id_num].rotate(angle, axis, point)

    def rotate_i(self, id_nums: list[int], angle: float, axis: list[float], point: list[float]):
        for id_num in id_nums:
            self.meshes[id_num].rotate(angle, axis, point)

    def rotate_all(self, angle: float, axis: list[float], point: list[float]):
        for id_num in self.meshes.keys():
            self.meshes[id_num].rotate(angle, axis, point)

    def move_all(self, position: list[float]):
        for id_num in self.meshes.keys():
            self.meshes[id_num].move(position)

    def add_to_plot(self, plt: vedo.Plotter, id_num: int):
        plt.add(self.meshes[id_num].mesh)


def get_vehicle_data(gui_q, ):
    root = tkinter.Tk()
    root.title('Vehicle Attribute Selection')
    root.columnconfigure(0, weight=1)
    root.columnconfigure(1, weight=1)
    root.columnconfigure(2, weight=1)

    fields = {
        0: {'data': tkinter.StringVar(), 'default': '___', 'max_v': 10.0, 'min_v': 0.0,
            's_name': '__', 'name': 'Enter the required vehicle parameters in feet'},
        1: {'data': tkinter.StringVar(), 'default': '0.8', 'max_v': 10.0, 'min_v': 0.1,
            's_name': 'back_overhang', 'name': 'Back Overhang'},
        2: {'data': tkinter.StringVar(), 'default': '0.8', 'max_v': 10.0, 'min_v': 0.1,
            's_name': 'front_overhang', 'name': 'Front Overhang'},
        6: {'data': tkinter.StringVar(), 'default': '4.0', 'max_v': 40.0, 'min_v': 1.0,
            's_name': 'length', 'name': 'Vehicle Length'},
        7: {'data': tkinter.StringVar(), 'default': '2.0', 'max_v': 20.0, 'min_v': 1.0,
            's_name': 'width', 'name': 'Vehicle Width'},

        3: {'data': tkinter.StringVar(), 'default': '0.6', 'max_v': 20.0, 'min_v': 0.1,
            's_name': 'wheel_radius', 'name': 'Wheel Radius'},
        4: {'data': tkinter.StringVar(), 'default': '0.2', 'max_v': 20.0, 'min_v': 0.1,
            's_name': 'wheel_width', 'name': 'Wheel Width'},
        5: {'data': tkinter.StringVar(), 'default': '4', 'max_v': 16.0, 'min_v': 1.0,
            's_name': 'num_wheels', 'name': 'Number of wheels'}
    }

    print('Enter vehicle attributes in dialog box')
    for i in fields.keys():
        label = tkinter.Label(root, text=fields[i]['name'], borderwidth=2, font=10)
        label.grid(column=0, row=i, sticky=tkinter.W, padx=5, pady=5)
        if i == 0:
            continue
        else:
            fields[i]['data'].set(fields[i]['default'])
            ent = tkinter.Entry(root, textvariable=fields[i]['data'], font=10)
            ent.grid(column=1, row=i, sticky=tkinter.E, padx=5, pady=5)

    tkinter.Button(root, text='Confirm', command=lambda: get_values(root, fields, gui_q)
                   ).grid(column=1, row=len(fields), sticky=tkinter.E, padx=5, pady=5)

    root.mainloop()
    exit()


def get_values(root, field_entries, gui_q):
    vehicle_data = VehicleData()
    try:
        for field_entry in field_entries:
            fe = field_entries[field_entry]
            dt = fe['data'].get()
            if field_entry == 0:
                continue
            else:
                setattr(vehicle_data, fe['s_name'], float(dt))
                # if fe['min_v'] <= float(dt) <= fe['max_v']:
                #     setattr(vehicle_data, fe['s_name'], float(dt))
                # else:
                #     print('Error: Value is out of bound')
        # pprint(vehicle_data.__dict__)
        gui_q.put(vehicle_data)
        root.destroy()
    except Exception as e:
        print(e)


def get_file_names(required_files):
    file_names = {}
    if required_files is None or len(required_files) == 0:
        return file_names

    use_defaults = True
    root = tkinter.Tk()
    root.withdraw()
    file_types = {
        'PLY': {'ext': ('.ply', '.PLY'), 'title': 'PLY File', 'desc': 'Point-cloud file', 'default': 't3.ply'},
        'TIF': {'ext': ('.tif', '.tiff'), 'title': 'TIF File', 'desc': 'Tagged Image File', 'default': '3_1.tif'},
        'PNG': {'ext': ('.png', '.jpg', '.jpeg'), 'title': 'Image File', 'desc': 'Image Files', 'default': '3_1.png'},
        'LAS': {'ext': ('.las', '.LAS'), 'title': 'LAS File', 'desc': 'LAS point file', 'default': '3_1.las'},
        'TFW': {'ext': ('.tfw', '.TFW'), 'title': 'TFW GIS File', 'desc': 'World coordinate file', 'default': '3_1.tfw'}
    }

    if len(sys.argv) < 1 + len(required_files):
        titles = ['[' + file_types[file_type]['title'] + ']' for file_type in required_files]
        if not use_defaults:
            print('Default Usage:  ', os.path.basename(__file__), ', '.join(titles))
        for i, file_type in enumerate(required_files):
            if use_defaults:
                file_name = file_types[file_type]['default']
            else:
                print(f'No {file_type} file specified: opening prompt')
                file_name = tkinter.filedialog.askopenfilename(initialdir=os.getcwd(),
                                                               title=f'Select the {file_type} File',
                                                               filetypes=[(file_types[file_type]['desc'],
                                                                           file_types[file_type]['ext'])])
            file_names[file_type] = file_name
    else:
        for i, file_type in enumerate(required_files):
            file_names[file_type] = sys.argv[i + 1]

    for file_t in file_names:
        if not os.path.isfile(file_names[file_t]):
            print(f'Invalid {file_t} file path: {file_names[file_t]}')
            exit(1)

    root.destroy()
    return file_names


def toggle_state(queue_obj: multiprocessing.Queue, value):
    d = {
        'time': time.time(),
        'value': value
    }
    queue_obj.put(d)
    print(queue_obj.qsize())


def gui_main(inp_q: multiprocessing.Queue, out_q: multiprocessing.Queue):
    root = tkinter.Tk()
    root.geometry('400x300')
    root.title('Main menu')

    label = tkinter.Label(root, text="Enter a value ", borderwidth=2, font=10)

    text = tkinter.StringVar()
    entry = tkinter.Entry(root, textvariable=text)
    # e.bind('<Key>', key_press)

    button_1 = tkinter.Button(root, text="Enter Slope AVG Mode", command=lambda: toggle_state(out_q, entry.get()))

    label.pack()
    entry.pack()
    button_1.pack()
    root.mainloop()
