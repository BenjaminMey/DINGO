import tkinter as tk
from DINGO.gui import Mousewheel_Support

class EntrySelect(tk.Entry):
    """Entry widget with Return and Arrow Keys bound to traverse"""
    def __init__(self, master, next_wgt=None, prev_wgt=None, **kwargs):
        tk.Entry.__init__(self, master, **kwargs)
        self.link_widget(next_wgt, prev_wgt)
        self.bind('<Return>', self.select_next)
        self.bind('<Down>', self.select_next)
        self.bind('<Up>', self.select_prev)
        self.bind('<<TraverseIn>>', self._on_traverse_in)
        self.bind('<<TraverseOut>>', self._on_traverse_out)
        self.bind('<FocusIn>', self._on_focus_in)

    def _on_focus_in(self, event):
        self.selection_range(0, tk.END)
        self.master.event_generate('<<ChildFocus>>')

    def _on_focus_out(self, event):
        self.xview_moveto(0)
        self.selection_clear()

    def _on_traverse_in(self, event):
        self.focus_set()
        pass

    def _on_traverse_out(self, event):
        self._on_focus_out(event)
    
    def link_widget(self, next=None, prev=None):  
        self.next_widget = next
        self.prev_widget = prev
        
    def select_next(self, event):
        if self.next_widget is not None:
            self.event_generate('<<TraverseOut>>')
            self.next_widget.event_generate('<<TraverseIn>>')
        else:
            self.event_generate('<<NextWindow>>')
        return 'break'
            
    def select_prev(self, event):
        if self.prev_widget is not None:
            self.event_generate('<<TraverseOut>>')
            self.prev_widget.event_generate('<<TraverseIn>>')
        else:
            self.event_generate('<<PrevWindow>>')
        return 'break'
        
    def set_next(self, widget):
        """Override the default next widget for this instance"""
        self.next_widget = widget
        
    def set_prev(self, widget):
        """Override the default previous widget for this instance"""
        self.prev_widget = widget

class EntriesExpandable(tk.LabelFrame, object):
    """Entry list that will expand as needed"""
    def __init__(self, master, texts=None, height=None, width=None, **kwargs):
        tk.LabelFrame.__init__(self, master, height=height, width=width, **kwargs)
        self.canvas = tk.Canvas(self, background='#E70000')
        self.yscrollbar = tk.Scrollbar(self, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.yscrollbar.set)
        self.entryframe = tk.Frame(self.canvas, height=height, width=width)
        self.canvas.create_window(0, 0, window=self.entryframe, tags='entryframe', anchor=tk.NW)

        Mousewheel_Support(self).add_support_to(self.canvas, yscrollbar=self.yscrollbar)
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        self.entryframe.bind('<<ChildFocus>>', self._show_entry)
        
        self.entries = []
        if isinstance(texts, (unicode,str)):
            self.add_entry(text=texts)
        elif isinstance(texts, (tuple,list)):
            for i in xrange(len(texts)):
                self.add_entry(text=texts[i], row=i)
        # last will be checked for expansion, not returned by get
        self.add_entry(text='', row=len(texts))
        self.grid_widgets()
        # link first to last and last to first for navigation
        self.entries[0][0].set_prev(self.entries[-1][0])
        self.entries[-1][0].set_next(self.entries[0][0])
        # select text in first
        self.entries[-1][0].focus_set()

    def grid_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.canvas.grid(row=0, column=0, sticky=tk.NSEW)
        self.yscrollbar.grid(row=0, column=1, sticky=tk.NS)

    def grid_entries(self, row, height=None, width=None, ):
        """Regrid entries greater than or equal to given row"""
        if width is None:
            width = max(self.entryframe.winfo_reqwidth(), 
                        self.canvas.winfo_reqwidth())
        if height is None:
            height = max(self.entryframe.winfo_reqheight(),
                         self.canvas.winfo_reqheight())
        self.resize_canvas_scroll(width, height)
        for i in xrange(row,len(self.entries)):
            self.entries[i][0].grid(row=i, column=0, sticky=tk.NSEW)

    def resize_canvas_scroll(self, width, height):
        self.canvas.configure(scrollregion='0 0 {} {}'.format(width, height))
        self.canvas.itemconfigure('entryframe', width=width, height=height)

    def _on_canvas_configure(self, event):
        width = max(self.entryframe.winfo_reqwidth(), event.width)
        height = max(self.entryframe.winfo_reqheight(), event.height)
        self.resize_canvas_scroll(width, height)

    def _show_entry(self, event, i):
        entry = event.widget
        idx = [ entry is pair[0] for pair in self.entries ].index(True)
        fraction = float(idx)/float(len(self.entries))
        self.canvas.yview_moveto(fraction)

    def add_entry(self, text=None, row=None, **kwargs):
        """Create Entry and its StringVar"""
        if text is not None:
            default_text = text
        else:
            default_text = ''
        if row is None:
            row = 0
        if row == -1:
            row = len(self.entries)
        var = tk.StringVar()
        var.set(default_text)
        entry = EntrySelect(self.entryframe, textvariable=var, **kwargs)
        entry.configure(validate='focusout',
                        validatecommand=lambda x=entry : self._check_entry(x))
        entry.bind('<FocusIn>', lambda event, i=row: self._show_entry(event, i))
        self.entries.append((entry, var))

        width = max(self.entryframe.winfo_reqwidth(), 
                        self.canvas.winfo_reqwidth())
        # height should include extra empty widget
        height = max(self.entryframe.winfo_reqheight() + 
                            entry.winfo_reqheight(),
                         self.canvas.winfo_reqheight())
        self.grid_entries(row, height, width)
        self.canvas.yview_moveto(1.0)
        
        entry.focus_set()
        return entry, var

    def del_entry(self, i):
        self.entries[i][0].destroy()
        del self.entries[i]
        self.grid_entries(i)
    
    def _check_entry(self, entry):
        """Add or delete entry if needed"""
        if len(self.entries) == 0:
            return
        if entry.get() == '':
            if entry is self.entries[-1][0]:
                return True
            else:
                idx = [ entry is pair[0] for pair in self.entries ].index(True)
                if entry is self.entries[0][0]:
                    self.entries[1][0].set_prev(self.entries[-1][0])
                    self.entries[-1][0].set_next(self.entries[1][0])
                self.del_entry(idx)
                return False
        else: #entry.get() != ''
            if entry is self.entries[-1][0]:
                self.add_entry(row=-1)
                # reset previous last's next link
                self.entries[-2][0].set_next(None)
                # set new last and first link
                self.entries[0][0].set_prev(self.entries[-1][0])
                self.entries[-1][0].set_next(self.entries[0][0])
            return True
        
    def get(self):
        return [ pair[1].get() for pair in self.entries[:-1] ]

    def print_list(self):
        print(self.get())
        
        
def test_ee(args=None):
    root = tk.Tk()
    testlist = ['foo', 'bar', 'baz', 1, 2, 3]
    frame = EntriesExpandable(root, text='Header', texts=testlist)

    exit_button = tk.Button(root, text='Exit', command=root.destroy)
    get_button = tk.Button(root, text='Print', command=frame.print_list)

    frame.grid(row=0, column=0, sticky=tk.NSEW)
    exit_button.grid(row=1, column=1, sticky=tk.SE)
    get_button.grid(row=1, column=0, sticky=tk.SE)
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)
    root.mainloop()

if __name__ == '__main__':
    test_ee()
