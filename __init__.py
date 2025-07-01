# EasyWindSetup - Blender Add-on
# Contributor(s): Sebastian Nowak (sebastian.nowak@thefarm51.com), Angelika Hryciuk-Nowak (angelika.hryciuk@thefarm51.com)
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

bl_info = {
        "name": "Easy Wind Setup",
        "description": "Add-on to provide tools for easy wind setup.",
        "author": "Sebastian Nowak, Angelika Hryciuk-Nowak, Marek Derkowski",
        "version": (1, 1, 2),
        "blender": (2, 80, 0),
        "location": "View 3D > Tool Shelf > Easy Wind Setup",
        "warning": "", # used for warning icon and text in add-ons panel
        #"wiki_url": "http://my.wiki.url",
        "tracker_url": "https://github.com/SebastianNowak/EasyWindSetup",
        #"support": "COMMUNITY",
        "category": "Object"
        }

import bpy
from . import addon_updater_ops

def register():
    addon_updater_ops.register(bl_info)

    from . import preferences
    from . import properties
    from . import ui
    preferences.register()
    properties.register()
    ui.register()

def unregister():
    addon_updater_ops.unregister()

    from . import preferences
    from . import properties
    from . import ui
    preferences.unregister()
    properties.unregister()
    ui.unregister()

if __package__ == '__main__':
    register()
