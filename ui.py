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
from .properties import TrankObjectItem, BranchObjectItem, LeafObjectItem
from bpy.props import CollectionProperty, IntProperty
from bpy.types import Panel

#
# Add additional functions here
#

class TRANK_UL_object_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # Wyświetl nazwę obiektu
        layout.label(text=item.name)

class BRANCH_UL_object_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=item.name)

class LEAF_UL_object_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=item.name)

class OBJECT_OT_load_trank(bpy.types.Operator):
    """Loads trank info from selected objects"""
    bl_idname = "object.load_trank"
    bl_label = "Mark selected objects as trank 🌴"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        if obj is None or obj.type != 'MESH':
            self.report({'WARNING'}, "No mesh object selected!")
            return {'CANCELLED'}
        scene = context.scene
        existing_names = {item.name for item in scene.trank_objects}
        for obj in context.selected_objects:
            # Remove from other lists if present
            # Remove from branch_objects
            for i, item in reversed(list(enumerate(scene.branch_objects))):
                if item.name == obj.name:
                    scene.branch_objects.remove(i)
            # Remove from leaf_objects
            for i, item in reversed(list(enumerate(scene.leaf_objects))):
                if item.name == obj.name:
                    scene.leaf_objects.remove(i)
            if obj.name not in existing_names:
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
    bl_label = "Mark selected objects as branch 🌿"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        if obj is None or obj.type != 'MESH':
            self.report({'WARNING'}, "No mesh object selected!")
            return {'CANCELLED'}
        scene = context.scene
        existing_names = {item.name for item in scene.branch_objects}
        for obj in context.selected_objects:
            # Remove from other lists if present
            for i, item in reversed(list(enumerate(scene.trank_objects))):
                if item.name == obj.name:
                    scene.trank_objects.remove(i)
            for i, item in reversed(list(enumerate(scene.leaf_objects))):
                if item.name == obj.name:
                    scene.leaf_objects.remove(i)
            if obj.name not in existing_names:
                item = scene.branch_objects.add()
                item.name = obj.name
        return {'FINISHED'}

class OBJECT_OT_clear_branch_objects(bpy.types.Operator):
    bl_idname = "object.clear_branch_objects"
    bl_label = "Clear"

    def execute(self, context):
        context.scene.branch_objects.clear()
        return {'FINISHED'}

class OBJECT_OT_load_leaf(bpy.types.Operator):
    """Loads leaf info from selected objects"""
    bl_idname = "object.load_leaf"
    bl_label = "Mark selected objects as leaf 🍁"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        if obj is None or obj.type != 'MESH':
            self.report({'WARNING'}, "No mesh object selected!")
            return {'CANCELLED'}
        scene = context.scene
        existing_names = {item.name for item in scene.leaf_objects}
        for obj in context.selected_objects:
            # Remove from other lists if present
            for i, item in reversed(list(enumerate(scene.trank_objects))):
                if item.name == obj.name:
                    scene.trank_objects.remove(i)
            for i, item in reversed(list(enumerate(scene.branch_objects))):
                if item.name == obj.name:
                    scene.branch_objects.remove(i)
            if obj.name not in existing_names:
                item = scene.leaf_objects.add()
                item.name = obj.name
        return {'FINISHED'}

class OBJECT_OT_clear_leaf_objects(bpy.types.Operator):
    bl_idname = "object.clear_leaf_objects"
    bl_label = "Clear"

    def execute(self, context):
        context.scene.leaf_objects.clear()
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

        # Trank
        box_objects = layout.box()
        box_objects.operator("object.load_trank")
        row_trunk = box_objects.row()
        row_trunk.label(text=f"Trank elements: {len(context.scene.trank_objects)}")
        row_trunk.operator("object.clear_trank_objects", text="", icon="X")
        box_objects.template_list(
            "TRANK_UL_object_list",
            "",
            context.scene,
            "trank_objects",
            context.scene,
            "trank_objects_index"
        )

        # Branches
        box_objects.operator("object.load_branch")
        row_branch = box_objects.row()
        row_branch.label(text=f"Branch elements: {len(context.scene.branch_objects)}")
        row_branch.operator("object.clear_branch_objects", text="", icon="X")
        box_objects.template_list(
            "BRANCH_UL_object_list",
            "",
            context.scene,
            "branch_objects",
            context.scene,
            "branch_objects_index"
        )

        # Leaves
        box_objects.operator("object.load_leaf")
        row_leaf = box_objects.row()
        row_leaf.label(text=f"Leaf elements: {len(context.scene.leaf_objects)}")
        row_leaf.operator("object.clear_leaf_objects", text="", icon="X")
        box_objects.template_list(
            "LEAF_UL_object_list",
            "",
            context.scene,
            "leaf_objects",
            context.scene,
            "leaf_objects_index"
        )

        # updater
        addon_updater_ops.update_notice_box_ui(self, context)

def register():
    bpy.utils.register_class(TRANK_UL_object_list)
    bpy.utils.register_class(BRANCH_UL_object_list)
    bpy.utils.register_class(LEAF_UL_object_list)
    bpy.types.Scene.trank_objects = bpy.props.CollectionProperty(type=TrankObjectItem)
    bpy.types.Scene.trank_objects_index = bpy.props.IntProperty(default=0)
    bpy.types.Scene.branch_objects = bpy.props.CollectionProperty(type=BranchObjectItem)
    bpy.types.Scene.branch_objects_index = bpy.props.IntProperty(default=0)
    bpy.types.Scene.leaf_objects = bpy.props.CollectionProperty(type=LeafObjectItem)
    bpy.types.Scene.leaf_objects_index = bpy.props.IntProperty(default=0)
    bpy.utils.register_class(OBJECT_OT_load_trank)
    bpy.utils.register_class(OBJECT_OT_clear_trank_objects)
    bpy.utils.register_class(OBJECT_OT_load_branch)
    bpy.utils.register_class(OBJECT_OT_clear_branch_objects)
    bpy.utils.register_class(OBJECT_OT_load_leaf)
    bpy.utils.register_class(OBJECT_OT_clear_leaf_objects)
    bpy.utils.register_class(VIEW3D_PT_easywindsetup_panel)

def unregister():
    del bpy.types.Scene.trank_objects
    del bpy.types.Scene.trank_objects_index
    del bpy.types.Scene.branch_objects
    del bpy.types.Scene.branch_objects_index
    del bpy.types.Scene.leaf_objects
    del bpy.types.Scene.leaf_objects_index
    bpy.utils.unregister_class(TRANK_UL_object_list)
    bpy.utils.unregister_class(BRANCH_UL_object_list)
    bpy.utils.unregister_class(LEAF_UL_object_list)
    bpy.utils.unregister_class(OBJECT_OT_load_trank)
    bpy.utils.unregister_class(OBJECT_OT_clear_trank_objects)
    bpy.utils.unregister_class(OBJECT_OT_load_branch)
    bpy.utils.unregister_class(OBJECT_OT_clear_branch_objects)
    bpy.utils.unregister_class(OBJECT_OT_load_leaf)
    bpy.utils.unregister_class(OBJECT_OT_clear_leaf_objects)
    bpy.utils.unregister_class(VIEW3D_PT_easywindsetup_panel)
