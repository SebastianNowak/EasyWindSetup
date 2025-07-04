import bpy
from . import addon_updater_ops

@addon_updater_ops.make_annotations
class EasyWindSetupPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    # Addon updater preferences.

    auto_check_update = bpy.props.BoolProperty(
		name="Auto-check for Update",
		description="If enabled, auto-check for updates using an interval",
		default=True)

    updater_interval_months = bpy.props.IntProperty(
		name='Months',
		description="Number of months between checking for updates",
		default=0,
		min=0)

    updater_interval_days = bpy.props.IntProperty(
		name='Days',
		description="Number of days between checking for updates",
		default=0,
		min=0,
		max=31)

    updater_interval_hours = bpy.props.IntProperty(
		name='Hours',
		description="Number of hours between checking for updates",
		default=0,
		min=0,
		max=23)

    updater_interval_minutes = bpy.props.IntProperty(
		name='Minutes',
		description="Number of minutes between checking for updates",
		default=1,
		min=0,
		max=59)

    def draw(self, context):
        layout = self.layout
        mainrow = layout.row()
        col = mainrow.column()

        addon_updater_ops.update_settings_ui_condensed(self, context, col)

def register():
    addon_updater_ops.make_annotations(EasyWindSetupPreferences)
    bpy.utils.register_class(EasyWindSetupPreferences)

def unregister():
    bpy.utils.unregister_class(EasyWindSetupPreferences)
