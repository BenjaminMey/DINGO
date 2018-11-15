import tkinter as tk

class EntrySelect(tk.Entry):
    """Entry widget with Return and Arrow Keys bound to traverse"""
    def __init__(self, master, next_wgt=None, prev_wgt=None, **kwargs):
        tk.Entry.__init__(self, master, **kwargs)
        self.link_widget(next_wgt, prev_wgt)
        self.bind('<Return>', self.select_next)
        self.bind('<Down>', self.select_next)
        self.bind('<Up>', self.select_prev)
    
    def link_widget(self, next=None, prev=None):  
        self.next_widget = next
        self.prev_widget = prev
        
    def select_next(self, event):
        if self.next_widget:
            self.event_generate('<<TraverseOut>>')
            self.next_widget.focus_set()
            self.next_widget.event_generate('<<TraverseIn>>')
        else:
            self.event_generate('<<NextWindow>>')
        return 'break'
            
    def select_prev(self, event):
        if self.prev_widget:
            self.event_generate('<<TraverseOut>>')
            self.prev_widget.focus_set()
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

class EntriesExpandable(tk.LabelFrame, tk.XView, tk.YView):
    """Entry list that will expand as needed"""
    def __init__(self, master, texts=None, **kwargs):
        tk.LabelFrame.__init__(self, master, **kwargs)
        
        self.entries = []
        if isinstance(texts, (unicode,str)):
            self.entries.append(self.add_entry(text=texts))
        elif isinstance(texts, (tuple,list)):
            for i in xrange(len(texts)):
                self.entries.append(self.add_entry(text=texts[i]))
        # last will checked for expansion, not returned by get
        self.entries.append(self.add_entry(text=''))
        self.grid_widgets()
        # link first to last and last to first for navigation
        self.entries[0][0].set_prev(self.entries[-1][0])
        self.entries[-1][0].set_next(self.entries[0][0])
        # select text in first
        self.entries[0][0].selection_range(0, tk.END)
        self.entries[0][0].focus_set()

    def add_entry(self, text=None, **kwargs):
        """Create Entry and its StringVar"""
        if text is not None:
            default_text = text
        else:
            default_text = ''
        var = tk.StringVar()
        var.set(default_text)
        entry = EntrySelect(self, textvariable=var)
        entry.configure(validate='focusout',
                        validatecommand=lambda x=entry : self.check_entry(x))
        entry.focus_set()
        return entry, var
        
    def grid_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        for i in xrange(len(self.entries)):
            self.entries[i][0].grid(row=i, column=0, sticky=tk.NSEW)
    
    def check_entry(self, entry):
        """Add or delete entry if needed"""
        if len(self.entries) == 0:
            return
        if entry.get() == '':
            if entry is self.entries[-1][0]:
                return True
            else:
                idx = [ entry is pair[0] for pair in self.entries ].index(True)
                self.del_entry(idx)
                return False
        else: #entry.get() != ''
            if entry is self.entries[-1][0]:
                self.entries.append(self.add_entry())
                self.grid_widgets()
                # reset previous last's next link
                self.entries[-2][0].set_next(None)
                # set new last and first link
                self.entries[0][0].set_prev(self.entries[-1][0])
                self.entries[-1][0].set_next(self.entries[0][0])
            return True
            
    def del_entry(self, i):
        self.entries[i][0].destroy()
        del self.entries[i]
        self.grid_widgets()
        
    def get(self):
        return [ pair[1].get() for pair in self.entries[:-1] ]

    def print_list(self):
        print(self.get())
        
class EntriesDict(tk.Frame):
        
def test_ee(args=None):
    root = tk.Tk()
    testlist = ['foo', 'bar', 'baz', 1, 2, 3]
    frame = EntriesExpandable(root, text='Header', texts=testlist, width=150, height=150)

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
