# Blender Add-on Template
# Contributor(s): Aaron Powell (aaron@lunadigital.tv)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import bpy
from . import addon_updater_ops
from . import properties
from .properties import TrankObjectItem
from bpy.props import CollectionProperty, IntProperty
from bpy.types import Panel

#
# Add additional functions here
#

class TRANK_UL_object_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # Wyświetl nazwę obiektu
        layout.label(text=item.name)

class OBJECT_OT_load_trank(bpy.types.Operator):
    """Loads trank info from selected objects"""
    bl_idname = "object.load_trank"
    bl_label = "Mark selected objects as trank"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        if obj is None or obj.type != 'MESH':
            self.report({'WARNING'}, "No mesh object selected!")
            return {'CANCELLED'}
        scene = context.scene
        for obj in context.selected_objects:
            item = scene.trank_objects.add()
            item.name = obj.name
        return {'FINISHED'}
    
class OBJECT_OT_clear_trank_objects(bpy.types.Operator):
    bl_idname = "object.clear_trank_objects"
    bl_label = "Clear"

    def execute(self, context):
        context.scene.trank_objects.clear()
        return {'FINISHED'}
    
class OBJECT_OT_load_branch(bpy.types.Operator):
    """Loads branch info from selected objects"""
    bl_idname = "object.load_branch"
    bl_label = "Mark selected objects as branch"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        if obj is None or obj.type != 'MESH':
            self.report({'WARNING'}, "No mesh object selected!")
            return {'CANCELLED'}

        return {'FINISHED'}

class VIEW3D_PT_easywindsetup_panel(bpy.types.Panel):
    """Creates a Panel in the 3D View"""
    bl_label = "Easy Wind Setup"
    bl_idname = "VIEW3D_PT_easywindsetup_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS' if bpy.app.version < (2, 80) else 'UI'
    bl_context = "objectmode"
    bl_category = "Easy Wind Setup"

    def draw(self, context):
        layout = self.layout
        # updater
        addon_updater_ops.check_for_update_background()

        layout.label(text="Load elements information")

        box_objects = layout.box()
        box_objects.operator("object.load_trank")
        row_trunk = box_objects.row()
        row_trunk.label(text=f"Trank elements: {len(context.scene.trank_objects)}")
        row_trunk.operator("object.clear_trank_objects", text="", icon="X")
        box_objects.template_list(
        "TRANK_UL_object_list",  # nazwa klasy UIList
        "",                      # unikalny identyfikator (może być pusty)
        context.scene,           # data
        "trank_objects",         # property z kolekcją
        context.scene,           # active_data
        "trank_objects_index"    # property z indeksem aktywnego elementu
        )
        box_objects.operator("object.load_branch")

        # updater
        addon_updater_ops.update_notice_box_ui(self, context)

def register():
    bpy.utils.register_class(TRANK_UL_object_list)
    bpy.types.Scene.trank_objects = bpy.props.CollectionProperty(type=TrankObjectItem)
    bpy.types.Scene.trank_objects_index = bpy.props.IntProperty(default=0)
    bpy.utils.register_class(OBJECT_OT_load_trank)
    bpy.utils.register_class(OBJECT_OT_clear_trank_objects)
    bpy.utils.register_class(OBJECT_OT_load_branch)
    bpy.utils.register_class(VIEW3D_PT_easywindsetup_panel)

def unregister():
    del bpy.types.Scene.trank_objects
    del bpy.types.Scene.trank_objects_index
    bpy.utils.unregister_class(TRANK_UL_object_list)
    bpy.utils.unregister_class(OBJECT_OT_load_trank)
    bpy.utils.unregister_class(OBJECT_OT_clear_trank_objects)
    bpy.utils.unregister_class(OBJECT_OT_load_branch)
    bpy.utils.unregister_class(VIEW3D_PT_easywindsetup_panel)
