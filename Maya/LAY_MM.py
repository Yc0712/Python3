import sys
import math
import tempfile
import traceback
import random
import os

from functools import wraps

from PySide2 import QtWidgets
from PySide2 import QtCore
from PySide2 import QtGui
from shiboken2 import wrapInstance
from functools import partial

import maya.cmds as cmds
import maya.OpenMaya as om 
import maya.OpenMayaUI as omui

TEMPDIR = tempfile.gettempdir()

def maya_main_window():
    main_window_ptr =  omui.MQtUtil.mainWindow()
    
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)
    
def openCloseChunk(func):
    @wraps(func)
    def wrapper(*args, **kargs):
        action = None
        try:
            cmds.undoInfo(openChunk=True)
            action = func(*args, **kargs)
        except:
            print(traceback.format_exc())
            pass
        finally:
            cmds.undoInfo(closeChunk=True)
            return action
    return wrapper    
    
class Create_camera_plane(object):
    
    RESOLUTION_WIDTH = cmds.getAttr('defaultResolution.width')
    RESOLUTION_HEIGHT = cmds.getAttr('defaultResolution.height')
    _camera = None
    def creat_image(self, width=RESOLUTION_WIDTH, height=RESOLUTION_HEIGHT):
        Plane = cmds.polyPlane(width=width/100, height=height/100, sx=10, ax=[0, 1, 0], cuv=2, ch=1)[0]
        cmds.rotate(90, rotateX=True, objectSpace=True)
        cmds.rotate(180, rotateY=True, objectSpace=True)
        cmds.makeIdentity(apply=True, t=True, r=True, s=True)
        
        return Plane
        
    def getobjectType(self, sel):
        selshape = cmds.listRelatives(sel, fullPath=True, shapes=True)
        if selshape:
            objectType = cmds.objectType(selshape)
            return objectType
        
    def check_selection_camera(self):
        sel = cmds.ls(selection=True, long=True)
        
        if len(sel) != 1:
            om.MGlobal.displayError("You must select a single camera.")
            return
        
        if self.getobjectType(sel) != "camera":
            om.MGlobal.displayError("You must select a single camera.")
            return
        
        return sel[0]
        
    def create_plane(self):
        self._camera = self.check_selection_camera()
        if self._camera:
            camera_fl = cmds.getAttr(f"{self._camera}.fl")
            camera_HFA = cmds.getAttr(f"{self._camera}.horizontalFilmAperture") * 25.4
            camera_VFA = cmds.getAttr(f"{self._camera}.verticalFilmAperture") * 25.4
            aov = cmds.camera(self._camera, q=True, horizontalFieldOfView=True)
            _Plane = self.creat_image(self.RESOLUTION_WIDTH, self.RESOLUTION_HEIGHT)
            camera_group = cmds.group(name=self._camera + "_" + "plane")
            _Plane = cmds.ls(_Plane, long=True)[0]
            cmds.transformLimits(_Plane, tz=[0,1], etz=[1,0])
                    
            cmds.parentConstraint(self._camera, camera_group)
            cmds.setAttr("{0}.sz".format(camera_group), -1)
            cmds.setAttr("{0}.tz".format(_Plane), 1000)
            cmds.addAttr(_Plane, longName='U', attributeType='double', defaultValue=0, keyable=True)
            cmds.addAttr(_Plane, longName='V', attributeType='double', defaultValue=0, keyable=True)
            cmds.addAttr(_Plane, longName='OffsetU', attributeType='double', defaultValue=0, keyable=True) # Simillar to "Animation Layer".
            cmds.addAttr(_Plane, longName='OffsetV', attributeType='double', defaultValue=0, keyable=True)        
    
            plane_sx = '{0}.sx = {0}.tz * tan({1} / 180 * {2} / 2) * 2 / {3} * 100;'.format(_Plane, aov, repr(math.pi), self.RESOLUTION_WIDTH)
            plane_sy = '{0}.sy = {0}.tz * tan({1} / 180 * {2} / 2) * 2 / {3} * 100;'.format(_Plane, aov, repr(math.pi), self.RESOLUTION_WIDTH)
            plane_sz = '{0}.sz = {0}.tz * tan({1} / 180 * {2} / 2) * 2 / {3} * 100;'.format(_Plane, aov, repr(math.pi), self.RESOLUTION_WIDTH)
            cmds.expression(s=plane_sx, object=_Plane, alwaysEvaluate=True, unitConversion='all')
            cmds.expression(s=plane_sy, object=_Plane, alwaysEvaluate=True, unitConversion='all')
            cmds.expression(s=plane_sz, object=_Plane, alwaysEvaluate=True, unitConversion='all')
            
    def locator_z(self):
        plane_selecet = cmds.ls(sl=True)
        
        if plane_selecet and len(plane_selecet) == 2 and self.getobjectType(plane_selecet[1]) == "camera" :
            
            loc = cmds.spaceLocator(name=f"{plane_selecet[0]}_loc")[0]
        
            cmds.matchTransform(loc, plane_selecet[0])
            
            loc_z = '{0}.tz =  sqrt(pow(({1}.tx - {2}.tx), 2) + pow(({1}.ty - {2}.ty), 2)+ pow(({1}.tz - {2}.tz), 2))'.format(plane_selecet[0], loc, plane_selecet[1])
            
            cmds.expression(s=loc_z, object=plane_selecet[0], alwaysEvaluate=True, unitConversion='all')
            
class Create_25D(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(Create_25D, self).__init__(parent)
        
        self.colorIndexList = [13,14,6,17,1,16,2,9,18,20,19,30]
        """
        13 # Red
        14 # Green
        6 # Blue
        17 # Yellow
        1 # Black
        16 # White
        2 # Gray
        9 # Purple
        18 # Cyan
        20 # Light Red
        19 # Light Green
        30 # Light Blue
        """
        
        self.int_validator = QtGui.QIntValidator()
        self.alphabet_whitespace_validator = QtGui.QRegExpValidator(QtCore.QRegExp("[a-z-A-Z\s_]+"))

        self.create_widgets()
        self.create_layouts()
        self.create_connections()

    def create_widgets(self):
        #### Options ####
        self.frame_offset_le = QtWidgets.QLineEdit()
        self.frame_offset_le.setValidator(self.int_validator) # Frame Offset Line Edit will only allow "Integer".
        self.frame_offset_le.setText("0")
        self.flip_u_cb = QtWidgets.QCheckBox("U")
        self.flip_v_cb = QtWidgets.QCheckBox("V")
        self.random_color_cb = QtWidgets.QCheckBox()
        self.projection_ray_cb = QtWidgets.QCheckBox()
        #self.projection_ray_cb.toggle() # Default is "ON".

        #### Rename ####
        self.prefix_lb = QtWidgets.QLabel("Prefix")
        self.prefix_le = QtWidgets.QLineEdit()
        self.prefix_le.setValidator(self.alphabet_whitespace_validator) # Prefix Line Edit will only allow "Alphabet" and "Whitespace".
        self.suffix_lb = QtWidgets.QLabel("Suffix")
        self.suffix_le = QtWidgets.QLineEdit()
        self.suffix_le.setValidator(self.alphabet_whitespace_validator) # Suffix Line Edit will only allow "Alphabet" and "Whitespace".

        #### Quick Import ####
        self.quick_import_btn = QtWidgets.QPushButton("Quick")
        self.quick_import_btn.setStyleSheet("QPushButton {background-color: #EC5f67;}")

        #### Manual Import ####
        self.manual_import_btn = QtWidgets.QPushButton("Manual")

        #### Create Null ####
        self.create_null_btn = QtWidgets.QPushButton("Null")

    def create_layouts(self):
        #### Options ####
        options_flip_Layout = QtWidgets.QHBoxLayout()
        #options_flip_Layout.addWidget(self.flip_u_cb)
        #options_flip_Layout.addWidget(self.flip_v_cb).

        options_GroupBox = QtWidgets.QGroupBox("Options")
        options_Layout = QtWidgets.QFormLayout()
        options_Layout.addRow("Frame Offset", self.frame_offset_le)
        #options_Layout.addRow("Flip", options_flip_Layout)
        options_Layout.addRow("Random Color", self.random_color_cb)
        options_Layout.addRow("Projection Ray", self.projection_ray_cb)
        options_GroupBox.setLayout(options_Layout)
        options_GroupBox.setContentsMargins(2,2,2,2)

        #### Rename ####
        # rename_GroupBox = QtWidgets.QGroupBox("Rename")
        # rename_Layout = QtWidgets.QGridLayout()
        # rename_Layout.addWidget(self.prefix_lb, 0, 0)
        # rename_Layout.addWidget(self.prefix_le, 0, 1)
        # rename_Layout.addWidget(self.suffix_lb, 1, 0)
        # rename_Layout.addWidget(self.suffix_le, 1, 1)
        # rename_GroupBox.setLayout(rename_Layout)

        #### Quick Import ####
        quick_import_GroupBox = QtWidgets.QGroupBox("")
        quick_import_Layout = QtWidgets.QHBoxLayout()
        quick_import_Layout.setContentsMargins(2, 2, 2, 2)
        quick_import_Layout.setSpacing(5)
        quick_import_Layout.addWidget(self.manual_import_btn)
        quick_import_Layout.addWidget(self.quick_import_btn)
        quick_import_Layout.addWidget(self.create_null_btn)
        quick_import_GroupBox.setLayout(quick_import_Layout)

        main_Layout = QtWidgets.QVBoxLayout(self)
        main_Layout.addWidget(options_GroupBox)
        main_Layout.setSpacing(2)
        main_Layout.setContentsMargins(0, 0, 0, 0)
        main_Layout.addWidget(quick_import_GroupBox)
        


    def create_connections(self):
        self.quick_import_btn.clicked.connect(lambda: self.create_zloc("quick"))
        self.manual_import_btn.clicked.connect(lambda: self.create_zloc("manual"))
        self.create_null_btn.clicked.connect(lambda: self.create_zloc("null"))

    @openCloseChunk
    def create_zloc(self, mode):
        if self.one_camera_selected() == False: # Select "One" "Camera" type object.
            om.MGlobal.displayError("Please select a camera.")
            return

        selCamTrans = cmds.ls(selection=True, long=True)[0]
        selCamShape = cmds.listRelatives(selCamTrans, shapes=True, fullPath=True)[0]
        selCamHFA = cmds.camera(selCamShape, q=True, hfa=True)
        selCamVFA = cmds.camera(selCamShape, q=True, vfa=True)
        selCamUUID = cmds.ls(selCamTrans, uuid=True)[0]
        selCamUUID_underscore = selCamUUID.replace("-", "_")
        selCamZLocGrp = "zloc_grp_{0}".format(selCamUUID_underscore)
        selCamZLocProjectionRayGrp = "zloc_projection_ray_grp_{0}".format(selCamUUID_underscore)

        ## Options ##
        frame_offset = int(self.frame_offset_le.text())
        #flip_u = self.flip_checked("flip_u_cb") # If checked returns -1, else 1.
        #flip_v = self.flip_checked("flip_v_cb") # If checked returns -1, else 1.
        random_color = self.random_color_cb.isChecked()
        projection_ray = self.projection_ray_cb.isChecked()

        ## Rename ##
        prefix = self.get_prefix()
        suffix = self.get_suffix()

        if mode == "quick":
            path = os.path.join(TEMPDIR, "quick.zloc")
            # print(path)
            # c:\users\<USER>\appdata\local\temp\zloc_quick.txt
        elif mode == "manual":
            try:
                path = cmds.fileDialog2(fileFilter='*.zloc', dialogStyle=2, fileMode=1)[0]
            except:
                return None
        elif mode == "null":
            path = "null"

        if path == "":
            om.MGlobal.displayError("Something is wrong with the path.")
            return

        if mode == "null":
            word_list = ["null_zloc#", "1", "0.000000000000000", "0.000000000000000", "3"]
            # <name> + # to avoid name collision.
        else:
            with open(path,'r') as f:
                """
                print(f):
                zloc01 1 0.100000000000000 0.100000000000000 0
                zloc01 2 0.200000000000000 0.200000000000000 0
                zloc01 3 0.300000000000000 0.300000000000000 0
                zloc02 1 -0.100000000000000 -0.100000000000000 1
                zloc02 2 -0.200000000000000 -0.200000000000000 1
                zloc02 3 -0.300000000000000 -0.300000000000000 1
                """
                # About ZLOC Format
                # <name> <frame> <U> <V> <3DE4_color_index>

                word_list = [word for line in f for word in line.split()]
                """
                print(word_list):
                ["zloc01", "1", "0.100000000000000", "0.100000000000000", "0",
                 "zloc01", "2", "0.200000000000000", "0.200000000000000", "0",
                 "zloc01", "3", "0.300000000000000", "0.300000000000000", "0",
                 "zloc02", "1", "-0.100000000000000", "-0.100000000000000", "1",
                 "zloc02", "2", "-0.200000000000000", "-0.200000000000000", "1",
                 "zloc02", "3", "-0.300000000000000", "-0.300000000000000", "1"]
                """
        zloc_list = sorted(set(zip(word_list[0::5], word_list[4::5])))
        # Zip is for pairing every "0"th(Name) and "4"th(3DE4 Color Index) item.
        # Set is for removing dulplicates.
        # Sorted is for reordering items in alphabetical and numerical order.
        """
        print(zloc_list):
        [("zloc01","0"), ("zloc02","1")]
        """
        group_word_by_five_list = [word_list[i:i+5] for i in range(0, len(word_list), 5)]
        # "group_word_by_five_list" Result:
        """
        [["zloc01", "1", "0.100000000000000", "0.100000000000000", "0"],
         ["zloc01", "2", "0.200000000000000", "0.200000000000000", "0"],
         ["zloc01", "3", "0.300000000000000", "0.300000000000000", "0"],
         ["zloc02", "1", "-0.100000000000000", "-0.100000000000000", "1"],
         ["zloc02", "2", "-0.200000000000000", "-0.200000000000000", "1"],
         ["zloc02", "3", "-0.300000000000000", "-0.300000000000000", "1"]]
        """

        # Check for name collision
        for zloc, _ in zloc_list:
            if cmds.objExists(prefix + zloc + suffix):
                om.MGlobal.displayError("Name collision detected. Please rename by using prefix and suffix.")
                return

        # Create ZLOC Group
        if cmds.objExists(selCamZLocGrp): # ZLOC Group Exists
            pass
        else:
            cmds.group(name=selCamZLocGrp, empty=True) # Create ZLOC Group
            cmds.parentConstraint(selCamTrans, selCamZLocGrp, maintainOffset=False)
            cmds.scaleConstraint(selCamTrans, selCamZLocGrp, maintainOffset=True)

        # Create ZLOC Projection Ray Group
        if projection_ray: # If Projection Ray checkbox is checked
            if cmds.objExists(selCamZLocProjectionRayGrp): # ZLOC Projection Ray Group Exists
                pass
            else:
                cmds.group(name=selCamZLocProjectionRayGrp, empty=True) # Create ZLOC Projection Ray Group
                cmds.hide(selCamZLocProjectionRayGrp) # Hide ZLOC Projection Ray Group.
                cmds.parentConstraint(selCamTrans, selCamZLocProjectionRayGrp, maintainOffset=False)
                cmds.scaleConstraint(selCamTrans, selCamZLocProjectionRayGrp, maintainOffset=True)

        for zloc, tde4_color_index in zloc_list:
            # Create ZLOC
            zlocTrans = cmds.spaceLocator(name=prefix + zloc + suffix)[0]
            zlocShape = cmds.listRelatives(zlocTrans, shapes=True, fullPath=True)[0]

            # Set ZLOC Color
            if random_color: # If Random Color checkbox is checked
                zloc_color = random.choice(self.colorIndexList) # Pick a random index from "colorIndexList"
            else:
                zloc_color = self.get_color_from_index(tde4_color_index)
            cmds.setAttr(zlocShape + '.overrideEnabled', 1) # Enable Color Override
            cmds.setAttr(zlocShape + '.overrideColor', zloc_color) # Set Color

            # Add & Set Attributes
            cmds.addAttr(zlocTrans, longName='U', attributeType='double', defaultValue=0)
            cmds.addAttr(zlocTrans, longName='V', attributeType='double', defaultValue=0)
            cmds.addAttr(zlocTrans, longName='OffsetU', attributeType='double', defaultValue=0) # Simillar to "Animation Layer".
            cmds.addAttr(zlocTrans, longName='OffsetV', attributeType='double', defaultValue=0) # Simillar to "Animation Layer".
            cmds.setAttr(zlocTrans + '.U', keyable=True)
            cmds.setAttr(zlocTrans + '.V', keyable=True)
            cmds.setAttr(zlocTrans + '.OffsetU', keyable=True)
            cmds.setAttr(zlocTrans + '.OffsetV', keyable=True)
            cmds.setAttr(zlocTrans + '.sx', 0.1)
            cmds.setAttr(zlocTrans + '.sy', 0.1)
            cmds.setAttr(zlocTrans + '.sz', 0.001)
            cmds.setAttr(zlocTrans + '.tz', -10)

            # Expressions
            cmds.expression(s="{0}.tx = {1}.hfa * 2.54 * {0}.tz / ({1}.fl / 10) * -1 * ({0}.U + {0}.OffsetU);".format(zlocTrans, selCamTrans), object=zlocTrans, alwaysEvaluate=True, unitConversion='all')
            cmds.expression(s="{0}.ty = {1}.vfa * 2.54 * {0}.tz / ({1}.fl / 10) * -1 * ({0}.V + {0}.OffsetV);".format(zlocTrans, selCamTrans), object=zlocTrans, alwaysEvaluate=True, unitConversion='all')

            cmds.parent(zlocTrans, selCamZLocGrp, relative=True) # Parent ZLOC to ZLOC Group

            # Projection Ray
            if projection_ray: # If Projection Ray checkbox is checked.
                projectionRayTrans = cmds.curve(name= zlocTrans + "_projectionRay", degree=1, point=[(0,0,0),(0,0,-1000)]) # Create a Nurbs Curve. Length is 1000.
                projectionRayShape = cmds.listRelatives(projectionRayTrans, shapes=True, fullPath=True)[0] # Get Shape Node's name.

                # Set Projection Ray Color
                cmds.setAttr(projectionRayShape + '.overrideEnabled', 1) # Enable Color Override.
                cmds.setAttr(projectionRayShape + '.overrideColor', zloc_color) # Set Color. Same Color as ZLOC.

                cmds.aicmdsonstraint(zlocTrans, projectionRayTrans, aimVector=[0.0, 0.0, -1.0], maintainOffset=False) # Aim Projection Ray to ZLOC.

                cmds.parent(projectionRayTrans, selCamZLocProjectionRayGrp, relative=True)

        if mode != "null": # If mode is "null", skip this loop.
            # Set Keyframe for each ZLOC's "U" & "V" attributes.
            for i in range(len(group_word_by_five_list)):
                cmds.setKeyframe(prefix + group_word_by_five_list[i][0] + suffix, t=int(group_word_by_five_list[i][1]) + frame_offset, v=float(group_word_by_five_list[i][2])/selCamHFA, at='U')
                cmds.setKeyframe(prefix + group_word_by_five_list[i][0] + suffix, t=int(group_word_by_five_list[i][1]) + frame_offset, v=float(group_word_by_five_list[i][3])/selCamVFA, at='V')

        # Select Camera in the end
        cmds.select(selCamTrans, replace=True)


    def one_camera_selected(self):
        selList = cmds.ls(selection=True, long=True)
        if len(selList)==1 and cmds.objectType(cmds.listRelatives(selList, shapes=True, fullPath=True)[0]) == 'camera':
            return True
        else:
            return False

    def get_prefix(self):
        prefix = self.prefix_le.text().replace(" ", "_")
        if prefix == "":
            return ""
        else:
            return "{0}_".format(prefix)

    def get_suffix(self):
        suffix = self.suffix_le.text().replace(" ", "_")
        if suffix == "":
            return ""
        else:
            return "_{0}".format(suffix)


    def get_color_from_index(self, tde4_color_index):
        color_dict = {
        # 3DE4 Color Index : Maya Color Index
        "0": 13, # Red
        "1": 14, # Green
        "2": 6, # Blue
        "3": 17, # Yellow
        "4": 1, # Black
        "5": 16, # White
        "6": 2, # Gray
        "7": 9, # Purple
        "8": 18, # Cyan
        "9": 20, # Light Red
        "10": 19, # Light Green
        "11": 30 # Light Blue
        }
        maya_color_index = color_dict[tde4_color_index]
        return maya_color_index  
           
class Switch(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(Switch, self).__init__(parent)
        
        self.create_widgets()
        self.create_layouts()
        self.create_connections()

    def create_widgets(self):
        #### Static & Dynamic Object ####
        self.static_object_lb = QtWidgets.QLabel("²»¶¯")

        self.static_object_lb.setAlignment(QtCore.Qt.AlignLeft)
        self.static_object_input_lb = QtWidgets.QLabel()
        #self.static_object_input_lb.setMaximumWidth(80)
        self.static_object_input_lb.setAlignment(QtCore.Qt.AlignLeft)
        self.static_object_input_lb.setStyleSheet("QLabel {background-color: #222222;}")
        self.static_object_btn = QtWidgets.QPushButton("GET")
        self.static_object_btn.setFixedSize(30,20)
        self.static_object_btn.setStyleSheet("QPushButton {background-color: #EC5f67;}")


        self.dynamic_object_lb = QtWidgets.QLabel("¶¯")
        self.dynamic_object_lb.setFixedWidth(10)
        self.dynamic_object_lb.setAlignment(QtCore.Qt.AlignLeft)
        self.dynamic_object_input_lb = QtWidgets.QLabel()
        #self.dynamic_object_input_lb.setMaximumWidth(80)
        self.dynamic_object_input_lb.setStyleSheet("QLabel {background-color: #222222;}")
        self.dynamic_object_btn = QtWidgets.QPushButton("GET")
        self.dynamic_object_btn.setFixedSize(30,20)
        self.dynamic_object_btn.setStyleSheet("QPushButton {background-color: #EC5f67;}")

        #### Static & Dynamic Object ####

        #### Switch ####
        self.switch_btn = QtWidgets.QPushButton("Switch")
        self.switch_btn.setFixedSize(40,30)
        self.switch_btn.setStyleSheet("QPushButton {background-color: #EC5f67;}")
        #### Switch ####

    def create_layouts(self):
        #### Static & Dynamic Object ####
        static_dynamic_object_GroupBox = QtWidgets.QGroupBox()
        static_dynamic_object_Layout = QtWidgets.QGridLayout()
        static_dynamic_object_GroupBox.setAlignment(QtCore.Qt.AlignLeft)
        static_dynamic_object_Layout.addWidget(self.static_object_lb, 0, 0)
        static_dynamic_object_Layout.addWidget(self.static_object_input_lb, 0, 1)
        static_dynamic_object_Layout.addWidget(self.static_object_btn, 0, 2)
        static_dynamic_object_Layout.addWidget(self.dynamic_object_lb, 1, 0)
        static_dynamic_object_Layout.addWidget(self.dynamic_object_input_lb, 1, 1)
        static_dynamic_object_Layout.addWidget(self.dynamic_object_btn, 1, 2)
        static_dynamic_object_GroupBox.setLayout(static_dynamic_object_Layout)
        #### Static & Dynamic Object ####

        main_Layout = QtWidgets.QHBoxLayout(self)
        main_Layout.addWidget(static_dynamic_object_GroupBox)
        main_Layout.addWidget(self.switch_btn)

    def create_connections(self):
        self.static_object_btn.clicked.connect(lambda: self.get_object("static"))
        self.dynamic_object_btn.clicked.connect(lambda: self.get_object("dynamic"))
        self.switch_btn.clicked.connect(self.switch_motion)

    def get_object(self, mode):
        sel_trans = cmds.ls(selection=True, long=True)
        if len(sel_trans) == 1:
            if mode=="static":
                self.static_object_input_lb.setText(sel_trans[0])
            if mode=="dynamic":
                self.dynamic_object_input_lb.setText(sel_trans[0])
        else:
            om.MGlobal.displayError("Please select exactly 'one' object.")
            return None

    @openCloseChunk
    def switch_motion(self):
        if self.dynamic_object_input_lb.text() != "" or self.static_object_input_lb.text() != "":
            attr_list = ["tx","ty","tz","rx","ry","rz"]
            start_frame = cmds.playbackOptions(q=True, minTime=True)
            end_frame = cmds.playbackOptions(q=True, maxTime=True)

            dynamic_trans = self.dynamic_object_input_lb.text()
            static_trans = self.static_object_input_lb.text()

            dynamic_grp = cmds.group(name="dynamic_grp", empty=True)
            static_grp = cmds.group(name="static_grp", empty=True)
            cmds.parent(static_grp, dynamic_grp)

            dynamic_group_pc = cmds.parentConstraint(dynamic_trans, dynamic_grp, maintainOffset=False)[0]
            static_group_pc = cmds.parentConstraint(static_trans, static_grp, maintainOffset=False)[0]

            cmds.bakeResults(static_grp, attribute=attr_list, time=(start_frame, end_frame))

            cmds.delete(static_group_pc)

            # Mute Dynamic Object & Dynamic Group
            for attr in attr_list:
                cmds.mute("{0}.{1}".format(dynamic_trans, attr))
                cmds.mute("{0}.{1}".format(dynamic_grp, attr))

            static_trans_pc = cmds.parentConstraint(static_grp, static_trans, maintainOffset=False)[0] # Parent Constraint Static Object to Static Group
            cmds.bakeResults(static_trans, attribute=attr_list, time=(start_frame, end_frame))
            cmds.delete(static_trans_pc, dynamic_grp)
        else:
            om.MGlobal.displayError("Staic Object or Dynamic Object is empty.")
            return None
            
            
class  create_horizonLine(object):          
            
    def getActive3dViewCam(self):
        active3dView = omui.M3dView.active3dView()
        active3dViewCamDagPath = om.MDagPath()
        active3dView.getCamera(active3dViewCamDagPath)
        active3dViewCamShape = active3dViewCamDagPath.fullPathName()
        active3dViewCamTrans = cmds.listRelatives(active3dViewCamShape, parent=True, fullPath=True)[0]

        return active3dViewCamShape, active3dViewCamTrans

    def main(self):
        if cmds.objExists("*horizonLine*"):
            cmds.delete("*horizonLine*") # Delete existing "horizonLine"
            return

        active3dViewCamShape, active3dViewCamTrans = self.getActive3dViewCam()

        horizonLineTrans = cmds.circle(name='horizonLine', radius=2, normal=(0,1,0), sections=32)[0]
        horizonLineShape = cmds.listRelatives(horizonLineTrans, shapes=True, fullPath=True)[0]

        cmds.expression(s="""
                        {0}.sx = {1}.nearClipPlane;
                        {0}.sy = {1}.nearClipPlane;
                        {0}.sz = {1}.nearClipPlane;
                        """.format(horizonLineTrans, active3dViewCamShape), object=horizonLineTrans)

        cmds.setAttr(horizonLineShape + '.overrideEnabled', 1)
        cmds.setAttr(horizonLineShape + '.overrideColor', 14)

        cmds.pointConstraint(active3dViewCamTrans, horizonLineTrans, maintainOffset=False)

        cmds.select(clear=True)  
          
class camera_tool(object):
    
    def getActive3dViewCam(self):
        active3dView = omui.M3dView.active3dView()
        active3dViewCamDagPath = om.MDagPath()
        active3dView.getCamera(active3dViewCamDagPath)
        active3dViewCamShape = active3dViewCamDagPath.fullPathName()
        active3dViewCamTrans = cmds.listRelatives(active3dViewCamShape, parent=True, fullPath=True)[0]

        return active3dViewCamShape, active3dViewCamTrans


    def getObjectType(self, sel):
        try:
            selShape = cmds.listRelatives(sel, fullPath=True, shapes=True)  # Get selected object's shape node.
            objectType = cmds.objectType(selShape)  # Get object type.
        except:
            objectType = "transform"  # If there is no shape node pass "transform".
        return objectType


    def center3d(self):
        """
        Centers the viewport to TLOC.
        This may not work properly if the Image Plane's Aspect Ratio and Device Aspect Ratio(in Render Setting) does not match.
        Image Plane Size: 1920 X 1080 (1.778)  and  Image Size: 1920 X 1080 (1.778) --> O
        Image Plane Size: 1920 X 1080 (1.778)  and  Image Size: 960 X 540 (1.778) --> O
        Image Plane Size: 1920 X 1080 (1.778) and  Image Size: 3000 X 1500 (1.5) --> X
        """
        # Get selected transform list
        selTransformList = cmds.ls(selection=True, long=True)
        if len(selTransformList) == 0:
            cmds.warning("Select one or more Transform Nodes")
            return

        # Check if imagePlane is in selection list
        for selTransform in selTransformList:
            objectType = self.getObjectType(selTransform)
            if objectType == "imagePlane":
                cmds.warning("Can't Center3D an image plane")
                return

        # Get Active 3D View Camera
        active3dViewCamShape, active3dViewCamTrans = self.getActive3dViewCam()

        active3dViewCamTrans = cmds.listRelatives(active3dViewCamShape, parent=True, fullPath=True)[0]
        try:
            active3dViewCamImgPlaneShape = cmds.listRelatives(active3dViewCamShape, allDescendents=True, type='imagePlane')[0]
        except:
            active3dViewCamImgPlaneShape = None

        # Set Imageplane to show in "All Views"
        if active3dViewCamImgPlaneShape is not None:
            cmds.imagePlane(active3dViewCamImgPlaneShape, e=True, showInAllViews=True)

        # Create Center3D Locator
        center3dLoc = cmds.spaceLocator(name='center3d_#')[0]
        cmds.setAttr(center3dLoc + '.v', 0)

        for selTransform in selTransformList:
            cmds.pointConstraint(selTransform, center3dLoc, maintainOffset=False)

        # Create Center3D Camera
        center3dCam = cmds.camera(name=active3dViewCamTrans + center3dLoc)[0]
        center3DcamTrans = cmds.ls(cmds.parent(center3dCam, active3dViewCamTrans, relative=True), long=True)[0]
        center3DcamShape = cmds.listRelatives(center3DcamTrans, shapes=True, fullPath=True)[0]

        # LookThru Center3D Camera
        panelWithFocus = cmds.getPanel(withFocus=True)
        cmds.lookThru(panelWithFocus, center3DcamShape)

        # Sync Shape Attributes. Active 3D View Cam & Center 3D Cam
        cmds.connectAttr(active3dViewCamShape + '.hfa', center3DcamShape + '.hfa')
        cmds.connectAttr(active3dViewCamShape + '.vfa', center3DcamShape + '.vfa')
        cmds.connectAttr(active3dViewCamShape + '.fl', center3DcamShape + '.fl')
        cmds.connectAttr(active3dViewCamShape + '.nearClipPlane', center3DcamShape + '.nearClipPlane')
        cmds.connectAttr(active3dViewCamShape + '.farClipPlane', center3DcamShape + '.farClipPlane')

        # Center3D Expression
        exp = 'global proc float[] cTtransformPoint(float $mtx[], float $pt[]) // multiply 4x4 matrix with 4x vector\n'
        exp += '{\n'
        exp += '    float $res[] = {};\n'
        exp += '    if(`size $pt` == 3)\n'
        exp += '    $pt[3] = 1.0;\n'
        exp += '    for($i=0;$i<4;$i++){\n'
        exp += '    float $tmp = 0;\n'
        exp += '    for($k=0;$k<4;$k++){\n'
        exp += '        $tmp += $pt[$k] * $mtx[$k * 4 + $i];\n'
        exp += '    };\n'
        exp += '    $res[$i] = $tmp;\n'
        exp += '    };\n'
        exp += '    return $res;\n'
        exp += '};\n'

        exp += 'global proc float[] cGetProjectionMatrix(string $shape) //get camera projection matrix\n'
        exp += '{\n'
        exp += '    float $res[] = {};\n'
        exp += '    if(`objExists $shape` && `nodeType $shape` == "camera"){\n'
        exp += '    python "import maya.OpenMaya as om";\n'
        exp += '    python "list = om.MSelectionList()";\n'
        exp += '    python (' + '"' + 'list.add(' + "'" + '"' + '+ $shape + ' + '"' + "')" + '");\n'
        exp += '    python "depNode = om.MObject()";\n'
        exp += '    python "list.getDependNode(0, depNode)";\n'
        exp += '    python "camFn = om.MFnCamera(depNode)";\n'
        exp += '    python "pMtx = om.MFloatMatrix()";\n'
        exp += '    python "pMtx = camFn.projectionMatrix()";\n'
        exp += '    for($i=0;$i<=3;$i++){\n'
        exp += '        for($k=0;$k<=3;$k++)\n'
        exp += '        $res[`size $res`] = `python ("pMtx(" + $i + ", " + $k + ")")`;\n'
        exp += '    };\n'
        exp += '    };\n'
        exp += '    return $res;\n'
        exp += '};\n'

        exp += 'global proc float[] cWorldSpaceToImageSpace(string $camera, float $worldPt[])\n'
        exp += '{\n'
        exp += '    string $camShape[] = `ls -dag -type "camera" $camera`;\n'
        exp += '    if(! `size $camShape`)\n'
        exp += '    return {};\n'
        exp += '    string $cam[] = `listRelatives -p -f $camShape`;\n'
        exp += '    float $cam_inverseMatrix[] = `getAttr ($cam[0] + ".worldInverseMatrix")`;\n'
        exp += '    float $cam_projectionMatrix[] = `cGetProjectionMatrix $camShape[0]`;\n'
        exp += '    float $ptInCamSpace[] = `cTtransformPoint $cam_inverseMatrix $worldPt`;\n'
        exp += '    float $projectedPoint[] = `cTtransformPoint $cam_projectionMatrix $ptInCamSpace`;\n'
        exp += '    float $resultX = (($projectedPoint[0] / $projectedPoint[3]));\n'
        exp += '    float $resultY = (($projectedPoint[1] / $projectedPoint[3]));\n'
        exp += '    return {$resultX, $resultY};\n'
        exp += '};\n'

        exp += 'float $xy[] = cWorldSpaceToImageSpace("' + active3dViewCamTrans + '", {' + center3dLoc + '.translateX,' + center3dLoc + '.translateY,' + center3dLoc + '.translateZ});\n'
        exp += center3DcamShape + '.horizontalFilmOffset = ($xy[0] *' + active3dViewCamShape + '.hfa)/2 ;\n'
        exp += center3DcamShape + '.verticalFilmOffset = ($xy[1] *' + active3dViewCamShape + '.vfa)/2 ;\n'

        cmds.expression(s=exp, object=center3DcamShape)

        # Select Center3D Loc ##
        cmds.select(center3dLoc, replace=True)

    def main(self):
        if cmds.objExists("*center3d*") == True:
            cmds.delete("*center3d*")  # Delete all Center3D nodes
            return

        self.center3d()
        
class create_cone(object):
    
    def createCone(self, locName):
        cone = cmds.polyCone(name=locName + '_cone', r=1, h=2, sx=4, sy=1, sz=0, ax=[0, -1, 0], rcp=0, cuv=3, ch=True)[0]
        cmds.move(1, y=True)
        cmds.rotate(45, y=True)
        cmds.move(0, 0, 0, cone + ".scalePivot", cone + ".rotatePivot", absolute=True)
        cmds.makeIdentity(apply=True, translate=True, rotate=True)
        return cone


    def main(self, color=14):
        selList = cmds.ls(selection=True)

        if not selList:
            return

        if cmds.ls("Locator_cone_Grp"):
            cmds.delete("Locator_cone_Grp")
        if cmds.ls("Locator_Display"):
            cmds.delete("Locator_Display")

        locator_group = cmds.createNode("transform", name="Locator_cone_Grp")
        locator_display = cmds.createDisplayLayer(name="Locator_Display")
        cmds.setAttr("{0}.color".format(locator_display), color)
        for sel in selList:
            cone = self.createCone(sel)
            cmds.select(cone, sel, replace=True)
            cmds.MatchTranslation()
            cmds.parent(cone, locator_group)
            cmds.editDisplayLayerMembers(locator_display, cone)
            cmds.select(clear=True)

        try:
            cmds.select(locator_group)
            cmds.sets(e=True, forceElement="useBackground1SG")
        except:
            useBackground = cmds.shadingNode("useBackground", asShader=True)
            useBackground1SG = cmds.sets(name="useBackground1SG", renderable=True, noSurfaceShader=True, empty=True)
            cmds.connectAttr("{0}.outColor".format(useBackground), "{0}.surfaceShader".format(useBackground1SG), f=True)
            cmds.select(locator_group)
            cmds.sets(e=True, forceElement="{0}".format(useBackground1SG))            
            
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
    
    def __init__(self, text, parent=None):
        super(CollapsibleWidget, self).__init__(parent)
        
        self.header_wdg = CollapsibleHeader(text)
        self.header_wdg.clicled.connect(self.on_header_clicked)
        
        self.body_wdg = QtWidgets.QWidget()
        
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
    
    def add_widget(self, widget):
        self.body_layout.addWidget(widget)
    
    def add_layout(self, layout):
        self.body_layout.addLayout(layout)
     
    def on_header_clicked(self):
        self.set_expanded(not self.header_wdg.is_expanded())

class MM_MAIN_TAB(QtWidgets.QWidget):
    

    dlg_instance = None
        
    def __init__(self, parent=None):
        super(MM_MAIN_TAB, self).__init__(parent)
        
        self.setMinimumSize(270, 500)
        
        self.big_font = QtGui.QFont()
        #self.big_font.setPointSize(10)
        self.big_font.setBold(True)
        
        self.ccp = Create_camera_plane()
        self.d25 = Create_25D()
        self.switch = Switch()
        self.horizonLine = create_horizonLine()
        self.cameraTool = camera_tool()
        self.create_cone = create_cone()
        
        self.create_widgets()
        self.create_layout()
        self.create_connections()
        
        
    def create_widgets(self):
        #Create_plane
        self.collapsible_wdg_a = CollapsibleWidget("Create_Plane")
        self.collapsible_wdg_a.set_expanded(True)
        self.collapsible_wdg_a.set_header_background_color(QtCore.Qt.black)
        
        #btn
        create_btn_layout = QtWidgets.QHBoxLayout()
        self.create_btn = QtWidgets.QPushButton("Create")
        self.connect_btn = QtWidgets.QPushButton("Connect")
        create_btn_layout.addWidget(self.create_btn)
        create_btn_layout.addWidget(self.connect_btn)
        
        #check u,v
        chebox_layout = QtWidgets.QHBoxLayout()
        chebox_layout.setContentsMargins(2 ,2, 2, 2)
        chebox_layout.setAlignment(QtCore.Qt.AlignCenter)
        self.chebox_u = QtWidgets.QCheckBox("U")
        self.chebox_u.setChecked(True)
        self.chebox_v = QtWidgets.QCheckBox("V")
        self.chebox_v.setChecked(True)
        chebox_layout.addWidget(self.chebox_u)
        chebox_layout.addWidget(self.chebox_v)
        
        #Create_plane_layout
        self.collapsible_wdg_a.add_layout(chebox_layout)
        self.collapsible_wdg_a.add_layout(create_btn_layout)
        
        #2.5d
        self.collapsible_wdg_b = CollapsibleWidget("2.5D")
        self.collapsible_wdg_b.set_expanded(True)
        self.collapsible_wdg_b.set_header_background_color(QtCore.Qt.black)
        self.collapsible_wdg_b.add_widget(self.d25)
        self.d25.quick_import_btn.setFont(self.big_font)
        
        #SWITCH
        self.collapsible_wdg_switch = CollapsibleWidget("Swtich")
        self.collapsible_wdg_switch.set_expanded(True)
        self.collapsible_wdg_switch.set_header_background_color(QtCore.Qt.black)
        self.collapsible_wdg_switch.add_widget(self.switch)

        #horizonLine
        self.collapsible_wdg_horizonLine = CollapsibleWidget("Camera")
        self.collapsible_wdg_horizonLine.set_expanded(True)
        self.collapsible_wdg_horizonLine.set_header_background_color(QtCore.Qt.black)
        
        #btn
        self.horizonLine_btn = QtWidgets.QPushButton("horizonLine")
        self.center3d_btn = QtWidgets.QPushButton("Center3d")
        #btn_layout
        self.horizonLine_layout = QtWidgets.QHBoxLayout()
        self.horizonLine_layout.addWidget(self.horizonLine_btn)
        self.horizonLine_layout.addWidget(self.center3d_btn)
        
        self.collapsible_wdg_horizonLine.add_layout(self.horizonLine_layout)
        
        #loctor
        self.collapsible_wdg_locator = CollapsibleWidget("Locator")
        self.collapsible_wdg_locator.set_expanded(False)
        self.collapsible_wdg_locator.set_header_background_color(QtCore.Qt.black)
        
        self.cone_btn = QtWidgets.QPushButton("Create_Cone")
        self.collapsible_wdg_locator.add_widget(self.cone_btn)
        
    def create_layout(self):
        self.body_wdg = QtWidgets.QWidget()
        
        self.body_layout = QtWidgets.QVBoxLayout(self.body_wdg)
        self.body_layout.setContentsMargins(4, 2, 4, 2) 
        self.body_layout.setSpacing(2)
        self.body_layout.setAlignment(QtCore.Qt.AlignTop)
        
        self.body_layout.addWidget(self.collapsible_wdg_a)
        self.body_layout.addWidget(self.collapsible_wdg_b)
        self.body_layout.addWidget(self.collapsible_wdg_switch)
        self.body_layout.addWidget(self.collapsible_wdg_horizonLine)
        self.body_layout.addWidget(self.collapsible_wdg_locator)
        
        self.body_scrool_area = QtWidgets.QScrollArea()
        self.body_scrool_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.body_scrool_area.setWidgetResizable(True)
        self.body_scrool_area.setWidget(self.body_wdg)
        
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.body_scrool_area)
        
    def create_connections(self):
        self.create_btn.clicked.connect(self.ccp.create_plane)
        self.connect_btn.clicked.connect(self.ccp.locator_z)
        self.horizonLine_btn.clicked.connect(self.horizonLine.main)
        self.center3d_btn.clicked.connect(self.cameraTool.main)
        self.cone_btn.clicked.connect(self.create_cone.main)

class LAY_MAIN_WINDOW(QtWidgets.QWidget):
    
    @classmethod
    def display(cls):
        if not cls.dlg_instance:
            cls.dlg_instance = LAY_MAIN_WINDOW()
            
        if cls.dlg_instance.isHidden():
            cls.dlg_instance.show()
        else:
            cls.dlg_instance.raise_()
            cls.dlg_instance.activateWindow()
    
    dlg_instance = None
    
    def __init__(self, parent=maya_main_window()):
        super(LAY_MAIN_WINDOW, self).__init__(parent)
    
        self.geometry = None
        self.setWindowTitle("LAY")
        self.setWindowFlags(QtCore.Qt.WindowType.Dialog)
        self.matchmove_tab = MM_MAIN_TAB()

        self.create_widgets()
        self.create_layouts()
        self.create_connections()

    def create_widgets(self):
        self.main_tabWidget = QtWidgets.QTabWidget()
        self.main_tabWidget.addTab(self.matchmove_tab, "Matchmove")
        
    def create_layouts(self):

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.addWidget(self.main_tabWidget)
    
    def create_connections(self):
        pass
    
    def closeEvent(self, e):
        if isinstance(self, LAY_MAIN_WINDOW):
            super().closeEvent(e)
            self.geometry = self.saveGeometry()
        
    def showEvent(self, e):
            super().showEvent(e)
            
            if self.geometry:
                self.restoreGeometry(self.geometry)
    
if __name__ == "__main__":
    
    LAY_MAIN_WINDOW.display()
    