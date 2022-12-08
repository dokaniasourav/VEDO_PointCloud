import PySimpleGUI as PySG


class GuiHeaderElement:
    def __init__(self,
                 _title: str):
        self.key_base = ''
        self.name = '\n' + _title

        _font = 'Helvetica 12'
        self.pad1 = PySG.Text('', size=(20, 1), font=_font)
        self.pad2 = PySG.Text('', size=(20, 1), font=_font)
        self.label = PySG.Text(_title, size=(20, 1), font=_font)
        self.elements: list[PySG.Element] = [self.pad1, self.label, self.pad2]


class GuiInputElement:
    def __init__(self,
                 _min: float,
                 _max: float,
                 _name: str,
                 _default: float):
        self.max = _max
        self.min = _min
        self.key = _name.replace(' ', '') + '_01'
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
                 _step: float,
                 _default: float):
        self.max = _max
        self.min = _min
        self.key_base = _name.replace(' ', '')
        self.label = _name
        self.default = _default

        _font = 'Helvetica 12'

        self.label_ele = PySG.Text(_name, size=(14, 1), font=_font)
        self.input_ele = PySG.InputText(key=self.key_base + '_out',
                                        enable_events=True, size=(6, 1),
                                        pad=10, font=_font,
                                        default_text=str(_default))
        self.slider_ele = PySG.Slider(range=(_min, _max),
                                      default_value=_default,
                                      key=self.key_base + '_inp',
                                      orientation='h', font=_font,
                                      resolution=_step, disable_number_display=True,
                                      enable_events=True)
        # self.slider_txt_ele = PySG.Text('', size=(10, 1), key=self.key_base+'_out')
        self.elements: list[PySG.Element] = [self.label_ele, self.input_ele, self.slider_ele]


class GuiConfirmButtons:
    def __init__(self):
        self.key_base = ''
        _size = (10, 1)
        self.elements: list[PySG.Element] = [PySG.OK(size=_size),
                                             PySG.Button('Save', size=_size),
                                             PySG.Button('Exit', size=_size)]


class MainGui:

    def __init__(self):
        PySG.theme('Reddit')
        PySG.user_settings_filename(path='.')

        self.elements = [
            GuiHeaderElement('Vehicle Attributes: '),
            GuiSliderElement(0.5, 30, 'Vehicle Length', 0.2, 10.0),
            GuiSliderElement(0.5, 15, 'Vehicle Width', 0.2, 6.0),
            GuiSliderElement(0.2, 25, 'Front Overhang', 0.2, 3.0),
            GuiSliderElement(0.2, 25, 'Back Overhang', 0.2, 3.0),

            GuiHeaderElement(''),
            GuiHeaderElement('Wheel Attributes: '),
            GuiSliderElement(0.1, 5, 'Wheel Radius', 0.1, 2.0),
            GuiSliderElement(0.1, 1, 'Wheel Width', 0.05, 0.2),

            GuiHeaderElement(''),
            GuiHeaderElement('Simulation Parameters: '),
            GuiSliderElement(1, 500, 'Number Of Points', 1, 5),

            GuiConfirmButtons()
        ]

        self.layout = []
        self.inp_keys = []
        self.out_keys = []
        for ele in self.elements:
            self.layout.append(ele.elements)
            _inp_key = ele.key_base+'_inp'
            _out_key = ele.key_base+'_out'
            self.inp_keys.append(_inp_key)
            self.out_keys.append(_out_key)

        self.output_dict: dict[str, str] = {}

    def show_gui(self):

        window = PySG.Window('Enter the Vehicle Attributes Box Below', self.layout, finalize=True)

        # Update the GUI Application
        for ele in self.elements:
            _inp_key = ele.key_base+'_inp'
            _out_key = ele.key_base+'_out'

            if len(_inp_key) > 4 and len(_out_key) > 4:
                _get_val = PySG.user_settings_get_entry(_out_key, 0.1)
                window[_inp_key].update(_get_val)
                window[_out_key].update(_get_val)

        while True:
            event, values = window.read()
            if event is None:
                return
            if event == 'Cancel' or event == 'Exit':
                window.close()
                return

            if event == 'Save':
                for key in self.out_keys:
                    if len(key) > 4:
                        PySG.user_settings_set_entry(key, values[key])

            if event in self.inp_keys:
                out_val = values[event]
                index = self.inp_keys.index(event)
                out_key = self.out_keys[index]
                window[out_key].update(str(out_val))
            elif event in self.out_keys:
                out_val = values[event]
                index = self.out_keys.index(event)
                out_key = self.inp_keys[index]
                window[out_key].update(str(out_val))

            # print(event, values)

            if event == 'OK':
                for value in values:
                    if '_out' in value:
                        value_strip = value.split('_')[0]
                        self.output_dict[value_strip] = values[value]
                window.close()
                return
