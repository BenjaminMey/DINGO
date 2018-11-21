import Tkinter as tk
import tkFileDialog as tkfd
import tkMessageBox as tkmb
import os
import sys
import json
import itertools
import platform
from DINGO.utils import read_config
from DINGO.base import DINGO

loremipsum = ('Lorem ipsum dolor sit amet, consectetur adipiscing elit, '
              'sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. '
              'Ut enim ad minim veniam, quis nostrud exercitation ullamco '
              'laboris nisi ut aliquip ex ea commodo consequat. '
              'Duis aute irure dolor in reprehenderit in voluptate velit '
              'esse cillum dolore eu fugiat nulla pariatur. '
              'Excepteur sint occaecat cupidatat non proident, '
              'sunt in culpa qui officia deserunt mollit anim id est laborum.')

shortlorem = 'Lorem ipsum dolor sit amet,'

class Mousewheel_Support(object):

    # implemetation of singleton pattern
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self, root, horizontal_factor=2, vertical_factor=2):
        
        self._active_area = None
        self.OS = platform.system()

        if isinstance(horizontal_factor, int):
            self.horizontal_factor = horizontal_factor
        else:
            raise Exception("Vertical factor must be an integer.")

        if isinstance(vertical_factor, int):
            self.vertical_factor = vertical_factor
        else:
            raise Exception("Horizontal factor must be an integer.")

        if platform.system() == "Linux":
            root.bind_all('<4>', self._on_mousewheel, add='+')
            root.bind_all('<5>', self._on_mousewheel, add='+')
        else:
            # Windows and MacOS
            root.bind_all("<MouseWheel>", self._on_mousewheel, add='+')

    def _on_mousewheel(self, event):
        if self._active_area:
            self._active_area.onMouseWheel(event)

    def _mousewheel_bind(self, widget):
        self._active_area = widget

    def _mousewheel_unbind(self):
        self._active_area = None

    def add_support_to(self, widget=None, xscrollbar=None, yscrollbar=None, what="units", horizontal_factor=None, vertical_factor=None):
        if xscrollbar is None and yscrollbar is None:
            return

        if xscrollbar is not None:
            horizontal_factor = horizontal_factor or self.horizontal_factor

            xscrollbar.onMouseWheel = self._make_mouse_wheel_handler(widget, 'x', self.horizontal_factor, what)
            xscrollbar.bind('<Enter>', lambda event, scrollbar=xscrollbar: self._mousewheel_bind(scrollbar))
            xscrollbar.bind('<Leave>', lambda event: self._mousewheel_unbind())

        if yscrollbar is not None:
            vertical_factor = vertical_factor or self.vertical_factor

            yscrollbar.onMouseWheel = self._make_mouse_wheel_handler(widget, 'y', self.vertical_factor, what)
            yscrollbar.bind('<Enter>', lambda event, scrollbar=yscrollbar: self._mousewheel_bind(scrollbar))
            yscrollbar.bind('<Leave>', lambda event: self._mousewheel_unbind())

        main_scrollbar = yscrollbar if yscrollbar is not None else xscrollbar

        if widget is not None:
            if isinstance(widget, list) or isinstance(widget, tuple):
                list_of_widgets = widget
                for widget in list_of_widgets:
                    widget.bind('<Enter>', lambda event: self._mousewheel_bind(widget))
                    widget.bind('<Leave>', lambda event: self._mousewheel_unbind())

                    widget.onMouseWheel = main_scrollbar.onMouseWheel
            else:
                widget.bind('<Enter>', lambda event: self._mousewheel_bind(widget))
                widget.bind('<Leave>', lambda event: self._mousewheel_unbind())

                widget.onMouseWheel = main_scrollbar.onMouseWheel

    @staticmethod
    def _make_mouse_wheel_handler(widget, orient, factor=1, what="units"):
        view_command = getattr(widget, orient + 'view')

        if platform.system() == 'Linux':
            def onMouseWheel(event):
                if event.num == 4:
                    view_command("scroll", (-1) * factor, what)
                elif event.num == 5:
                    view_command("scroll", factor, what)

        elif platform.system() == 'Windows':
            def onMouseWheel(event):
                view_command("scroll", (-1) * int((event.delta / 120) * factor), what)

        elif platform.system() == 'Darwin':
            def onMouseWheel(event):
                view_command("scroll", event.delta, what)

        return onMouseWheel

class DINGOFile(tk.Frame):
    def __init__(self, parent, default_filename=''):
        tk.Frame.__init__(self, parent)
        
        self.file_label = tk.Label(self, text=default_filename)
        self.file_label.pack()
        
        self.new = tk.Button(self, text='New', command=self.new_config(parent))
        
        self.open = tk.Button(self, text='Open', command=self.open_json)
        self.open.pack(side=LEFT)
        
        self.save = tk.Button(self, text='Save', command=self.save_json)
        self.save.pack(side=LEFT)
        
    def new_config(self, parent):
        keys = []
        for tup in DINGO.default_expected_keys:
            if isinstance(tup[0],(unicode,str)):
                keys.append(tup[0])
            elif isinstance(tup[0],(tuple,list)):
                keys.append(tup[0][0])
        config = dict(zip(keys, itertools.repeat(None)))
        parent.update_options(config)
        
    def open_json(self):
        self.filename = tkfd.askopenfilename(
            initaldir=os.getcwd(), 
            title='Select file', 
            filetypes=(('json files','*.json'),('all files','*.*')))
        try:
            config = read_config(self.filename)
        except IOError:
            config = None
        return config
        
    def save_json(self, adict):
        filename = self.filename.get()
        with open(filename, 'w') as f:
            json.dump(adict, f)
            
class DINGOOptions(tk.Frame):
    def __init__(self, parent, config=None):
        tk.Frame.__init__(self, parent)
        
        self.scrollbar = tk.Scrollbar(self)
        self.scrollbar.pack(side=RIGHT,fill=Y)
        
        self.listbox = tk.ListBox(self)
        
    def make_options_widget(self, k, v):
        print('k: {}, v: {}'.format(k,v))
        if isinstance(v,(unicode,str)):
            pass
            
    def make_input_widget(self, aninput):
        pass

class HidePrint():
    def __enter__(self):
        self._orig_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._orig_stdout

class DINGOApp(tk.Tk):
    def __init__(self, label='DINGO', filename=None):
        tk.Tk.__init__(self)
        self.grid_columnconfigure(0,weight=1)
        self.grid_rowconfigure(0,weight=1)
        self.resizable(True, False)
        frame = tk.LabelFrame(self, text='DINGO Config Editing')
        self.create_widgets()
        self.grid_widgets()
        self.grid_columnconfigure(0, weight=1)
        self.update_options(config)
    
    #@classmethod
    #def main(cls):
        #tk.NoDefaultRoot()
        #root = tk.Tk()
        #app = cls(root)
        #app.grid_columnconfigure(0,weight=1)
        #app.grid_rowconfigure(0,weight=1)
        #root.resizable(True, False)
        #root.mainloop()
            
    def create_widgets(self, filename=None):
        self.setup = DINGOFile(self)
        self.setup.pack()
        
        if filename is not None:
            config = self.setup.open_json(filename)
        if config is not None:
            try:
                aDINGO.check_input_fields('DINGOApp', config, DINGO.default_expected_keys)
            except Exception as err:
                handle_create_error(err)
                
        self.options = DINGOOptions(self)
        self.options.pack()
        
        self.run = tk.Button(self, text='Run', command=run_DINGO)
        self.run.pack()
        
        self.plugin = tk.Entry(self, text='Linear')
        self.plugin.pack(side=LEFT)
        
        self.plugin_args = Extra_entry()
        self.plugin_args.pack(side=LEFT)
        
    def grid_widgets(self):
        options = dict(sticky=NSEW, padx=4, pady=4)
        self.setup.grid(column=0, row=0, **options)
        self.options.grid(column=0, row=1, **options)
        self.run.grid(column=0, row=2, **options)
        self.runplugin.grid(column=0, row=2, **options)
        
    def update_options(self, config):
        for k,v in config.iteritems():
            DINGOOptions.make_options_widget(k,v)
            
    def handle_create_error(err):
        tkmb.showerror('DINGO Creation Error', err)
    
    def handle_run_error():
        raise NotImplementedError
            
    def run_DINGO(self, config):
        with HidePrint():
            aDINGO = DINGO()
        try:
            aDINGO.create_wf_from_config(cfg=config)
        except Exception as err:
            handle_create_error(err)
            
        try:
            aDINGO.run(**runoptions)
        except Exception as err:
            handle_run_error(err)
        
