# GUI for RePixelator v1.0
# Works on python 3.4 or higher

try:
    import wx
    from wx.adv import AboutDialogInfo, GenericAboutBox
except:
    print('wxpython>=4.0.0 not installed. Type "pip install wxpython" to install')
    exit()

try:
    from .repixelator import rePixelateFile
    from .repixelator import __version__
except:
    wx.LogFatalError('repixelator.py file not found or corrupt. Please place the file within the same directory.')

from threading import Thread
from pathlib import Path
import os
import sys
import numpy as np

if os.name == 'nt':
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('RePixelator.'+__version__) # taskbar icon fix
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0) # close the cmd

os.chdir(os.path.dirname(os.path.abspath(__file__))) # set cwd to script directory, not the cmd.


class RedirectStdoutToTextCtrl():
    def __init__(self, widget):
        sys.stdout = self
        self.widget = widget
    
    def write(self, message):
        self.widget.WriteText(message)
        return len(message)
    
    def __del__(self):
        sys.stdout = sys.__stdout__


class GUI(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title)
        self.SetIcon(wx.Icon('icon.ico'))
        
        self.panel = wx.Panel(self)
        
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.panel.SetSizer(hSizer)
        self.outerSizer = hSizer
        
        vSizer = wx.BoxSizer(wx.VERTICAL)
        hSizer.Add(vSizer, flag=wx.EXPAND)
        
        mainPanel = wx.Panel(self.panel)
        vSizer.Add(mainPanel, proportion=1)
        self.mainUI(mainPanel)
        
        self.settingsPanel = wx.Panel(self.panel)
        vSizer.Add(self.settingsPanel, flag=wx.ALL|wx.EXPAND, border=5)
        self.settingsUI(self.settingsPanel)
        self.settingsPanelStat = False
        
        self.loggerPanel = wx.Panel(self.panel)
        hSizer.Add(self.loggerPanel, flag=wx.EXPAND, proportion=1)
        self.logsUI(self.loggerPanel)
        self.loggerPanelStat = False
        
        self.toggleFrames()
        self.Centre()
        self.panel.Layout()
        
    def mainUI(self, panel):
        sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(sizer)
        
        # TODO: Stop button
        self.dndButton = wx.Button(panel, label='Drop files here\nor click to select files', size=(222, 100))
        sizer.Add(self.dndButton, flag=wx.ALL, border=5, proportion=1)
        self.dndButton.Bind(wx.EVT_BUTTON, self.onOpenFiles)
        self.dndButton.SetDropTarget(self.FileDrop(self))
        
        self.gauge = wx.Gauge(panel, range=1000, style=wx.GA_HORIZONTAL, size=(0, 20))
        sizer.Add(self.gauge, flag=wx.LEFT|wx.RIGHT|wx.EXPAND, border=5)
        self.gauge.SetValue(0)
        
        bottomSizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(bottomSizer, flag=wx.EXPAND)
        
        settingsButton = wx.Button(panel, label='Settings', style=wx.BU_EXACTFIT)
        bottomSizer.Add(settingsButton, flag=wx.ALL, border=5)
        settingsButton.Bind(wx.EVT_BUTTON, lambda _: self.toggleFrames('s'))
        
        logsButton = wx.Button(panel, label='Logs', style=wx.BU_EXACTFIT)
        bottomSizer.Add(logsButton, flag=wx.UP|wx.DOWN, border=5)
        logsButton.Bind(wx.EVT_BUTTON, lambda _: self.toggleFrames('l'))
        
        self.statusLabel = wx.StaticText(panel, label='0%', style=wx.ALIGN_CENTRE_HORIZONTAL)
        bottomSizer.Add(self.statusLabel, flag=wx.ALIGN_CENTER, proportion=1)
        
        aboutButton = wx.Button(panel, label='About', style=wx.BU_EXACTFIT)
        bottomSizer.Add(aboutButton, flag=wx.ALL^wx.LEFT, border=5)
        aboutButton.Bind(wx.EVT_BUTTON, self.showAboutFrame)
        
    def settingsUI(self, panel):
        sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(sizer)
        
        #
        sizer.Add(wx.StaticLine(panel, wx.LI_HORIZONTAL), flag=wx.EXPAND)
        #
        
        # multiplier setting
        mulLabel = wx.StaticText(panel, label='Image pre zoom: x4')
        sizer.Add(mulLabel, flag=wx.ALL|wx.EXPAND, border=5)
        
        mulSlider = wx.Slider(panel, value=4, minValue=1, maxValue=4, style=wx.SL_AUTOTICKS)
        sizer.Add(mulSlider, flag=wx.EXPAND)
        mulSlider.Bind(wx.EVT_SCROLL, lambda _: mulLabel.SetLabel(mulLabel.GetLabel()[:-1]+str(mulSlider.GetValue())))
        
        #
        sizer.Add(wx.StaticLine(panel, wx.LI_HORIZONTAL), flag=wx.EXPAND)
        #
        
        # noise reduction
        nrLabel = wx.StaticText(panel, label='Noise Reduction: 0')
        sizer.Add(nrLabel, flag=wx.ALL|wx.EXPAND, border=5)
        
        nrSlider = wx.Slider(panel, value=0, minValue=0, maxValue=6, style=wx.SL_AUTOTICKS)
        sizer.Add(nrSlider, flag=wx.EXPAND)
        
        self.nrCheckBoxAlertStat = False
        def onNrSlider(evt):
            sliderValue = nrSlider.GetValue()
            nrLabel.SetLabel(nrLabel.GetLabel()[:-1] + str(sliderValue))
            if sliderValue > 0 and not self.nrCheckBoxAlertStat:
                self.nrCheckBoxAlertStat = True
                wx.MessageDialog(self, 'Noise reduction is not suitable for most images.\nPlease use it with problematic images only.', 'Warning', wx.OK|wx.ICON_WARNING).ShowModal()
        nrSlider.Bind(wx.EVT_SCROLL, onNrSlider)
        
        #
        sizer.Add(wx.StaticLine(panel, wx.LI_HORIZONTAL), flag=wx.EXPAND)
        #
        
        # offset pixel setting
        opSizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(opSizer, flag=wx.EXPAND|wx.ALL, border=5)
        
        opText = wx.StaticText(panel, label='Offset pixel threshold:')
        opSizer.Add(opText, flag=wx.ALIGN_CENTER_VERTICAL)
        
        opEntry = wx.TextCtrl(panel, value='0.8', size=(30, 25))
        opSizer.Add(opEntry, flag=wx.LEFT|wx.RIGHT, border=5)
        
        opUnit = wx.StaticText(panel, label='px')
        opSizer.Add(opUnit, flag=wx.ALIGN_CENTER_VERTICAL)
        
        #
        sizer.Add(wx.StaticLine(panel, wx.LI_HORIZONTAL), flag=wx.EXPAND)
        #
        
        fsLabel = wx.StaticText(panel, label='File save path')
        sizer.Add(fsLabel, flag=wx.ALL|wx.ALIGN_LEFT, border=5)
        
        fsRadioButton = wx.RadioButton(panel, label="Each file's directory")
        sizer.Add(fsRadioButton, flag=wx.LEFT|wx.BOTTOM, border=5)
        fsRadioButton.SetValue(True)
        fsRadioButton2 = wx.RadioButton(panel, label='Current directory')
        sizer.Add(fsRadioButton2, flag=wx.LEFT|wx.BOTTOM, border=5)
        
        #
        sizer.Add(wx.StaticLine(panel, wx.LI_HORIZONTAL), flag=wx.EXPAND)
        #
        
        outLabel = wx.StaticText(panel, label='Output file name')
        sizer.Add(outLabel, flag=wx.TOP|wx.LEFT|wx.ALIGN_LEFT, border=5)
        
        outEntry = wx.TextCtrl(panel, value='%s_converted.png', size=(100, 25))
        sizer.Add(outEntry, flag=wx.ALL|wx.EXPAND, border=5)
        
        self.settings = [mulSlider, nrSlider, opEntry, fsRadioButton, outEntry]
    
    def logsUI(self, panel):
        sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(sizer)
        
        self.logsTextCtrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE|wx.TE_READONLY, size=(222, 0))
        sizer.Add(self.logsTextCtrl, flag=wx.ALL|wx.EXPAND, border=5, proportion=1)
        self.logsTextCtrl.WriteText('Right click to clear the logs.\n\n')
        RedirectStdoutToTextCtrl(self.logsTextCtrl)
        
        def onContextMenu(evt):
            menu = wx.Menu()
            
            clearLog = menu.Append(wx.ID_ANY, "Clear log")
            menu.Bind(wx.EVT_MENU, lambda _: self.logsTextCtrl.Clear(), id=clearLog.GetId())
            
            self.logsTextCtrl.PopupMenu(menu)
        self.logsTextCtrl.Bind(wx.EVT_CONTEXT_MENU, onContextMenu)
        
    def toggleFrames(self, panelName=''):
        if panelName:
            x, y = self.GetSize()
            if x > self.minX:
                self.loggerPanelStat = True
            else:
                self.loggerPanelStat = False
        
        if panelName == 's':
            self.settingsPanelStat = not self.settingsPanelStat
        elif panelName == 'l':
            self.loggerPanelStat = not self.loggerPanelStat
        
        self.settingsPanel.Show(self.settingsPanelStat)
        self.loggerPanel.Show(False)
        
        self.outerSizer.SetSizeHints(self)
        if not panelName:
            x, y = self.GetSize()
            self.minX = x
        
        if self.loggerPanelStat:
            x, y = self.GetSize()
            self.SetSize((x+222, y))
        self.loggerPanel.Show(True)
        self.logsTextCtrl.SetInsertionPoint(-1)
        
        self.panel.Layout()
    
    def onOpenFiles(self, evt):
        with wx.FileDialog(self, "Open image file", wildcard="OpenCV compatible image files|*.bmp;*.dib;*.jpeg;*.jpg;*.jpe;*.jp2;*.png;*.webp;*.pbm;*.pgm;*.ppm;*.pxm;*.pnm;*.pfm;*.sr;*.ras;*.tiff;*.tif;*.exr;*.hdr;*.pic|All files|*.*", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            
            files = fileDialog.GetPaths()
            self.startConvert(files)
    
    def showAboutFrame(self, evt):
        info = AboutDialogInfo()
        info.SetName('RePixelator')
        info.SetVersion(__version__)
        info.SetDescription('by yclee126 (YeongChan Lee)')
        info.SetWebSite('github.com/yclee126/RePixelator')
        GenericAboutBox(info)
    
    def startConvert(self, files):
        # get parameters
        mul_value = self.settings[0].GetValue()
        nr_value = self.settings[1].GetValue() / 2
        try:
            op_value = float(self.settings[2].GetValue())
        except:
            wx.MessageDialog(self, 'Invalid character in number field', 'Error', wx.OK|wx.ICON_ERROR).ShowModal()
            return

        out_sel = self.settings[3].GetValue()
        out_string = self.settings[4].GetValue()
        try:
            str(Path(out_string).stem) % ''
        except:
            wx.MessageDialog(self, 'Invalid output file name', 'Error', wx.OK|wx.ICON_ERROR).ShowModal()
            return
        
        # start thread
        Thread(target=self.workerThread, daemon=True, args=(files, mul_value, nr_value, op_value, out_sel, out_string)).start()
    
    def workerThread(self, files, mul_value, nr_value, op_value, out_sel, out_string):
        wx.CallAfter(self.dndButton.Enable, False)
        wx.CallAfter(self.settingsPanel.Enable, False)
        wx.CallAfter(self.gauge.SetValue, 0)
        wx.CallAfter(self.statusLabel.SetLabel, '0%')
        wx.CallAfter(self.panel.Layout)
        
        failed_files = []
        
        for i, file in enumerate(files):
            print(f'\nFile {i+1}/{len(files)}')
            file_path = Path(file).resolve()
            
            if out_sel:
                output_path = str(file_path.parent)
            else:
                output_path = str(Path().cwd())
            
            file_name = out_string % str(file_path.stem)
            output_file = os.path.join(output_path, file_name)
            
            # process file
            result = False
            try:
                result = rePixelateFile(file, output_file, mul_value, nr_value, op_value)
            except:
                print('Unknown error')
            
            if not result:
                failed_files.append(file)
            
            wx.CallAfter(self.gauge.SetValue, int((i+1)/len(files)*1000))
            wx.CallAfter(self.statusLabel.SetLabel, f'{int((i+1)/len(files)*100)}%')
            wx.CallAfter(self.panel.Layout)
        
        if failed_files:
            failMsg = f'\n{len(failed_files)} file(s) failed to process:'
            print(failMsg)
            for failed_file in failed_files:
                print(failed_file)
            wx.MessageDialog(self, 'An error has occurred. Please check the log.', 'Error', wx.OK|wx.ICON_ERROR).ShowModal()
        else:
            print('\nAll files converted.')
        
        wx.CallAfter(self.dndButton.Enable, True)
        wx.CallAfter(self.settingsPanel.Enable, True)
        wx.CallAfter(self.gauge.SetValue, 1000)
        
    def getIcon(self):
        pass
    
    class FileDrop(wx.FileDropTarget):
        def __init__(self, parent):
            wx.FileDropTarget.__init__(self)
            self.parent = parent
     
        def OnDropFiles(self, x, y, filenames):
            self.parent.startConvert(filenames)
            return True

def main():
    app = wx.App()
    gui = GUI(None, wx.ID_ANY, 'RePixelator')
    gui.Show(True)
    app.MainLoop()

if __name__ == '__main__':
    main()