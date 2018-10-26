import Tkinter as tk
import tkFileDialog as tkfd
import tkMessageBox as tkmb
import os
import sys
import json
import itertools
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

class Extra_entry(tk.Frame):
    def __init__(self, parent):
        self.scrollbar = tk.Scrollbar(self)
        self.scrollbar.pack(side=RIGHT, fill=Y)
        self.variables = []
        self.entries = []
        self.add_entry(0)
        
    def callback():
        for var in self.variables:
            if var.get() == '':
                idx = self.variables.index(var)
                self.variables.pop(idx)
                entry = self.entries.pop(idx)
                entry.destroy()
                
        
    def add_entry(self, newentry):
        self.variables.append(tk.StringVar(self))
        self.entries.append(tk.Entry(self, 
                                    textvariable=self.variables[newentry],
                                    validate='focusout',
                                    validatecommand=callback))
        self.entries[newentry].pack()

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
        
