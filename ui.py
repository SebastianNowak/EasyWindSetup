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
from .properties import TrunkObjectItem, BranchObjectItem, LeafObjectItem
from bpy.props import CollectionProperty, IntProperty
from bpy.types import Panel
import mathutils
import re
import difflib

#
# Add additional functions here
#

class TRUNK_UL_object_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # Wyświetl nazwę obiektu
        layout.label(text=item.name)

class BRANCH_UL_object_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=item.name)

class LEAF_UL_object_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=item.name)

class OBJECT_OT_load_trunk(bpy.types.Operator):
    """Loads trunk info from selected objects"""
    bl_idname = "object.load_trunk"
    bl_label = "Mark selected objects as trunk 🌴"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        if obj is None or obj.type != 'MESH':
            self.report({'WARNING'}, "No mesh object selected!")
            return {'CANCELLED'}
        scene = context.scene
        existing_names = {item.name for item in scene.trunk_objects}
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
                item = scene.trunk_objects.add()
                item.name = obj.name
        return {'FINISHED'}
    
class OBJECT_OT_clear_trunk_objects(bpy.types.Operator):
    bl_idname = "object.clear_trunk_objects"
    bl_label = "Clear"

    def execute(self, context):
        context.scene.trunk_objects.clear()
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
            for i, item in reversed(list(enumerate(scene.trunk_objects))):
                if item.name == obj.name:
                    scene.trunk_objects.remove(i)
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
            for i, item in reversed(list(enumerate(scene.trunk_objects))):
                if item.name == obj.name:
                    scene.trunk_objects.remove(i)
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

class OBJECT_OT_set_pivot_to_meshes_auto(bpy.types.Operator):
    """Set Pivot to Meshes (auto)"""
    bl_idname = "object.set_pivot_to_meshes_auto"
    bl_label = "Set Pivot to Meshes (auto)"

    def execute(self, context):
        scene = context.scene
        trunk_names = [item.name for item in scene.trunk_objects]
        branch_names = [item.name for item in scene.branch_objects]
        leaf_names = [item.name for item in scene.leaf_objects]

        # Zbierz wszystkie vertexy z trunk (w globalnych)
        trunk_verts = []
        for name in trunk_names:
            obj = bpy.data.objects.get(name)
            if obj and obj.type == 'MESH':
                mesh = obj.data
                mat = obj.matrix_world
                trunk_verts.extend([mat @ v.co for v in mesh.vertices])

        # Zbierz wszystkie vertexy z branch (w globalnych)
        branch_verts = []
        for name in branch_names:
            obj = bpy.data.objects.get(name)
            if obj and obj.type == 'MESH':
                mesh = obj.data
                mat = obj.matrix_world
                branch_verts.extend([mat @ v.co for v in mesh.vertices])

        # Dla każdego branch: znajdź najbliższy vertex w trunk względem vertexów branch i ustaw pivot na tym vertexie
        if trunk_verts:
            for name in branch_names:
                obj = bpy.data.objects.get(name)
                if obj and obj.type == 'MESH':
                    obj_mesh = obj.data
                    obj_mat = obj.matrix_world
                    verts_global = [obj_mat @ v.co for v in obj_mesh.vertices]
                    min_dist = None
                    nearest_branch_v = None
                    nearest_trunk_v = None
                    for v_branch in verts_global:
                        for v_trunk in trunk_verts:
                            dist = (v_branch - v_trunk).length
                            if min_dist is None or dist < min_dist:
                                min_dist = dist
                                nearest_trunk_v = v_trunk
                                nearest_branch_v = v_branch
                    if nearest_branch_v is not None:
                        delta = nearest_branch_v - obj.location
                        obj.data.transform(mathutils.Matrix.Translation(-delta))
                        obj.location = nearest_branch_v

        # Dla każdego leaf: znajdź najbliższy vertex w branch względem vertexów leaf i ustaw pivot na tym vertexie
        if branch_verts:
            for name in leaf_names:
                obj = bpy.data.objects.get(name)
                if obj and obj.type == 'MESH':
                    obj_mesh = obj.data
                    obj_mat = obj.matrix_world
                    verts_global = [obj_mat @ v.co for v in obj_mesh.vertices]
                    min_dist = None
                    nearest_leaf_v = None
                    nearest_branch_v = None
                    for v_leaf in verts_global:
                        for v_branch in branch_verts:
                            dist = (v_leaf - v_branch).length
                            if min_dist is None or dist < min_dist:
                                min_dist = dist
                                nearest_branch_v = v_branch
                                nearest_leaf_v = v_leaf
                    if nearest_leaf_v is not None:
                        delta = nearest_leaf_v - obj.location
                        obj.data.transform(mathutils.Matrix.Translation(-delta))
                        obj.location = nearest_leaf_v

        self.report({'INFO'}, "Pivots set for branch and leaf objects")
        return {'FINISHED'}

class OBJECT_OT_pivot_to_center(bpy.types.Operator):
    bl_idname = "object.pivot_to_center"
    bl_label = "Pivot to center"
    def execute(self, context):
        self.report({'INFO'}, "Pivot to center pressed")
        return {'FINISHED'}

class OBJECT_OT_break_object_apart(bpy.types.Operator):
    bl_idname = "object.break_object_apart"
    bl_label = "Break Object apart"
    def execute(self, context):
        self.report({'INFO'}, "Break Object apart pressed")
        return {'FINISHED'}

class OBJECT_OT_set_pivot_to_mesh_manually(bpy.types.Operator):
    bl_idname = "object.set_pivot_to_mesh_manually"
    bl_label = "Set Pivot to Mesh (manually)"
    def execute(self, context):
        self.report({'INFO'}, "Set Pivot to Mesh (manually) pressed")
        return {'FINISHED'}

class OBJECT_OT_fix_pivot_rotation(bpy.types.Operator):
    bl_idname = "object.fix_pivot_rotation"
    bl_label = "Fix Pivot Rotation"
    def execute(self, context):
        self.report({'INFO'}, "Fix Pivot Rotation pressed")
        return {'FINISHED'}

class OBJECT_OT_set_pivot_from_uv(bpy.types.Operator):
    bl_idname = "object.set_pivot_from_uv"
    bl_label = "Set Pivot from UV"
    def execute(self, context):
        self.report({'INFO'}, "Set Pivot from UV pressed")
        return {'FINISHED'}

class OBJECT_OT_fix_pivot_rotation_from_uv(bpy.types.Operator):
    bl_idname = "object.fix_pivot_rotation_from_uv"
    bl_label = "Fix Pivot Rotation from UV"
    def execute(self, context):
        self.report({'INFO'}, "Fix Pivot Rotation from UV pressed")
        return {'FINISHED'}

class OBJECT_OT_fix_pivot_rotation_from_uv_xz(bpy.types.Operator):
    bl_idname = "object.fix_pivot_rotation_from_uv_xz"
    bl_label = "Fix Pivot Rotation from UV (X & Z)"
    def execute(self, context):
        self.report({'INFO'}, "Fix Pivot Rotation from UV (X & Z) pressed")
        return {'FINISHED'}

class OBJECT_OT_get_by_names(bpy.types.Operator):
    bl_idname = "object.get_by_names"
    bl_label = "Get by names"

    def execute(self, context):
        scene = context.scene
        print("=== [EasyWindSetup] get_by_names execution ===")
        scene.trunk_objects.clear()
        scene.branch_objects.clear()
        scene.leaf_objects.clear()

        # Patterns for each type (more typos included)
        trunk_patterns = [
            "trunk", "trnk", "trun", "trunc", "trank", "truncj", "truncs", "truncx", "truncz",
            "trunl", "trunm", "trunck", "truncq", "truncw", "truncv", "truncb", "truncn", "truncg", "trunks"
        ]
        branch_patterns = [
            "branch", "brnch", "branc", "brnach", "branh", "branck", "bracnh", "bracn", "bracch", "branxh",
            "brabch", "brabnch", "brancc", "brancg", "branvh", "branbh", "branqh", "branwh", "branmh", "branah",
            "branrh", "brunch", "brancj", "branches"
        ]
        leaf_patterns = [
            "leaf", "leav", "leafe", "leave", "leef", "leavf", "lefa", "lefae", "leavc", "leacf", "leqf",
            "leawf", "leazf", "leasf", "leavd", "leafv", "leabf", "leapf", "leatf", "leaff", "leafff",
            "leavff", "leavv", "leavvv", "leaves", "leafs"
        ]

        # Helper: find the pattern that matches closest to the end of the name
        def find_best_pattern(name, patterns):
            name_lower = name.lower()
            best_idx = -1
            best_pat = None
            for pat in patterns:
                pat_lower = pat.lower()
                idx = name_lower.rfind(pat_lower)
                if idx != -1 and idx + len(pat_lower) > best_idx:
                    best_idx = idx + len(pat_lower)
                    best_pat = pat_lower
            return best_pat, best_idx

        assigned = set()
        obj_to_type = {}

        # 1. Try assign by object name (from the end)
        for obj in bpy.data.objects:
            if obj.type != 'MESH':
                continue
            name = obj.name
            trunk_pat, trunk_idx = find_best_pattern(name, trunk_patterns)
            branch_pat, branch_idx = find_best_pattern(name, branch_patterns)
            leaf_pat, leaf_idx = find_best_pattern(name, leaf_patterns)
            # Find which pattern is closest to the end
            best = max(
                [("trunk", trunk_idx), ("branch", branch_idx), ("leaf", leaf_idx)],
                key=lambda x: x[1] if x[1] is not None else -1
            )
            if best[1] is not None and best[1] >= 0:
                if best[0] == "trunk":
                    item = scene.trunk_objects.add()
                elif best[0] == "branch":
                    item = scene.branch_objects.add()
                elif best[0] == "leaf":
                    item = scene.leaf_objects.add()
                item.name = obj.name
                assigned.add(obj.name)
                obj_to_type[obj.name] = best[0]
                print(f"[object name assign] {obj.name} -> {best[0]} (pattern at idx {best[1]})")
            else:
                obj_to_type[obj.name] = None

        # 2. Try assign by material names (from the end) for unassigned objects
        for obj in bpy.data.objects:
            if obj.type != 'MESH' or obj.name in assigned:
                continue
            mat_names = [slot.material.name for slot in obj.material_slots if slot.material]
            if hasattr(obj, "active_material") and obj.active_material:
                active_mat_name = obj.active_material.name
                if active_mat_name not in mat_names:
                    mat_names.append(active_mat_name)
            best_type = None
            best_idx = -1
            for mat_name in mat_names:
                trunk_pat, trunk_idx = find_best_pattern(mat_name, trunk_patterns)
                branch_pat, branch_idx = find_best_pattern(mat_name, branch_patterns)
                leaf_pat, leaf_idx = find_best_pattern(mat_name, leaf_patterns)
                local_best = max(
                    [("trunk", trunk_idx), ("branch", branch_idx), ("leaf", leaf_idx)],
                    key=lambda x: x[1] if x[1] is not None else -1
                )
                if local_best[1] is not None and local_best[1] > best_idx:
                    best_type = local_best[0]
                    best_idx = local_best[1]
            if best_type:
                if best_type == "trunk":
                    item = scene.trunk_objects.add()
                elif best_type == "branch":
                    item = scene.branch_objects.add()
                elif best_type == "leaf":
                    item = scene.leaf_objects.add()
                item.name = obj.name
                assigned.add(obj.name)
                obj_to_type[obj.name] = best_type
                print(f"[material name assign] {obj.name} -> {best_type} (pattern at idx {best_idx})")

        # 3. If any collection is empty, try to infer pattern from other collections (by name or material)
        def infer_pattern(collection, patterns):
            names = [item.name.lower() for item in collection]
            if not names:
                return None
            substr = names[0]
            for n in names[1:]:
                match = difflib.SequenceMatcher(None, substr, n).find_longest_match(0, len(substr), 0, len(n))
                if match.size > 2:
                    substr = substr[match.a:match.a+match.size]
                else:
                    substr = ""
            if substr and substr not in [p.lower() for p in patterns]:
                return substr
            return None

        all_mesh_objs = [obj for obj in bpy.data.objects if obj.type == 'MESH' and obj.name not in assigned]
        # Trunk
        if len(scene.trunk_objects) == 0 and (len(scene.branch_objects) > 0 or len(scene.leaf_objects) > 0):
            pattern = infer_pattern(scene.branch_objects, branch_patterns) or infer_pattern(scene.leaf_objects, leaf_patterns)
            if pattern:
                for obj in all_mesh_objs:
                    if pattern in obj.name.lower():
                        item = scene.trunk_objects.add()
                        item.name = obj.name
                        assigned.add(obj.name)
                        print(f"[infer name] {obj.name} -> trunk (pattern: {pattern})")
        # Branch
        if len(scene.branch_objects) == 0 and (len(scene.trunk_objects) > 0 or len(scene.leaf_objects) > 0):
            pattern = infer_pattern(scene.trunk_objects, trunk_patterns) or infer_pattern(scene.leaf_objects, leaf_patterns)
            if pattern:
                for obj in all_mesh_objs:
                    if pattern in obj.name.lower():
                        item = scene.branch_objects.add()
                        item.name = obj.name
                        assigned.add(obj.name)
                        print(f"[infer name] {obj.name} -> branch (pattern: {pattern})")
        # Leaf
        if len(scene.leaf_objects) == 0 and (len(scene.trunk_objects) > 0 or len(scene.branch_objects) > 0):
            pattern = infer_pattern(scene.trunk_objects, trunk_patterns) or infer_pattern(scene.branch_objects, branch_patterns)
            if pattern:
                for obj in all_mesh_objs:
                    if pattern in obj.name.lower():
                        item = scene.leaf_objects.add()
                        item.name = obj.name
                        assigned.add(obj.name)
                        print(f"[infer name] {obj.name} -> leaf (pattern: {pattern})")

        # Try to infer by material names if still empty
        all_mesh_objs = [obj for obj in bpy.data.objects if obj.type == 'MESH' and obj.name not in assigned]
        # Trunk
        if len(scene.trunk_objects) == 0:
            for obj in all_mesh_objs:
                mat_names = [slot.material.name for slot in obj.material_slots if slot.material]
                if hasattr(obj, "active_material") and obj.active_material:
                    active_mat_name = obj.active_material.name
                    if active_mat_name not in mat_names:
                        mat_names.append(active_mat_name)
                for mat_name in mat_names:
                    if mat_name and mat_name.lower() not in assigned:
                        if any(pat in mat_name.lower() for pat in trunk_patterns):
                            item = scene.trunk_objects.add()
                            item.name = obj.name
                            assigned.add(obj.name)
                            print(f"[infer material] {obj.name} ({mat_name}) -> trunk")
                            break
        # Branch
        if len(scene.branch_objects) == 0:
            for obj in all_mesh_objs:
                mat_names = [slot.material.name for slot in obj.material_slots if slot.material]
                if hasattr(obj, "active_material") and obj.active_material:
                    active_mat_name = obj.active_material.name
                    if active_mat_name not in mat_names:
                        mat_names.append(active_mat_name)
                for mat_name in mat_names:
                    if mat_name and mat_name.lower() not in assigned:
                        if any(pat in mat_name.lower() for pat in branch_patterns):
                            item = scene.branch_objects.add()
                            item.name = obj.name
                            assigned.add(obj.name)
                            print(f"[infer material] {obj.name} ({mat_name}) -> branch")
                            break
        # Leaf
        if len(scene.leaf_objects) == 0:
            for obj in all_mesh_objs:
                mat_names = [slot.material.name for slot in obj.material_slots if slot.material]
                if hasattr(obj, "active_material") and obj.active_material:
                    active_mat_name = obj.active_material.name
                    if active_mat_name not in mat_names:
                        mat_names.append(active_mat_name)
                for mat_name in mat_names:
                    if mat_name and mat_name.lower() not in assigned:
                        if any(pat in mat_name.lower() for pat in leaf_patterns):
                            item = scene.leaf_objects.add()
                            item.name = obj.name
                            assigned.add(obj.name)
                            print(f"[infer material] {obj.name} ({mat_name}) -> leaf")
                            break

        # Ensure no duplicates between collections
        def remove_duplicates(coll_a, coll_b):
            names_b = {item.name for item in coll_b}
            for i in reversed(range(len(coll_a))):
                if coll_a[i].name in names_b:
                    coll_a.remove(i)
        remove_duplicates(scene.trunk_objects, scene.branch_objects)
        remove_duplicates(scene.trunk_objects, scene.leaf_objects)
        remove_duplicates(scene.branch_objects, scene.trunk_objects)
        remove_duplicates(scene.branch_objects, scene.leaf_objects)
        remove_duplicates(scene.leaf_objects, scene.trunk_objects)
        remove_duplicates(scene.leaf_objects, scene.branch_objects)

        self.report({'INFO'}, "Collections filled by names")
        print("=== [EasyWindSetup] get_by_names execution END ===")
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

        # --- DODATKOWE PRZYCISKI NA GÓRZE ---
        layout.operator("object.break_object_apart", text="Break Object apart")
        layout.separator()
        layout.operator("object.pivot_to_center", text="Pivot to center")
        layout.operator("object.set_pivot_to_mesh_manually", text="Set Pivot to Mesh (manually)")
        layout.operator("object.set_pivot_from_uv", text="Set Pivot from UV")
        layout.separator()
        layout.operator("object.fix_pivot_rotation", text="Fix Pivot Rotation")
        row = layout.row(align=True)
        row.operator("object.fix_pivot_rotation_from_uv", text="Fix Pivot Rotation from UV")
        row.operator("object.fix_pivot_rotation_from_uv_xz", text="Fix Pivot Rotation from UV (X & Z)")
        layout.separator()

        # Przycisk Set Pivot to Meshes (auto) NAD labelem
        enabled = (
            len(context.scene.trunk_objects) > 0 and
            len(context.scene.branch_objects) > 0 and
            len(context.scene.leaf_objects) > 0
        )
        row = layout.row()
        row.enabled = enabled
        row.operator("object.set_pivot_to_meshes_auto", icon="PIVOT_BOUNDBOX")

        # Label + Get by names obok siebie
        row = layout.row(align=True)
        row.label(text="Informations required for auto setup:")
        row.operator("object.get_by_names", text="Get by names", icon="VIEWZOOM")

        # Trunk
        box_objects = layout.box()
        row_trunk = box_objects.row()
        row_trunk.label(text=f"Trunk elements: {len(context.scene.trunk_objects)}")
        row_trunk.operator("object.load_trunk")
        row_trunk.operator("object.clear_trunk_objects", text="", icon="X")
        box_objects.template_list(
            "TRUNK_UL_object_list",
            "",
            context.scene,
            "trunk_objects",
            context.scene,
            "trunk_objects_index"
        )

        # Branches
        row_branch = box_objects.row()
        row_branch.label(text=f"Branch elements: {len(context.scene.branch_objects)}")
        row_branch.operator("object.load_branch")
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
        row_leaf = box_objects.row()
        row_leaf.label(text=f"Leaf elements: {len(context.scene.leaf_objects)}")
        row_leaf.operator("object.load_leaf")
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
    bpy.utils.register_class(TRUNK_UL_object_list)
    bpy.utils.register_class(BRANCH_UL_object_list)
    bpy.utils.register_class(LEAF_UL_object_list)
    bpy.types.Scene.trunk_objects = bpy.props.CollectionProperty(type=TrunkObjectItem)
    bpy.types.Scene.trunk_objects_index = bpy.props.IntProperty(default=0)
    bpy.types.Scene.branch_objects = bpy.props.CollectionProperty(type=BranchObjectItem)
    bpy.types.Scene.branch_objects_index = bpy.props.IntProperty(default=0)
    bpy.types.Scene.leaf_objects = bpy.props.CollectionProperty(type=LeafObjectItem)
    bpy.types.Scene.leaf_objects_index = bpy.props.IntProperty(default=0)
    bpy.utils.register_class(OBJECT_OT_load_trunk)
    bpy.utils.register_class(OBJECT_OT_clear_trunk_objects)
    bpy.utils.register_class(OBJECT_OT_load_branch)
    bpy.utils.register_class(OBJECT_OT_clear_branch_objects)
    bpy.utils.register_class(OBJECT_OT_load_leaf)
    bpy.utils.register_class(OBJECT_OT_clear_leaf_objects)
    bpy.utils.register_class(OBJECT_OT_set_pivot_to_meshes_auto)
    bpy.utils.register_class(OBJECT_OT_pivot_to_center)
    bpy.utils.register_class(OBJECT_OT_break_object_apart)
    bpy.utils.register_class(OBJECT_OT_set_pivot_to_mesh_manually)
    bpy.utils.register_class(OBJECT_OT_fix_pivot_rotation)
    bpy.utils.register_class(OBJECT_OT_set_pivot_from_uv)
    bpy.utils.register_class(OBJECT_OT_fix_pivot_rotation_from_uv)
    bpy.utils.register_class(OBJECT_OT_fix_pivot_rotation_from_uv_xz)
    bpy.utils.register_class(OBJECT_OT_get_by_names)
    bpy.utils.register_class(VIEW3D_PT_easywindsetup_panel)

def unregister():
    del bpy.types.Scene.trunk_objects
    del bpy.types.Scene.trunk_objects_index
    del bpy.types.Scene.branch_objects
    del bpy.types.Scene.branch_objects_index
    del bpy.types.Scene.leaf_objects
    del bpy.types.Scene.leaf_objects_index
    bpy.utils.unregister_class(TRUNK_UL_object_list)
    bpy.utils.unregister_class(BRANCH_UL_object_list)
    bpy.utils.unregister_class(LEAF_UL_object_list)
    bpy.utils.unregister_class(OBJECT_OT_load_trunk)
    bpy.utils.unregister_class(OBJECT_OT_clear_trunk_objects)
    bpy.utils.unregister_class(OBJECT_OT_load_branch)
    bpy.utils.unregister_class(OBJECT_OT_clear_branch_objects)
    bpy.utils.unregister_class(OBJECT_OT_load_leaf)
    bpy.utils.unregister_class(OBJECT_OT_clear_leaf_objects)
    bpy.utils.unregister_class(OBJECT_OT_set_pivot_to_meshes_auto)
    bpy.utils.unregister_class(OBJECT_OT_pivot_to_center)
    bpy.utils.unregister_class(OBJECT_OT_break_object_apart)
    bpy.utils.unregister_class(OBJECT_OT_set_pivot_to_mesh_manually)
    bpy.utils.unregister_class(OBJECT_OT_fix_pivot_rotation)
    bpy.utils.unregister_class(OBJECT_OT_set_pivot_from_uv)
    bpy.utils.unregister_class(OBJECT_OT_fix_pivot_rotation_from_uv)
    bpy.utils.unregister_class(OBJECT_OT_fix_pivot_rotation_from_uv_xz)
    bpy.utils.unregister_class(OBJECT_OT_get_by_names)
    bpy.utils.unregister_class(VIEW3D_PT_easywindsetup_panel)
    bpy.utils.unregister_class(VIEW3D_PT_easywindsetup_panel)
    bpy.utils.unregister_class(OBJECT_OT_set_pivot_to_mesh_manually)
    bpy.utils.unregister_class(OBJECT_OT_fix_pivot_rotation)
    bpy.utils.unregister_class(OBJECT_OT_set_pivot_from_uv)
    bpy.utils.unregister_class(OBJECT_OT_fix_pivot_rotation_from_uv)
    bpy.utils.unregister_class(OBJECT_OT_fix_pivot_rotation_from_uv_xz)
    bpy.utils.unregister_class(OBJECT_OT_get_by_names)
    bpy.utils.unregister_class(VIEW3D_PT_easywindsetup_panel)
    bpy.utils.unregister_class(VIEW3D_PT_easywindsetup_panel)
    bpy.utils.unregister_class(OBJECT_OT_clear_trunk_objects)
    bpy.utils.unregister_class(OBJECT_OT_load_branch)
    bpy.utils.unregister_class(OBJECT_OT_clear_branch_objects)
    bpy.utils.unregister_class(OBJECT_OT_load_leaf)
    bpy.utils.unregister_class(OBJECT_OT_clear_leaf_objects)
    bpy.utils.unregister_class(OBJECT_OT_set_pivot_to_meshes_auto)
    bpy.utils.unregister_class(OBJECT_OT_pivot_to_center)
    bpy.utils.unregister_class(OBJECT_OT_break_object_apart)
    bpy.utils.unregister_class(OBJECT_OT_set_pivot_to_mesh_manually)
    bpy.utils.unregister_class(OBJECT_OT_fix_pivot_rotation)
    bpy.utils.unregister_class(OBJECT_OT_set_pivot_from_uv)
    bpy.utils.unregister_class(OBJECT_OT_fix_pivot_rotation_from_uv)
    bpy.utils.unregister_class(OBJECT_OT_fix_pivot_rotation_from_uv_xz)
    bpy.utils.unregister_class(OBJECT_OT_get_by_names)
    bpy.utils.unregister_class(VIEW3D_PT_easywindsetup_panel)
    bpy.utils.unregister_class(VIEW3D_PT_easywindsetup_panel)
    bpy.utils.unregister_class(OBJECT_OT_set_pivot_to_mesh_manually)
    bpy.utils.unregister_class(OBJECT_OT_fix_pivot_rotation)
    bpy.utils.unregister_class(OBJECT_OT_set_pivot_from_uv)
    bpy.utils.unregister_class(OBJECT_OT_fix_pivot_rotation_from_uv)
    bpy.utils.unregister_class(OBJECT_OT_fix_pivot_rotation_from_uv_xz)
    bpy.utils.unregister_class(OBJECT_OT_get_by_names)
    bpy.utils.unregister_class(VIEW3D_PT_easywindsetup_panel)
    bpy.utils.unregister_class(VIEW3D_PT_easywindsetup_panel)
