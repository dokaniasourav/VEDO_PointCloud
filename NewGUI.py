import random

import PySimpleGUI as PySG


class GuiHeaderElement:
    def __init__(self,
                 _title: str):
        self.key = _title.replace(' ', '') + '_' + str(random.randint(1000, 9999))
        self.name = _title

        self.label = PySG.Text(_title, size=(10, 1))
        self.elements: list[PySG.Element] = [self.label]


class GuiInputElement:
    def __init__(self,
                 _min: float,
                 _max: float,
                 _name: str,
                 _default: float):
        self.max = _max
        self.min = _min
        self.key = _name.replace(' ', '') + '_' + str(random.randint(1000, 9999))
        self.name = _name
        self.default = _default

        self.label = PySG.Text(_name, size=(10, 1))
        self.input = PySG.InputText(key=self.key)
        self.elements: list[PySG.Element] = [self.label, self.input]


class GuiSliderElement:
    def __init__(self,
                 _min: float,
                 _max: float,
                 _name: str,
                 _default: float):
        self.max = _max
        self.min = _min
        self.key_base = _name.replace(' ', '') + '_' + str(random.randint(1000, 9999))
        self.label = _name
        self.default = _default
        self.label_ele = PySG.Text(_name, size=(10, 1))
        self.slider_ele = PySG.Slider(range=(_min, _max),
                                      default_value=_default,
                                      key=self.key_base + '_inp',
                                      orientation='h',
                                      resolution=0.1, disable_number_display=True,
                                      enable_events=True)
        self.slider_txt_ele = PySG.Text('', size=(10, 1), key=self.key_base+'_out')

        self.elements: list[PySG.Element] = [self.label_ele, self.slider_ele, self.slider_txt_ele]


class MainGui:

    main_inputs = ['width', 'length', 'front_overhang', 'back_overhang',
                   'wheel_radius', 'wheel_width', 'num_wheels']

    def __init__(self):
        self.elements = [
            GuiHeaderElement('Enter the Vehicle Attributes Below'),
            GuiSliderElement(0.1, 30, 'Width ', 0.1),
            GuiSliderElement(0.1, 30, 'Height', 0.1)
        ]

        self.layout = []
        for ele in self.elements:
            self.layout.append(ele.elements)

        print(self.layout)
        window = PySG.Window('Simple Data Entry Window', self.layout)

        while True:
            event, values = window.read()
            if event is None:
                return
            if event == 'Cancel':
                window.close()
                return
            # inp_key = self.e4.key_base + '_inp'
            # out_key = self.e4.key_base + '_out'
            # if event == inp_key:
            #     out_val = values[inp_key]
            #     window[out_key].update(str(out_val))

            print(event, values)


MainGui()