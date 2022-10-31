import multiprocessing
import tkinter


class VehicleData:
    width: float
    length: float
    height: float
    position: []
    num_wheels: int
    wheel_width: float
    wheel_radius: float
    back_overhang: float
    front_overhang: float
    path_points = []
    path_lines = []


def get_vehicle_data(gui_q, ):
    root = tkinter.Tk()
    root.title('Vehicle Attribute Selection')
    root.columnconfigure(0, weight=1)
    root.columnconfigure(1, weight=4)

    fields = {
        0: {'data': tkinter.StringVar(), 'default': '___', 'max_v': 10.0, 'min_v': 0.0,
            's_name': '__', 'name': 'Enter the required vehicle parameters'},
        1: {'data': tkinter.StringVar(), 'default': '1.0', 'max_v': 10.0, 'min_v': 0.1,
            's_name': 'back_overhang', 'name': 'Back Overhang'},
        2: {'data': tkinter.StringVar(), 'default': '0.8', 'max_v': 10.0, 'min_v': 0.1,
            's_name': 'front_overhang', 'name': 'Front Overhang'},
        6: {'data': tkinter.StringVar(), 'default': '3.0', 'max_v': 40.0, 'min_v': 1.0,
            's_name': 'length', 'name': 'Vehicle Length'},
        7: {'data': tkinter.StringVar(), 'default': '1.6', 'max_v': 20.0, 'min_v': 1.0,
            's_name': 'width', 'name': 'Vehicle Width'},

        3: {'data': tkinter.StringVar(), 'default': '0.8', 'max_v': 20.0, 'min_v': 0.1,
            's_name': 'wheel_radius', 'name': 'Wheel Radius'},
        4: {'data': tkinter.StringVar(), 'default': '0.2', 'max_v': 20.0, 'min_v': 0.1,
            's_name': 'wheel_width', 'name': 'Wheel Width'},
        5: {'data': tkinter.StringVar(), 'default': '4', 'max_v': 16.0, 'min_v': 1.0,
            's_name': 'num_wheels', 'name': 'Number of wheels'}
    }

    print('Enter vehicle attributes in dialog box')
    for i in range(0, 8):
        tkinter.Label(root, text=fields[i]['name'], borderwidth=2, font=10).grid(
            column=0, row=i, sticky=tkinter.W, padx=5, pady=5)
        if i == 0:
            continue
        else:
            fields[i]['data'].set(fields[i]['default'])
            ent = tkinter.Entry(root, textvariable=fields[i]['data'])
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