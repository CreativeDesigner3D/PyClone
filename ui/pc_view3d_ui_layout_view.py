import bpy
from bpy.types import (
        Operator,
        Panel,
        PropertyGroup,
        UIList,
        )
from bpy.props import (
        BoolProperty,
        FloatProperty,
        IntProperty,
        PointerProperty,
        StringProperty,
        CollectionProperty,
        )

from .. import pyclone_utils
from ..pc_lib import pc_utils, pc_types

class VIEW3D_PT_pc_layout_view(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Layout View"
    bl_label = "Layout View"
    bl_options = {'HIDE_HEADER'}
    
    @classmethod
    def poll(cls, context):
        for scene in bpy.data.scenes:
            props = pyclone_utils.get_scene_props(scene)
            if props.is_view_scene:
                return True
        return False

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="",icon='SCENE')

    def draw_camera_settings(self,context,layout):
        scene = context.scene
        rd = scene.render

        scene_props = pyclone_utils.get_scene_props(scene)
        box = layout.box()
        row = box.row(align=True)
        row.scale_y = 1.3
        row.operator('render.render',text="Go Back to Model",icon='BACK').use_viewport=True
        row.operator('render.render',text="Render",icon='SCENE').use_viewport=True

        if scene_props.is_view_scene:
            box = layout.box()
            box.label(text="Page Setup",icon='FILE')
            row = box.row()
            row.label(text="Page Size")
            row.prop(scene_props,'page_size',text="")
            row = box.row()
            # row.label(text="Fit to Paper")            
            row.prop(scene_props,'fit_to_paper',text="Fit to Paper")
            if not scene_props.fit_to_paper:
                row.prop(scene_props,'page_scale',text="")
            row = box.row()
            row.label(text="Print Style")                   
            row.prop(scene_props,'page_style',text="")

            #CREATE VIEW OF ASSEMBLY    
            box = layout.box()
            box.label(text="Create View",icon='SEQ_PREVIEW')    
            row = box.row()        
            row.operator('pc_assembly.create_assembly_dimension',text="Top",icon='AXIS_TOP')
            row.operator('pc_assembly.create_assembly_dimension',text="Front",icon='FACESEL')
            row.operator('pc_assembly.create_assembly_dimension',text="Side",icon='AXIS_SIDE')

            #ADD DIMENSION ADD ANNOTATION
            box = layout.box()
            box.label(text="Dimensions and Annotations",icon='DRIVER_DISTANCE')               
            box.operator('pc_assembly.create_assembly_dimension',text="Add Dimension",icon='TRACKING_FORWARDS_SINGLE')
            box.operator('pc_assembly.create_assembly_dimension',text="Add Annotation",icon='CON_ROTLIMIT')
            box.operator('pc_assembly.add_title_block',text="Add Title Block",icon='MENU_PANEL')

            #ADD TITLE BLOCK

        else:
            box = layout.box()
            box.label(text="Dimensions and Annotations",icon='DRIVER_DISTANCE')               
            box.operator('pc_assembly.create_assembly_dimension',text="Add Dimension",icon='TRACKING_FORWARDS_SINGLE')
            box.operator('pc_assembly.create_assembly_dimension',text="Add Annotation",icon='CON_ROTLIMIT')
            box.operator('pc_assembly.add_title_block',text="Add Title Block",icon='MENU_PANEL')
            # box.prop(cam_obj.data,'ortho_scale',text="View Scale")
            
            # col = box.column(align=True)
            # row = col.row(align=True)
            # row.label(text="Resolution:")
            # row.prop(rd, "resolution_x", text="X")
            # row.prop(rd, "resolution_y", text="Y")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        rd = scene.render

        scene_props = pyclone_utils.get_scene_props(scene)
        obj = context.object
        obj_props = pyclone_utils.get_scene_props(obj)

        self.draw_camera_settings(context,layout)

        if obj_props.is_view_object:
            # layout.prop(obj,'name')

            if obj.type == 'CAMERA':
                pass

            if obj.type == 'EMPTY':
                pass


classes = (
    VIEW3D_PT_pc_layout_view,
)

register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
    register()        