from PySide2 import QtWidgets
from PySide2 import QtGui
from PySide2 import QtCore
from shiboken2 import wrapInstance

from pxr import Sdf, UsdUtils, Usd
from MAYA_UTILS import maya_usd

import maya.cmds as cmds
import maya.OpenMayaUI as omui
import maya.api.OpenMaya as om
import maya.mel as mel

from functools import partial

import sys
import os
import time
import tempfile

from MayaWorkspaceControl import WorkspaceControl

import MAYA_TOOLS.LAY.usd_utils.export_usd.code.source.export_usd as export_usd
import MAYA_TOOLS.LAY.usd_utils.import_usd.code.source.import_usd as import_usd
import MAYA_TOOLS.LAY.usd_update.code.source.usd_update as usd_update


class fast_import_export(object):
    
    @classmethod
    def export_prims(cls):
        root_prims = maya_usd.getPrimsFromSelected()
        if not root_prims:
            om.MGlobal.displayError("Empty USD selection.")
            return
        stages = set(prim.GetStage() for prim in root_prims)
        if not stages or len(stages) > 1:
            print("Multiple stages.")
            return
        stage = stages.pop()
        target_layer = Sdf.Layer.CreateAnonymous()
        source_layer = UsdUtils.FlattenLayerStack(stage)
        source_layer.ClearCustomLayerData()
        
        def children(a,layer,path,*args):
            if a != 'primChildren':
                return True
            children = layer.GetPrimAtPath(path).nameChildren
            output_list = []
            for childName, childPrim in children.items():
                child_path = childPrim.path.pathString
                if any(child_path.startswith(prim.GetPath().pathString + '/')
                       or prim.GetPath().pathString.startswith(child_path + '/')
                       or prim.GetPath().pathString == child_path for prim in root_prims):
                    output_list.append(childName)
            return (True, output_list, output_list)

        def values(*args):
            return True

        new_stage = Usd.Stage.Open(source_layer)
        iterator = iter(new_stage.Traverse())
        for prim in iterator:
            if prim.HasAssetInfo() and prim.HasAuthoredReferences():
                refs = Usd.PrimCompositionQuery.GetDirectReferences(prim)
                asset_ref = refs.GetCompositionArcs()[0].GetIntroducingListEditor()[1]
                while asset_ref.IsInternal():
                    _prim = stage.GetPrimAtPath(asset_ref.primPath)
                    if not _prim:
                        continue
                    refs = Usd.PrimCompositionQuery.GetDirectReferences(_prim)
                    asset_ref = refs.GetCompositionArcs()[0].GetIntroducingListEditor()[1]
                if prim.HasVariantSets():
                    variant_sets = prim.GetVariantSets()
                    variant_sels = prim.GetVariantSets().GetAllVariantSelections()
                    for variant_set, variant in variant_sels.items():
                        variant_sets.SetSelection(variant_set, variant)
                prim.GetReferences().SetReferences([asset_ref])
                iterator.PruneChildren()

        res = Sdf.CopySpec(source_layer, Sdf.Path("/"), target_layer, Sdf.Path("/"), values, children)
        
        save_path = os.path.join(tempfile.gettempdir(), "Maya_usd.usda")

        try:
            res = target_layer.Export(save_path)
            if not res:
                raise Exception("No write permission.")
        except Exception as e:
            print(f"Export FAILED!\n{str(e)}")
        print("Export Successfully!")
        
    @classmethod
    def import_prims(cls):
        path = os.path.join(tempfile.gettempdir(), "Maya_usd.usda")
        layer = Sdf.Layer.FindOrOpen(path)
        if not layer:
            print("File cannot be opened!")
            return
        layer.Reload(True)
        stage = cls.getStage()
        if not stage:
            print("Stage error!")
            return
        mylayer = stage.GetEditTarget().GetLayer()
        UsdUtils.StitchLayers(mylayer, layer)
        print("import Successfully")
        
    @classmethod
    def getStage(cls):
        try:
            stage_name = cmds.listRelatives("|MASTER|COMPONENTS|USD", ad=True, type='mayaUsdProxyShape', f=True)[0]
            stage = maya_usd.getStage(stage_name)
            return stage
        except:
            return None
    
    @classmethod
    def del_usd(cls):
        path = os.path.join(tempfile.gettempdir(), "Maya_usd.usda")
        if os.path.exists(path):
            os.remove(path)
            print("DEL OK")
     
        
class CollapsibleHeader(QtWidgets.QWidget):
    
    COLLAPSED_PIXMAP = QtGui.QPixmap(":teRightArrow.png")
    EXPANDED_PIXMAP = QtGui.QPixmap(":teDownArrow.png")
    
    clicled = QtCore.Signal()
    
    def __init__(self, text, parent=None):
        super(CollapsibleHeader, self).__init__(parent)
        
        self.setAutoFillBackground(True)
        self.set_background_color(None)
        
        self.icon_label = QtWidgets.QLabel()
        self.icon_label.setFixedWidth(self.COLLAPSED_PIXMAP.width())
        
        self.text_lable = QtWidgets.QLabel()
        self.text_lable.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.setContentsMargins(2, 2, 2, 2)
        self.main_layout.addWidget(self.icon_label)
        self.main_layout.addWidget(self.text_lable)            
    
        self.set_text(text)
        self.set_expanded(False)
        
    def set_text(self, text):
        self.text_lable.setText("<b>{0}</b>".format(text))
    
    def set_background_color(self, color):
        if not color:
            color = QtWidgets.QPushButton().palette().color(QtGui.QPalette.Button)
            
        palette = self.palette()
        palette.setColor(QtGui.QPalette.Window, color)
        self.setPalette(palette)
    
    
    def is_expanded(self):
        return self._expanded
        
    def set_expanded(self, expanded):
        self._expanded = expanded
        
        if(self._expanded):
            self.icon_label.setPixmap(self.EXPANDED_PIXMAP)
        else:
            self.icon_label.setPixmap(self.COLLAPSED_PIXMAP)
    
    def mouseReleaseEvent(self, event):
        self.clicled.emit()
    
    
class CollapsibleWidget(QtWidgets.QWidget):
    
    
    clicled = QtCore.Signal()
    
    def __init__(self, text, parent=None):
        super(CollapsibleWidget, self).__init__(parent)
        
        self.append_stretch_on_collapse = False
        self.stretch_appended = False
        
        self.header_wdg = CollapsibleHeader(text)
        self.header_wdg.clicled.connect(self.on_header_clicked)
        
        self.body_wdg = QtWidgets.QWidget()
        self.body_wdg.setAutoFillBackground(True)
        
        palette = self.body_wdg.palette()
        palette.setColor(QtGui.QPalette.Window, palette.color(QtGui.QPalette.Window).lighter(110))
        self.body_wdg.setPalette(palette)
        
        self.body_layout = QtWidgets.QVBoxLayout(self.body_wdg)
        self.body_layout.setContentsMargins(2, 2, 2, 2)
        self.body_layout.setSpacing(2)
        
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(1)
        self.main_layout.addWidget(self.header_wdg)
        self.main_layout.addWidget(self.body_wdg)
        
        self.set_expanded(False)
        
    def set_header_background_color(self, color):
        self.header_wdg.set_background_color(color)
    
    def set_expanded(self, expanded):
        self.header_wdg.set_expanded(expanded)
        self.body_wdg.setVisible(expanded)
        
        if self.append_stretch_on_collapse:
            if expanded:
                if self.stretch_appended:
                    self.main_layout.takeAt(self.main_layout.count() - 1)
                    self.stretch_appended = False
            elif not self.stretch_appended:
                self.main_layout.addStretch()
                self.stretch_appended = True
                
    def add_widget(self, widget):
        self.body_layout.addWidget(widget)
    
    def add_layout(self, layout):
        self.body_layout.addLayout(layout)
     
    def on_header_clicked(self):
        self.set_expanded(not self.header_wdg.is_expanded())
        self.clicled.emit()

class ColorChangeButton(QtWidgets.QPushButton):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        
        self.enter_color = QtCore.Qt.green
        self.leave_color = QtWidgets.QPushButton().palette().color(QtGui.QPalette.Button)
        
        self.setAutoFillBackground(True)
        
        self.fount = QtGui.QFont()
        self.fount.setBold(True)
        #Maiandra GD
        self.fount.setFamily("Microsoft JhengHei")
        self.setFont(self.fount)
        
        self.enter = False
        
    def set_enter_color(self, color):
        self.enter_color = color

    def set_leace_color(self, color):
        self.leave_color = color

    def set_background_color(self, color):
        palette = self.palette() 
        palette.setColor(self.backgroundRole(), color) 
        if self.enter: 
            palette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.black)
        else:
            palette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
        self.setPalette(palette)  

    def enterEvent(self, e):
        self.enter = True
        self.set_background_color(self.enter_color)
        self.update()
        
    def leaveEvent(self, e):
        self.enter = False
        self.set_background_color(self.leave_color)
        self.update()
        
class ColorInfoChangewidget(QtWidgets.QWidget):
    
    color_change = QtCore.Signal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setFixedSize(15, 15)
        
        self.color = QtCore.Qt.green
        
        self.is_path = False
        self.get_usd_path()
        
    def set_background_color(self):
        if self.is_path:
            self.color = QtCore.Qt.green
        else:
            self.color = QtCore.Qt.red
            
    def paintEvent(self, paint_event):
        painter = QtGui.QPainter(self)
        painter.setBrush(self.color)
        painter.fillRect(0, 0, self.width(), self.height(), self.color)
        self.update()

    def get_usd_path(self):
        path = os.path.join(tempfile.gettempdir(), "Maya_usd.usda")
        if os.path.exists(path):
            self.is_path = True
            self.color = QtCore.Qt.green
        else:
            self.is_path = False
            self.color = QtCore.Qt.red
            
            
class ZurbriggFormLayout(QtWidgets.QGridLayout):

    def __init__(self, parent=None):
        super(ZurbriggFormLayout, self).__init__(parent)

        self.setContentsMargins(0, 0, 0, 8)
        self.setColumnMinimumWidth(0, 80)
        self.setHorizontalSpacing(6)

    def addWidgetRow(self, row, label, widget):
        self.addWidget(QtWidgets.QLabel(label), row, 0, QtCore.Qt.AlignRight)
        self.addWidget(widget, row, 1)

    def addLayoutRow(self, row, label, layout):
        self.addWidget(QtWidgets.QLabel(label), row, 0, QtCore.Qt.AlignRight)
        self.addLayout(layout, row, 1)

class line(QtWidgets.QFrame):
    
    def __init__(self, box, parent=None):
        super().__init__(parent)
        
        self.setFrameShape(box)
        
        self.setFrameShadow(QtWidgets.QFrame.Sunken)

    
class Import_ExportWidget(QtWidgets.QWidget):
        
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.create_widgets()
        self.create_layout()
        self.create_connections()
        
        
    def create_widgets(self):
        
        self.import_btn = ColorChangeButton("Import USD")
        self.import_btn.setFixedWidth(100)
        
        self.export_btn = ColorChangeButton("Export USD")
        self.export_btn.setFixedWidth(100)
        
        self.fast_import_btn = ColorChangeButton("Fast Import USD")
        self.fast_import_btn.enter_color = QtCore.Qt.blue
        self.fast_import_btn.setFixedWidth(100)
        
        self.fast_export_btn = ColorChangeButton("Fast Export USD")
        self.fast_export_btn.enter_color = QtCore.Qt.blue
        self.fast_export_btn.setFixedWidth(100)
        
        self.color_info = ColorInfoChangewidget()
        
        
        self.delete_usd = ColorChangeButton("DEL USD Cache")
        self.delete_usd.enter_color = QtCore.Qt.red
        self.delete_usd.setFixedWidth(100)
        
        self.collapsible_wdg_import = CollapsibleWidget("Fast Import/Export ")
        self.collapsible_wdg_import.setContentsMargins(2, 0, 0, 0)
        self.collapsible_wdg_import.set_expanded(True)

        
    def create_layout(self):
        body_wdg = QtWidgets.QWidget()
        
        body_layout = QtWidgets.QVBoxLayout(body_wdg)
        body_layout.setContentsMargins(0, 0, 0, 0) 
        body_layout.setSpacing(2)
        body_layout.setAlignment(QtCore.Qt.AlignTop)
        
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.import_btn)
        button_layout.addWidget(self.export_btn)
        button_layout.setAlignment(self.import_btn, QtCore.Qt.AlignRight)
        button_layout.setAlignment(self.export_btn, QtCore.Qt.AlignLeft)
        
        del_layout = QtWidgets.QHBoxLayout()
        del_layout.addWidget(self.color_info)
        del_layout.addWidget(self.delete_usd)
        del_layout.setAlignment(self.color_info, QtCore.Qt.AlignRight)

        fast_button_layout = QtWidgets.QHBoxLayout()
        fast_button_layout.addWidget(self.fast_import_btn)
        fast_button_layout.addWidget(self.fast_export_btn)
        fast_button_layout.setAlignment(self.fast_import_btn, QtCore.Qt.AlignRight)
        fast_button_layout.setAlignment(self.fast_export_btn, QtCore.Qt.AlignLeft)
        
    
        body_layout.addLayout(fast_button_layout)
        body_layout.setSpacing(5)
        body_layout.addWidget(line(QtWidgets.QFrame.HLine))
        body_layout.addLayout(del_layout)
        self.collapsible_wdg_import.add_widget(body_wdg)

        
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(5)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.collapsible_wdg_import)
        
        
    def create_connections(self):
        
        self.collapsible_wdg_import.clicled.connect(partial(self.color_info.get_usd_path))
        
        self.import_btn.clicked.connect(partial(import_usd.import_prims))
        self.export_btn.clicked.connect(partial(export_usd.export_prims))

        
        self.fast_import_btn.clicked.connect(partial(fast_import_export.import_prims))
        self.fast_export_btn.clicked.connect(partial(fast_import_export.export_prims))    
        self.fast_export_btn.clicked.connect(partial(self.color_info.get_usd_path))
        
        self.delete_usd.clicked.connect(partial(fast_import_export.del_usd))
        self.delete_usd.clicked.connect(partial(self.color_info.get_usd_path))
        
        
class MayaUsdToolsWidget(QtWidgets.QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.Fount = QtGui.QFont()
        self.Fount.setBold(True)
        self.Fount.setFamily("Comic Sans MS")
        self.Fount.setPointSize(11)
        
        self.create_widgets()
        self.create_layouts()
        self.create_connections()

        
    def create_widgets(self):
        self.collapsible_wdg_import = CollapsibleWidget("USD Import/Export ")
        self.collapsible_wdg_import.set_expanded(True)
        
        self.import_wdg = Import_ExportWidget()
        self.collapsible_wdg_import.add_widget(self.import_wdg)
        
        self.collapsible_wdg_TaskTool = CollapsibleWidget("USD Task")
        self.collapsible_wdg_TaskTool.set_expanded(False)
    
        self.collapsible_wdg_Duplicate = CollapsibleWidget("USD Duplicate As Maya")
        self.collapsible_wdg_Duplicate.set_expanded(False)
        
        self.collapsible_wdg_Scence = CollapsibleWidget("USD Scence Cleanup")
        self.collapsible_wdg_Scence.set_expanded(False)
        
        self.collapsible_wdg_Bake_Ani = CollapsibleWidget("Bake Animated Transform to USD Prim")
        self.collapsible_wdg_Bake_Ani.set_expanded(False)
        
        self.collapsible_wdg_Match = CollapsibleWidget("USD MatchTransformations")
        self.collapsible_wdg_Match.set_expanded(False)
        
        self.update_btn = QtWidgets.QPushButton("ALL USD Update!")
        self.update_btn.setFixedHeight(40)
        self.update_btn.setFont(self.Fount)
        
        pal = self.update_btn.palette()
        pal.setColor(QtGui.QPalette.Button, QtGui.QColor(QtCore.Qt.darkGreen).darker())
        self.update_btn.setPalette(pal)

        self.help_btn = QtWidgets.QPushButton("Help!")
        self.help_btn.setPalette(pal)
        self.help_btn.setMaximumWidth(50)
        self.help_btn.setFixedHeight(40)
        self.help_btn.setFont(self.Fount)
        
        pal = self.help_btn.palette()
        pal.setColor(QtGui.QPalette.Button, QtGui.QColor(QtCore.Qt.darkCyan).darker())
        self.help_btn.setPalette(pal)
        
    def create_layouts(self):
        
        self.body_wdg = QtWidgets.QWidget()
        
        self.body_layout = QtWidgets.QVBoxLayout(self.body_wdg)
        self.body_layout.setContentsMargins(0, 0, 0, 0) 
        self.body_layout.setSpacing(2)
        self.body_layout.setAlignment(QtCore.Qt.AlignTop)
        self.body_layout.addWidget(self.collapsible_wdg_import)
        self.body_layout.addWidget(self.collapsible_wdg_TaskTool)
        self.body_layout.addWidget(self.collapsible_wdg_Duplicate)
        self.body_layout.addWidget(self.collapsible_wdg_Scence)
        self.body_layout.addWidget(self.collapsible_wdg_Bake_Ani)
        self.body_layout.addWidget(self.collapsible_wdg_Match)
        
        self.update_layout = QtWidgets.QHBoxLayout()
        self.update_layout.setSpacing(2)
        self.update_layout.addWidget(self.update_btn)
        self.update_layout.addWidget(self.help_btn)

        
        self.body_scrool_area = QtWidgets.QScrollArea()
        self.body_scrool_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.body_scrool_area.setWidgetResizable(True)
        self.body_scrool_area.setWidget(self.body_wdg)
        
        
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(2, 5, 2, 1)
        main_layout.addWidget(self.body_scrool_area)
        main_layout.addLayout(self.update_layout)
        
    def create_connections(self):
        self.collapsible_wdg_import.clicled.connect(self.import_wdg.color_info.get_usd_path)
        
        
        self.update_btn.clicked.connect(usd_update.main)


class MayaLayUI(QtWidgets.QWidget):
    
    
    ui_instance = None
    
    WindowsTitle = "MAYA_Lay"
    
    UI_NAME = "Maya_LAY"
    
    @classmethod
    def display(cls):
        if cls.ui_instance:
            cls.ui_instance.show_workspace_control()
        else:
            cls.ui_instance = Maya_loader_UI()
            
    @classmethod
    def get_workspace_control_name(cls):
        return "{0}WorkspaceControl".format(cls.UI_NAME)
        
    def __init__(self, parent=None):
        super().__init__(parent)
        
        
        
        self.MayaUsdTool_wdg = MayaUsdToolsWidget()

        
        self.create_widgets()
        self.create_layout()
        self.create_connections()
        self.create_workspace_control()
        
        
    def create_widgets(self):
        pass
        #self.MayaUsdTool_tab = QtWidgets.QTabWidget()
        #self.MayaUsdTool_tab.addTab(self.MayaUsdTool_wdg , "USD_Tools")
        
    def create_layout(self):
    
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.MayaUsdTool_wdg)

    def create_connections(self):
        pass
        
        
    def showEvent(self, evevt):
        if self.workspace_control_instance.is_floating():
            self.workspace_control_instance.set_label("USD")
        else:
            self.workspace_control_instance.set_label("USD")   
        
    def create_workspace_control(self):
        self.workspace_control_instance = WorkspaceControl(self.get_workspace_control_name())
        if self.workspace_control_instance.exists():
            self.workspace_control_instance.restore(self)
        else:
            self.workspace_control_instance.create(self.WindowsTitle, self, ui_script="from Maya_Lay_UI import MayaLayUI\nMayaLayUI.display()")
        
    def show_workspace_control(self):
        self.workspace_control_instance.set_visible(True)     


if __name__ == "__main__":
    
    WorkspaceControl_control_name = MayaLayUI.get_workspace_control_name()
    
    if cmds.window(WorkspaceControl_control_name, exists=True):
        cmds.deleteUI(WorkspaceControl_control_name)

    LAY_Tool = MayaLayUI() 



