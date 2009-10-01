""" CellProfiler.CellProfilerGUI.CPFrame - Cell Profiler's main window

CellProfiler is distributed under the GNU General Public License.
See the accompanying file LICENSE for details.

Developed by the Broad Institute
Copyright 2003-2009

Please see the AUTHORS file for credits.

Website: http://www.cellprofiler.org
"""
__version__="$Revision$"

import os
import wx
import wx.html
import wx.lib.scrolledpanel
import cellprofiler.preferences
from cellprofiler.gui import get_icon, get_cp_bitmap
from cellprofiler.gui.pipelinelistview import PipelineListView
from cellprofiler.gui.cpfigure import close_all
from cellprofiler.pipeline import Pipeline
from cellprofiler.gui.pipelinecontroller import PipelineController
from cellprofiler.gui.moduleview import ModuleView
from cellprofiler.gui.preferencesview import PreferencesView
from cellprofiler.gui.directoryview import DirectoryView
import cellprofiler.gui.preferencesdlg
import traceback
import sys

ID_FILE_LOAD_PIPELINE=wx.NewId()
ID_FILE_EXIT=wx.NewId()
ID_FILE_WIDGET_INSPECTOR=wx.NewId()
ID_FILE_SAVE_PIPELINE=wx.NewId()
ID_FILE_CLEAR_PIPELINE=wx.NewId()
ID_FILE_ANALYZE_IMAGES=wx.NewId()
ID_FILE_STOP_ANALYSIS=wx.NewId()

ID_OPTIONS_PREFERENCES = wx.NewId()

ID_DEBUG_START = wx.NewId()
ID_DEBUG_STOP = wx.NewId()
ID_DEBUG_STEP = wx.NewId()
ID_DEBUG_NEXT_IMAGE_SET = wx.NewId()
ID_DEBUG_NEXT_GROUP = wx.NewId()

ID_WINDOW_CLOSE_ALL = wx.NewId()
ID_WINDOW_SHOW_ALL_FRAMES = wx.NewId()
ID_WINDOW_HIDE_ALL_FRAMES = wx.NewId()

ID_HELP_MODULE=wx.NewId()

class CPFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        """Initialize the frame and its layout
        
        """
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.BackgroundColour = cellprofiler.preferences.get_background_color()
        self.__top_left_panel = wx.Panel(self,-1)
        self.__logo_panel = wx.Panel(self,-1,style=wx.RAISED_BORDER)
        self.__module_list_panel = wx.Panel(self.__top_left_panel,-1)
        self.__module_controls_panel = wx.Panel(self.__top_left_panel,-1)
        self.__module_panel = wx.lib.scrolledpanel.ScrolledPanel(self,-1,style=wx.SUNKEN_BORDER)
        self.__file_list_panel = wx.Panel(self,-1)
        self.__preferences_panel = wx.Panel(self,-1)
        self.__pipeline = Pipeline()
        self.__add_menu()
        self.__attach_views()
        self.__set_properties()
        self.__set_icon()
        self.__layout_logo()
        self.__do_layout()
        self.__error_listeners = []
        self.Bind(wx.EVT_SIZE,self.__on_size,self)
        self.tbicon = wx.TaskBarIcon()
        self.tbicon.SetIcon(get_icon(), "CellProfiler2.0")

    def OnClose(self, event):
        self.tbicon.Destroy()
        self.Destroy()
 
    def __set_properties(self):
        self.SetTitle("CellProfiler")
        self.SetSize((640, 480))
 
    def __add_menu(self):
        """Add the menu to the frame
        
        """
        self.__menu_bar = wx.MenuBar()
        self.__menu_file = wx.Menu()
        self.__menu_file.Append(ID_FILE_LOAD_PIPELINE,'Load Pipeline...\tctrl+P','Load a pipeline from a .MAT file')
        self.__menu_file.Append(ID_FILE_SAVE_PIPELINE,'Save Pipeline as...','Save a pipeline as a .MAT file')
        self.__menu_file.Append(ID_FILE_CLEAR_PIPELINE,'Clear pipeline','Remove all modules from the current pipeline')
        self.__menu_file.AppendSeparator()
        self.__menu_file.Append(ID_FILE_ANALYZE_IMAGES,'Analyze images\tctrl+N','Run the pipeline on the images in the image directory')
        self.__menu_file.Append(ID_FILE_STOP_ANALYSIS,'Stop analysis','Stop running the pipeline')
        self.__menu_file.AppendSeparator()
        self.__menu_file.Append(ID_OPTIONS_PREFERENCES,"&Preferences...","Set global application preferences")
        # self.__menu_file.Append(ID_FILE_WIDGET_INSPECTOR,'Widget inspector','Run the widget inspector for debugging the UI')
        self.__menu_file.Append(ID_FILE_EXIT,'E&xit\tctrl+Q','Quit the application')
        self.__menu_bar.Append(self.__menu_file,'&File')
        self.__menu_debug = wx.Menu()
        self.__menu_debug.Append(ID_DEBUG_START,'&Start test run\tF5','Start the pipeline debugger')
        self.__menu_debug.Append(ID_DEBUG_STOP,'S&top test run\tctrl+F5','Stop the pipeline debugger')
        self.__menu_debug.Append(ID_DEBUG_STEP,'Ste&p to next module\tF6','Execute the currently selected module')
        self.__menu_debug.Append(ID_DEBUG_NEXT_IMAGE_SET,'&Next image set\tF7','Advance to the next image set')
        self.__menu_debug.Append(ID_DEBUG_NEXT_GROUP, 'Next &group\tF8','Advance to the next group in the image set')
        self.__menu_debug.Enable(ID_DEBUG_STOP,False)
        self.__menu_debug.Enable(ID_DEBUG_STEP,False)
        self.__menu_debug.Enable(ID_DEBUG_NEXT_IMAGE_SET,False)
        self.__menu_debug.Enable(ID_DEBUG_NEXT_GROUP, False)
        self.__menu_bar.Append(self.__menu_debug,'&Test')
        self.__menu_window = wx.Menu()
        self.__menu_window.Append(ID_WINDOW_CLOSE_ALL, "Close &all\tctrl+L", 
                                  "Close all figure windows")
        self.__menu_window.Append(ID_WINDOW_SHOW_ALL_FRAMES,"Show all frames",
                                  "Show all module display frames for all modules during analysis")
        self.__menu_window.Append(ID_WINDOW_HIDE_ALL_FRAMES,"Hide all frames",
                                  "Hide all module display frames for all modules during analysis")
        self.__menu_bar.Append(self.__menu_window,"&Window")
        self.__menu_help = wx.Menu()
        self.__menu_help.Append(ID_HELP_MODULE,'Module help','Display help from the module''s .m file')
        self.__menu_bar.Append(self.__menu_help,'&Help')
        self.SetMenuBar(self.__menu_bar)
        wx.EVT_MENU(self,ID_FILE_EXIT,lambda event: self.Close())
        wx.EVT_MENU(self,ID_FILE_WIDGET_INSPECTOR,self.__on_widget_inspector)
        wx.EVT_MENU(self,ID_HELP_MODULE,self.__on_help_module)
        wx.EVT_MENU(self,ID_OPTIONS_PREFERENCES, self.__on_preferences)
        wx.EVT_MENU(self,ID_WINDOW_CLOSE_ALL, self.__on_close_all)
        accelerator_table = wx.AcceleratorTable([(wx.ACCEL_CTRL,ord('N'),ID_FILE_ANALYZE_IMAGES),
                                                 (wx.ACCEL_CTRL,ord('P'),ID_FILE_LOAD_PIPELINE),
                                                 (wx.ACCEL_CTRL,ord('L'),ID_WINDOW_CLOSE_ALL),
                                                 (wx.ACCEL_CTRL,ord('Q'),ID_FILE_EXIT),
                                                 (wx.ACCEL_NORMAL,wx.WXK_F5,ID_DEBUG_START),
                                                 (wx.ACCEL_CTRL,wx.WXK_F5,ID_DEBUG_STOP),
                                                 (wx.ACCEL_NORMAL,wx.WXK_F6,ID_DEBUG_STEP),
                                                 (wx.ACCEL_NORMAL,wx.WXK_F7,ID_DEBUG_NEXT_IMAGE_SET),
                                                 (wx.ACCEL_NORMAL,wx.WXK_F8,ID_DEBUG_NEXT_GROUP)])
        self.SetAcceleratorTable(accelerator_table)
    
    def enable_debug_commands(self, enable=True):
        """Enable or disable the debug commands (like ID_DEBUG_STEP)"""
        self.__menu_debug.Enable(ID_DEBUG_START,not enable)
        self.__menu_debug.Enable(ID_DEBUG_STOP,enable)
        self.__menu_debug.Enable(ID_DEBUG_STEP,enable)
        self.__menu_debug.Enable(ID_DEBUG_NEXT_IMAGE_SET,enable)
        self.__menu_debug.Enable(ID_DEBUG_NEXT_GROUP, enable)
        
    def __on_widget_inspector(self, evt):
        try:
            import wx.lib.inspection
            wx.lib.inspection.InspectionTool().Show()
        except:
            wx.MessageBox("Inspection tool is not available on this platform")

    def __on_preferences(self, event):
        dlg = cellprofiler.gui.preferencesdlg.PreferencesDlg()
        dlg.show_modal()
    
    def __on_close_all(self, event):
        close_all(self)
        
    def __on_help_module(self,event):
        modules = self.__pipeline_list_view.get_selected_modules()
        self.do_help_modules(modules)
        
    def do_help_modules(self, modules):
        for module in modules:
            self.do_help_module(module.module_name, module.get_help())
    
    def do_help_module(self, module_name, help_text):
        helpframe = wx.Frame(self,-1,'Help for module, "%s"' %
                             (module_name),size=(640,480))
        sizer = wx.BoxSizer()
        helpframe.SetSizer(sizer)
        if False:
            font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FIXED_FONT)
            bgcolor = wx.SystemSettings.GetColour(wx.SYS_COLOUR_LISTBOX)
            panel = wx.lib.scrolledpanel.ScrolledPanel(helpframe,-1,style=wx.SUNKEN_BORDER)
            panel.SetBackgroundColour(bgcolor)
            sizer.Add(panel,1,wx.EXPAND)
            statictext = wx.StaticText(panel,-1, help_text)
            statictext.SetFont(font)
            statictext.SetBackgroundColour(bgcolor)
            sizer = wx.BoxSizer()
            sizer.Add(statictext,1,wx.EXPAND|wx.ALL,5)
            panel.SetSizer(sizer)
            panel.SetupScrolling()
        else:
            window = wx.html.HtmlWindow(helpframe)
            sizer.Add(window,1,wx.EXPAND)
            window.AppendToPage(help_text)
        helpframe.SetIcon(get_icon())
        helpframe.Layout()
        helpframe.Show()
        
    def __attach_views(self):
        self.__pipeline_list_view = PipelineListView(self.__module_list_panel)
        self.__pipeline_controller = PipelineController(self.__pipeline,self)
        self.__pipeline_list_view.attach_to_pipeline(self.__pipeline,self.__pipeline_controller)
        self.__pipeline_controller.attach_to_module_controls_panel(self.__module_controls_panel)
        self.__module_view = ModuleView(self.__module_panel,self.__pipeline)
        self.__pipeline_controller.attach_to_module_view(self.__module_view)
        self.__pipeline_list_view.attach_to_module_view((self.__module_view))
        self.__preferences_view = PreferencesView(self.__preferences_panel)
        self.__preferences_view.attach_to_pipeline_controller(self.__pipeline_controller)
        self.__directory_view = DirectoryView(self.__file_list_panel)
        self.__pipeline_controller.attach_to_directory_view(self.__directory_view)
        
    def __do_layout(self):
        self.__sizer = CPSizer(2,2,0,1)
        self.__top_left_sizer = wx.FlexGridSizer(3,1,1,1)
        self.__top_left_sizer.Add(self.__logo_panel,0,wx.EXPAND|wx.ALL,1)
        self.__top_left_sizer.Add(self.__module_list_panel,1,wx.EXPAND|wx.ALL,1)
        self.__top_left_sizer.Add(self.__module_controls_panel,0,wx.EXPAND|wx.ALL,2)
        self.__top_left_sizer.AddGrowableRow(1)
        self.__top_left_panel.SetSizer(self.__top_left_sizer)
        self.__sizer.AddMany([(self.__top_left_panel,0,wx.EXPAND),
                         (self.__module_panel,1,wx.EXPAND),
                         (self.__file_list_panel,0,wx.EXPAND),
                         (self.__preferences_panel,0,wx.EXPAND)])
        self.__sizer.set_ignore_height(0,1) # Ignore the best height for the file list panel
        self.__sizer.set_ignore_height(0,0) # Ignore the best height for the module list panel
        self.SetSizer(self.__sizer)
        self.Layout()
        self.__directory_view.set_height(self.__preferences_panel.GetBestSize()[1])

    def __layout_logo(self):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        bitmap = get_cp_bitmap(52)
        logopic = wx.StaticBitmap(self.__logo_panel,-1,bitmap)
        logotext = wx.StaticText(self.__logo_panel,-1,"CellProfiler\nimage analysis\npipeline",style=wx.ALIGN_CENTER)
        sizer.AddMany([(logopic,0,wx.ALIGN_LEFT|wx.ALIGN_TOP|wx.ALL,5),
                       (logotext,1,wx.EXPAND)])
        self.__logo_panel.SetSizer(sizer)
    
    def __set_icon(self):
        self.SetIcon(get_icon())
    
    def __on_size(self, event):
        self.Layout()
 
    def display_error(self,message,error):
        """Displays an exception in a standardized way
        
        """
        for listener in self.__error_listeners:
            listener(message, error)
        tb = sys.exc_info()[2]
        traceback.print_tb(tb)
        text = '\n'.join(traceback.format_list(traceback.extract_tb(tb)))
        text = error.message + '\n'+text
        wx.MessageBox(text,"Caught exception during operation")
    
    def add_error_listener(self,listener):
        """Add a listener for display errors"""
        self.__error_listeners.append(listener)
    
    def remove_error_listener(self,listener):
        """Remove a listener for display errors"""
        self.__error_listeners.remove(listener)
    
    def get_preferences_view(self):
        return self.__preferences_view
    
    preferences_view = property(get_preferences_view)
    
    def get_pipeline_controller(self):
        """Get the pipeline controller to drive testing"""
        return self.__pipeline_controller
    
    pipeline_controller = property(get_pipeline_controller)
    
    def get_pipeline(self):
        """Get the pipeline - mostly to drive testing"""
        return self.__pipeline
    
    pipeline = property(get_pipeline)
    
    def get_module_view(self):
        """Return the module view window"""
        return self.__module_view
    
    module_view = property(get_module_view)
    
    def get_pipeline_list_view(self):
        return self.__pipeline_list_view
    
    pipeline_list_view = property(get_pipeline_list_view)

class CPSizer(wx.PySizer):
    """A grid sizer that deals out leftover sizes to the hungry row and column
    
    """
    # If this were for use outside of here, it would look at the positioning flags such
    # as wx.EXPAND and wx.ALIGN... in RecalcSizes, but we assume everything wants
    # to be expanded
    def __init__(self,rows,cols,hungry_row,hungry_col):
        wx.PySizer.__init__(self)
        self.__rows = rows
        self.__cols = cols
        self.__hungry_row = hungry_row
        self.__hungry_col = hungry_col
        self.__ignore_width = [[False for j in range(0,rows)] for i in range(0,cols)]
        self.__ignore_height = [[False for j in range(0,rows)] for i in range(0,cols)]
    
    def set_ignore_width(self,col,row,ignore=True):
        """Don't pay any attention to the minimum width of the item in grid cell col,row
        
        """
        self.__ignore_width[col][row]=ignore
    
    def get_ignore_width(self,col,row):
        """Return true if we should ignore the minimum width of the item at col,row
        
        """
        return self.__ignore_width[col][row]
    
    def set_ignore_height(self,col,row,ignore=True):
        """Don't pay any attention to the minimum height of the item in grid cell col,row
        
        """
        self.__ignore_height[col][row]=ignore
    
    def get_ignore_height(self,col,row):
        """Return true if we should ignore the minimum height of the item at col,row
        
        """
        return self.__ignore_height[col][row]
    
    def CalcMin(self):
        """Calculate the minimum row and column and add
        """
        (row_heights, col_widths) = self.__get_min_sizes()
        return wx.Size(sum(col_widths),sum(row_heights))
    
    def __get_min_sizes(self):
        row_heights=[0 for i in range(0,self.__rows)]
        col_widths=[0 for i in range(0,self.__cols)]
        idx = 0
        for item in self.GetChildren():
            row,col = divmod(idx,self.__rows)
            size = item.CalcMin()
            if not self.get_ignore_width(col,row):
                col_widths[col]=max(col_widths[col],size[0])
            if not self.get_ignore_height(col,row):
                row_heights[row]=max(row_heights[row],size[1])
            idx+=1
        return (row_heights,col_widths)
    
    def RecalcSizes(self):
        """Recalculate the sizes of our items, distributing leftovers among them  
        """
        (row_heights, col_widths) = self.__get_min_sizes()
        size = self.GetSize()
        leftover_width = size[0]- sum(col_widths)
        leftover_height = size[1] - sum(row_heights)
        col_widths[self.__hungry_col]+=leftover_width
        row_heights[self.__hungry_row]+=leftover_height
        idx = 0
        for item in self.GetChildren():
            row,col = divmod(idx,self.__rows)
            item_size = wx.Size(col_widths[col],row_heights[row])
            item_pos = wx.Point(sum(col_widths[:col]),sum(row_heights[:row]))
            item.SetDimension(item_pos,item_size)
            idx+=1
    
        
