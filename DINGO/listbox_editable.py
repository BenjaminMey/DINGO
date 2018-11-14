import tkinter as tk
from tkinter import ttk
from pprint import pprint


class ListboxEditable(object):
    """Act as listbox, but convert to entry upon selection, then update"""
    def __init__(self, master, alist, font='Calibri', size=12, 
    ColorActive='#E3E3E3', ColorNotActive='#C9C9C9'):
        self.master = master
        self.mylist = alist
        self.NRows = len(self.mylist)
        self.font = font
        self.size = size
        self.ColorActive = ColorActive
        self.ColorNotActive = ColorNotActive
        self.create_widgets()
        self.grid_widgets()
        
    def create_widgets(self):
        self.entryVar = tk.StringVar()
        self.entry = tk.Entry(self.master, textvariable=self.entryVar, 
                font=(self.font, self.size), width=20, borderwidth=2)
        
        self.numbers = []
        self.editables = []
        for i in xrange(len(self.mylist) + 1):
            self.add_label(i)
        print('NRows: %s' % self.NRows)
        print('len(editables): %s' % len(self.editables))
    
    def add_label(self, i, fg_color='black', bw=2, jfy=tk.LEFT):
        if i == self.NRows:
            self.NRows = self.NRows + 1
            self.mylist.append('')
            n_prefix = 'Add '
        else:
            n_prefix = ''
        self.numbers.append(tk.Label(self.master,
                text=''.join((n_prefix, str(i), ':')), 
                font=(self.font, self.size),
                foreground=fg_color, background=self.ColorNotActive,
                borderwidth=bw, width=5, justify=jfy))
        self.editables.append(tk.Label(self.master, 
                text=str(self.mylist[i]),
                font=(self.font, self.size), 
                foreground=fg_color, background=self.ColorNotActive,   
                borderwidth=bw, width=20, justify=jfy))
                
        self.editables[i].bind('<Button-1>', lambda event, x=i :
                self.select(x))
        self.editables[i].bind('<Up>', lambda event, x=i :
                self.select_up(x))
        self.editables[i].bind('<Down>', lambda event, x=i : 
                self.select_down(x))
        self.editables[i].bind('<Double-1>', lambda event, x=i : 
                self.label2entry(x))
        self.editables[i].bind('<Return>', lambda event, x=i : 
                self.label2entry(x))
        self.numbers[i].bind('<Button-1>', lambda event, x=i :
                self.select(x))
        self.numbers[i].bind('<Double-1>', lambda event, x=i : 
                self.label2entry(x))
        
    def del_label(self, i):
        self.NRows = self.NRows - 1
        del self.mylist[i]
        self.editables[i].destroy()
        del self.editables[i]
        self.numbers[-1].destroy()
        del self.numbers[-1]
                       
    def grid_widgets(self):
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_columnconfigure(1, weight=4)
        for i in xrange(self.NRows):
            self.numbers[i].grid(row=i, column=0)
            self.editables[i].grid(row=i, column=1)
    
    def select(self, selection):
        print(selection)
        pprint(self.__dict__, indent=2)
        for i in xrange(self.NRows):
            self.editables[i].configure(background=self.ColorNotActive)
        self.editables[selection].configure(background=self.ColorActive)
        self.editables[selection].focus_set()
        
    def select_up(self, curSelection):
        if curSelection == 0:
            next = self.NRows - 1
        else:
            next = curSelection - 1
        self.select(next)
        
    def select_down(self, curSelection):
        if curSelection == self.NRows - 1:
            next = 0
        else:
            next = curSelection + 1
        self.select(next)
        
    def label2entry(self, i):
        self.editables[i].grid_forget()
        self.entryVar.set(self.mylist[i])
        self.entry.selection_range(0, tk.END)
        self.entry.grid(row=i, column=1)
        self.entry.focus_set()
        
        self.entry.bind('<FocusOut>', lambda event, x=i : self.entry2label(x))
        self.entry.bind('<Return>', lambda event, x=i : self.entry2label(x))
        
    def entry2label(self, i):
        e = self.entryVar.get()
        self.mylist[i] = e
        self.editables[i].configure(text=e)
        self.entry.grid_forget()
        self.editables[i].grid(row=i, column=1)
        #default
        self.select(i)
        #lastrow == '' -> update label
        #otherrow != '' -> update label
        #lastrow != '' -> add row
        #otherrow == '' -> del row
        print('i: %s, e: %s' % (i,e))
        if i == self.NRows and e != '':
            self.del_label(i)
            self.add_label(i)
            self.grid_widgets()

def main():
    testlist = ['foo', 'bar', 'baz', 1, 2, 3]
    root = tk.Tk()
    mainframe = tk.Frame(root, bg='#C9C9C9')
    header = tk.Label(mainframe, text='Header', font=('Calibri', 16, 'bold'), 
            padx=4, pady=4, background='#C9C9C9')
    frame_listbox = tk.Frame(mainframe, bg='#C9C9C9')
    listbox = ListboxEditable(frame_listbox, testlist)
    
    mainframe.grid(row=0, column=0)
    header.grid(row=0, column=0, columnspan=1)
    frame_listbox.grid(row=1, column=0)
    
    root.mainloop()

if __name__ == '__main__':
    main()
    
