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
import bmesh
from mathutils import Vector
import mathutils

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
    bl_options = {'REGISTER', 'UNDO'}

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
    bl_options = {'REGISTER', 'UNDO'}

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
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.leaf_objects.clear()
        return {'FINISHED'}

class OBJECT_OT_set_pivot_to_meshes_auto(bpy.types.Operator):
    """Set Pivot to Meshes (auto)"""
    bl_idname = "object.set_pivot_to_meshes_auto"
    bl_label = "Set Pivot to Meshes (auto)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        import time
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

        # Loader/progress bar setup
        total = len(branch_names) + len(leaf_names)
        done = 0

        wm = context.window_manager
        wm.progress_begin(0, total)

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
                done += 1
                wm.progress_update(done)
                # time.sleep(0.01) # optionally slow down for testing

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
                done += 1
                wm.progress_update(done)
                # time.sleep(0.01) # optionally slow down for testing

        wm.progress_end()
        self.report({'INFO'}, "Pivots set for branch and leaf objects")
        return {'FINISHED'}

class OBJECT_OT_set_pivot_to_mesh_manually(bpy.types.Operator):
    bl_idname = "object.set_pivot_to_mesh_manually"
    bl_label = "Set Pivot to Mesh (🡓) (manually)"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        import time
        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'WARNING'}, "No objects selected!")
            return {'CANCELLED'}

        wm = context.window_manager
        wm.progress_begin(0, len(selected_objects))
        for idx, obj in enumerate(selected_objects):
            if obj.type != 'MESH':
                self.report({'WARNING'}, f"Skipping {obj.name}, as it is not a mesh object.")
                wm.progress_update(idx + 1)
                continue

            # Store the current active object
            original_active_object = context.view_layer.objects.active

            # Switch to edit mode for the current object
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='EDIT')

            # Get mesh data and find the two lowest vertices
            bm = bmesh.from_edit_mesh(obj.data)
            lowest_verts = sorted(bm.verts, key=lambda v: v.co.z)[:2]

            if len(lowest_verts) < 2:
                self.report({'WARNING'}, f"{obj.name} has less than two vertices!")
                bpy.ops.object.mode_set(mode='OBJECT')
                continue

            # Calculate the midpoint of the two lowest vertices
            mid_point = (lowest_verts[0].co + lowest_verts[1].co) / 2

            # Wypisz wartość mid_point w konsoli Blender'a
            print(f"Object: {obj.name}, Midpoint: {mid_point}")

            # Switch back to object mode
            bpy.ops.object.mode_set(mode='OBJECT')

            # Set the cursor to the calculated midpoint in world space
            bpy.context.scene.cursor.location = obj.matrix_world @ mid_point

            # Set the origin to the cursor without moving the object
            bpy.ops.object.select_all(action='DESELECT')  # Deselect all objects
            obj.select_set(True)  # Select the current object
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='BOUNDS')

            # Restore the original active object
            bpy.context.view_layer.objects.active = original_active_object
            wm.progress_update(idx + 1)
        wm.progress_end()
        return {'FINISHED'}

class OBJECT_OT_set_pivot_to_mesh_manually_up(bpy.types.Operator):
    bl_idname = "object.set_pivot_to_mesh_manually_up"
    bl_label = "Set Pivot To Mesh (🡑) (manually)"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        import time
        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'WARNING'}, "No objects selected!")
            return {'CANCELLED'}

        wm = context.window_manager
        wm.progress_begin(0, len(selected_objects))
        for idx, obj in enumerate(selected_objects):
            if obj.type != 'MESH':
                self.report({'WARNING'}, f"Skipping {obj.name}, as it is not a mesh object.")
                wm.progress_update(idx + 1)
                continue

            # Store the current active object
            original_active_object = context.view_layer.objects.active

            # Switch to edit mode for the current object
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='EDIT')

            # Get mesh data and find the two highest vertices
            bm = bmesh.from_edit_mesh(obj.data)
            highest_verts = sorted(bm.verts, key=lambda v: v.co.z, reverse=True)[:2]

            if len(highest_verts) < 2:
                self.report({'WARNING'}, f"{obj.name} has less than two vertices!")
                bpy.ops.object.mode_set(mode='OBJECT')
                continue

            # Calculate the midpoint of the two highest vertices
            mid_point = (highest_verts[0].co + highest_verts[1].co) / 2

            # Wypisz wartość mid_point w konsoli Blender'a
            print(f"Object: {obj.name}, Midpoint: {mid_point}")

            # Switch back to object mode
            bpy.ops.object.mode_set(mode='OBJECT')

            # Set the cursor to the calculated midpoint in world space
            bpy.context.scene.cursor.location = obj.matrix_world @ mid_point

            # Set the origin to the cursor without moving the object
            bpy.ops.object.select_all(action='DESELECT')  # Deselect all objects
            obj.select_set(True)  # Select the current object
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='BOUNDS')

            # Restore the original active object
            bpy.context.view_layer.objects.active = original_active_object
            wm.progress_update(idx + 1)
        wm.progress_end()
        return {'FINISHED'}

def boundboxAxis(pp, obj):
    """Estimates the X vector from the origin point and boundbox vertices."""
    bbvv = [None for _ in range(8)]
    bbLength = [None for _ in range(8)]
    ws = obj.matrix_world.to_scale()

    for i in range(8):
        bbvv[i] = mathutils.Vector((
            obj.bound_box[i][0] * ws[0],
            obj.bound_box[i][1] * ws[1],
            obj.bound_box[i][2] * ws[2]
        ))  # Create a vector list for each vert of the bounding box (from origin point)
        bbLength[i] = bbvv[i].length  # Create list with the lengths

    # Find the furthest points from origin
    highestVertexId = 0
    for i in range(1, 8):  # Find the furthest point
        if bbLength[highestVertexId] < bbLength[i]:
            highestVertexId = i

    fvidlist = []
    for i in range(8):  # Check if other vertex have roughly the same distance
        if bbLength[i] >= (bbLength[highestVertexId] * 0.95):  # Tolerance range for similar distances
            fvidlist.append(i)

    # Get an average position
    axisdir = mathutils.Vector((0.0, 0.0, 0.0))
    for i in range(len(fvidlist)):
        axisdir += bbvv[fvidlist[i]]
    axisdir /= len(fvidlist)

    vecout = axisdir.normalized()
    axisextent = axisdir.length
    return vecout, axisextent

class OBJECT_OT_fix_pivot_rotation(bpy.types.Operator):
    bl_idname = "object.fix_pivot_rotation"
    bl_label = "Fix Pivot Rotation"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        import time
        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'WARNING'}, "No objects selected!")
            return {'CANCELLED'}

        wm = context.window_manager
        wm.progress_begin(0, len(selected_objects))
        for idx, obj in enumerate(selected_objects):
            if obj.type != 'MESH':
                self.report({'WARNING'}, f"Skipping {obj.name}, as it is not a mesh object.")
                wm.progress_update(idx + 1)
                continue

            original_active_object = context.view_layer.objects.active
            # Calculate the bounding box axis
            direction, extent = boundboxAxis(None, obj)

            # Calculate the rotation matrix to align X-axis to the direction vector
            rotation_matrix = direction.to_track_quat('X', 'Z').to_matrix().to_4x4()

            # Store the original matrix
            original_location = obj.matrix_world.to_translation()

            # Apply the rotation to the pivot point only
            obj.matrix_world = rotation_matrix @ obj.matrix_world

            # Reset geometry to original position
            obj.data.transform(rotation_matrix.inverted())

            obj.location = original_location
            wm.progress_update(idx + 1)
        wm.progress_end()
        return {'FINISHED'}

class OBJECT_OT_set_pivot_from_uv(bpy.types.Operator):
    bl_idname = "object.set_pivot_from_uv"
    bl_label = "Set Pivot from UV"
    bl_options = {'REGISTER', 'UNDO'}

    uv_x = bpy.props.FloatProperty(
        name="UV X",
        description="UV X coordinate (0-1)",
        default=0.5,
        min=-10.0,
        max=10.0
    )
    uv_y = bpy.props.FloatProperty(
        name="UV Y",
        description="UV Y coordinate (0-1)",
        default=0.5,
        min=-10.0,
        max=10.0
    )
    def execute(self, context):
        import time
        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'WARNING'}, "No objects selected!")
            return {'CANCELLED'}

        wm = context.window_manager
        wm.progress_begin(0, len(selected_objects))
        for idx, obj in enumerate(selected_objects):
            if obj.type != 'MESH':
                self.report({'WARNING'}, f"Skipping {obj.name}, as it is not a mesh object.")
                wm.progress_update(idx + 1)
                continue

            # Sprawdź, czy obiekt ma aktywną mapę UV
            if not obj.data.uv_layers.active:
                self.report({'WARNING'}, f"{obj.name} has no active UV map!")
                wm.progress_update(idx + 1)
                continue

            uv_layer = obj.data.uv_layers.active
            loops = obj.data.loops
            verts = obj.data.vertices

            # Szukamy pętli (loop) z UV najbliższym podanym wartościom uv_x i uv_y
            desired_uv = Vector((self.uv_x, self.uv_y))
            closest_vert_index = None
            closest_distance = float('inf')

            for poly in obj.data.polygons:
                for loop_index in poly.loop_indices:
                    uv_coords = uv_layer.data[loop_index].uv
                    dist = (uv_coords - desired_uv).length
                    if dist < closest_distance:
                        closest_distance = dist
                        closest_vert_index = loops[loop_index].vertex_index

            if closest_vert_index is None:
                self.report({'WARNING'}, f"No suitable UV coordinate found in {obj.name}")
                wm.progress_update(idx + 1)
                continue

            # Wyznaczamy pozycję wierzchołka w przestrzeni świata
            vert_local_pos = verts[closest_vert_index].co
            vert_world_pos = obj.matrix_world @ vert_local_pos

            # Ustawiamy pivot w tym punkcie
            bpy.context.scene.cursor.location = vert_world_pos

            # Musimy zresetować selekcję i ustawić obiekt jako aktywny,
            # aby "origin_set" zadziałało poprawnie tylko na bieżącym obiekcie.
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj

            bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='BOUNDS')
            wm.progress_update(idx + 1)
        wm.progress_end()
        return {'FINISHED'}

class OBJECT_OT_fix_pivot_rotation_from_uv(bpy.types.Operator):
    bl_idname = "object.fix_pivot_rotation_from_uv"
    bl_label = "Fix Pivot Rotation from UV"
    bl_options = {'REGISTER', 'UNDO'}

    uv_x = bpy.props.FloatProperty(
        name="UV X",
        description="UV X coordinate (0-1)",
        default=0.5,
        min=0.0,
        max=1.0
    )
    uv_y = bpy.props.FloatProperty(
        name="UV Y",
        description="UV Y coordinate (0-1)",
        default=0.5,
        min=0.0,
        max=1.0
    )
    def execute(self, context):
        import time
        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'WARNING'}, "No objects selected!")
            return {'CANCELLED'}

        wm = context.window_manager
        wm.progress_begin(0, len(selected_objects))
        for idx, obj in enumerate(selected_objects):
            if obj.type != 'MESH':
                self.report({'WARNING'}, f"Skipping {obj.name}, because it is not a mesh object.")
                wm.progress_update(idx + 1)
                continue

            # Sprawdź, czy obiekt ma aktywną mapę UV
            uv_layers = obj.data.uv_layers
            if not uv_layers.active:
                self.report({'WARNING'}, f"{obj.name} has no active UV map!")
                wm.progress_update(idx + 1)
                continue

            uv_layer = uv_layers.active
            loops = obj.data.loops
            verts = obj.data.vertices

            # Szukamy wierzchołka o UV najbliższym do (uv_x, uv_y)
            desired_uv = Vector((self.uv_x, self.uv_y))
            closest_vert_index = None
            closest_distance = float('inf')

            for poly in obj.data.polygons:
                for loop_index in poly.loop_indices:
                    uv_coords = uv_layer.data[loop_index].uv
                    dist = (uv_coords - desired_uv).length
                    if dist < closest_distance:
                        closest_distance = dist
                        closest_vert_index = loops[loop_index].vertex_index

            if closest_vert_index is None:
                self.report({'WARNING'}, f"No suitable UV coordinate found in {obj.name}!")
                wm.progress_update(idx + 1)
                continue

            # Pozycja wierzchołka w przestrzeni lokalnej i światowej
            vert_local_pos = verts[closest_vert_index].co
            vert_world_pos = obj.matrix_world @ vert_local_pos

            # Kierunek, w którym będziemy ustawiać oś X (od środka obiektu do tego wierzchołka)
            direction_local = vert_local_pos.normalized()
            # Jeśli wektor jest (0,0,0), nie można ustalić kierunku
            if direction_local.length == 0:
                self.report({'WARNING'}, f"Vertex in {obj.name} is at origin; cannot set rotation.")
                wm.progress_update(idx + 1)
                continue

            # Tworzymy macierz rotacji, wyrównując oś X do direction_local
            rotation_matrix = direction_local.to_track_quat('X', 'Z').to_matrix().to_4x4()

            # Zapisujemy oryginalną pozycję (lub całą macierz - w zależności od preferencji)
            original_location = obj.matrix_world.to_translation()

            # Obrót pivotu (macierz świata)
            obj.matrix_world = rotation_matrix @ obj.matrix_world

            # Reset geometrii, aby nie przemieściła się w przestrzeni
            obj.data.transform(rotation_matrix.inverted())

            # Przywracamy jedynie pozycję
            obj.location = original_location
            wm.progress_update(idx + 1)
        wm.progress_end()
        return {'FINISHED'}

class OBJECT_OT_fix_pivot_rotation_from_uv_xz(bpy.types.Operator):
    bl_idname = "object.fix_pivot_rotation_from_uv_xz"
    bl_label = "Fix Pivot Rotation from UV (X & Z)"
    bl_options = {'REGISTER', 'UNDO'}

    # Ustawiane przez użytkownika współrzędne UV (oś X)
    uv_x = bpy.props.FloatProperty(
        name="UV X",
        description="UV X coordinate (0-1) for X-axis direction",
        default=0.5,
        min=0.0,
        max=1.0
    )
    uv_y = bpy.props.FloatProperty(
        name="UV Y",
        description="UV Y coordinate (0-1) for X-axis direction",
        default=0.5,
        min=0.0,
        max=1.0
    )

    # Skrajne wartości UV.x, względem których wyznaczamy wierzchołki do ustawienia osi Z
    uv_x_min = bpy.props.FloatProperty(
        name="UV X Min",
        description="Lower extreme for UV X (default 0.0)",
        default=0.0,
        min=0.0,
        max=1.0
    )
    uv_x_max = bpy.props.FloatProperty(
        name="UV X Max",
        description="Upper extreme for UV X (default 1.0)",
        default=1.0,
        min=0.0,
        max=1.0
    )
    # Tolerancja, by znaleźć wierzchołki 'blisko' krawędzi min i max
    tolerance = bpy.props.FloatProperty(
        name="Tolerance",
        description="Threshold near UV X Min/Max for collecting extreme vertices",
        default=0.01,
        min=0.0,
        max=0.5
    )

    # Nowa właściwość - checkbox do odwrócenia osi Z
    reverse_z = bpy.props.BoolProperty(
        name="Reverse Z Axis",
        description="Flip Z-axis direction after it is computed",
        default=False
    )
    def execute(self, context):
        import time
        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'WARNING'}, "No objects selected!")
            return {'CANCELLED'}

        wm = context.window_manager
        wm.progress_begin(0, len(selected_objects))
        for idx, obj in enumerate(selected_objects):
            if obj.type != 'MESH':
                self.report({'WARNING'}, f"Skipping {obj.name}, not a mesh object.")
                wm.progress_update(idx + 1)
                continue

            # Sprawdź aktywną mapę UV
            if not obj.data.uv_layers.active:
                self.report({'WARNING'}, f"{obj.name} has no active UV map!")
                wm.progress_update(idx + 1)
                continue

            uv_layer = obj.data.uv_layers.active
            loops = obj.data.loops
            verts = obj.data.vertices

            # -----------------------------------------------------------
            # 1) Znajdź wierzchołek najbliższy (uv_x, uv_y) => kierunek osi X
            # -----------------------------------------------------------
            target_uv = Vector((self.uv_x, self.uv_y))
            closest_vert_index = None
            closest_dist = float('inf')

            # -----------------------------------------------------------
            # 2) Zbierz wierzchołki skrajne w UV.x => kierunek osi Z
            # -----------------------------------------------------------
            extreme_verts = []  # wierzchołki w strefach 'min' i 'max'
            min_edge = self.uv_x_min + self.tolerance
            max_edge = self.uv_x_max - self.tolerance

            for poly in obj.data.polygons:
                for loop_index in poly.loop_indices:
                    uv_coords = uv_layer.data[loop_index].uv
                    vertex_idx = loops[loop_index].vertex_index

                    # Szukanie wierzchołka (X-axis)
                    dist = (uv_coords - target_uv).length
                    if dist < closest_dist:
                        closest_dist = dist
                        closest_vert_index = vertex_idx

                    # Zbieranie wierzchołków skrajnych (Z-axis)
                    if uv_coords.x <= min_edge or uv_coords.x >= max_edge:
                        extreme_verts.append(vertex_idx)

            if closest_vert_index is None:
                self.report({'WARNING'}, f"No suitable UV coordinate for X-axis in {obj.name}.")
                wm.progress_update(idx + 1)
                continue
            if not extreme_verts:
                self.report({'WARNING'}, f"No extreme UV.x vertices found in {obj.name} (check tolerance?).")
                wm.progress_update(idx + 1)
                continue

            # -----------------------------------------------------------
            # 3) Obliczenie wektora dla osi X
            # -----------------------------------------------------------
            vert_local_pos_x = verts[closest_vert_index].co
            if vert_local_pos_x.length == 0:
                self.report({'WARNING'}, f"Vertex for X-axis in {obj.name} is at origin; cannot set rotation.")
                wm.progress_update(idx + 1)
                continue

            direction_local_x = vert_local_pos_x.normalized()

            # -----------------------------------------------------------
            # 4) Obliczenie wektora dla osi Z (średnia skrajnych wierzchołków)
            # -----------------------------------------------------------
            sum_extreme = Vector((0.0, 0.0, 0.0))
            for v_idx in extreme_verts:
                sum_extreme += verts[v_idx].co
            avg_extreme_local = sum_extreme / len(extreme_verts)

            if avg_extreme_local.length == 0:
                self.report({'WARNING'}, f"Extreme vertices in {obj.name} cannot define a valid Z-axis.")
                wm.progress_update(idx + 1)
                continue

            direction_local_z = avg_extreme_local.normalized()

            # -----------------------------------------------------------
            # 5) Ortonormalizacja (X, Y, Z)
            # -----------------------------------------------------------
            X_ = direction_local_x
            Z_ = direction_local_z

            # Początkowy Y = Z x X
            Y_ = Z_.cross(X_)
            if Y_.length == 0:
                self.report({'WARNING'}, f"X-axis and Z-axis are parallel for {obj.name}; cannot set full rotation.")
                wm.progress_update(idx + 1)
                continue
            Y_.normalize()

            # Z = X x Y
            Z_ = X_.cross(Y_)
            Z_.normalize()

            # X = Y x Z (ostatecznie, aby spójnie ortonormalizować)
            X_ = Y_.cross(Z_)
            X_.normalize()

            # -----------------------------------------------------------
            # 5a) Odwracanie osi Z (jeśli użytkownik wybrał taką opcję)
            # -----------------------------------------------------------
            if self.reverse_z:
                Z_ = -Z_
                # Po odwróceniu Z_ ponownie ortonormalizujemy układ
                Y_ = Z_.cross(X_)
                Y_.normalize()
                Z_ = X_.cross(Y_)
                Z_.normalize()
                X_ = Y_.cross(Z_)
                X_.normalize()

            # Budujemy macierz 3x3
            rot_mat_3x3 = mathutils.Matrix([
                [X_.x, Y_.x, Z_.x],
                [X_.y, Y_.y, Z_.y],
                [X_.z, Y_.z, Z_.z]
            ])
            rotation_matrix = rot_mat_3x3.to_4x4()

            # -----------------------------------------------------------
            # 6) Nałożenie rotacji pivotu, zachowanie pozycji obiektu
            # -----------------------------------------------------------
            original_location = obj.matrix_world.to_translation()

            # Obracamy pivot
            obj.matrix_world = rotation_matrix @ obj.matrix_world

            # Reset geometrii (odwrotna macierz)
            obj.data.transform(rotation_matrix.inverted())

            # Przywracamy wyłącznie pozycję
            obj.location = original_location
            wm.progress_update(idx + 1)
        wm.progress_end()
        return {'FINISHED'}

class OBJECT_OT_get_by_names(bpy.types.Operator):
    bl_idname = "object.get_by_names"
    bl_label = "Get by names"
    bl_options = {'REGISTER', 'UNDO'}

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
        row = layout.row(align=True)
        row.operator("object.set_pivot_to_mesh_manually", text="Set Pivot to Mesh (🡓) (manually)")
        row.operator("object.set_pivot_to_mesh_manually_up", text="Set Pivot To Mesh (🡑) (manually)")
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
    bpy.utils.register_class(OBJECT_OT_set_pivot_to_mesh_manually_up)
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
    bpy.utils.unregister_class(OBJECT_OT_set_pivot_to_mesh_manually_up)
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
    bpy.utils.unregister_class(OBJECT_OT_set_pivot_to_mesh_manually_up)
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
