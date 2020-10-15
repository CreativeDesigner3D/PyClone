import bpy
import math
from ..pc_lib import pc_types, pc_utils
from .. import pyclone_utils

def draw_assembly_properties(context, layout, assembly):
    unit_system = context.scene.unit_settings.system
    scene_props = pyclone_utils.get_scene_props(context.scene)

    col = layout.column(align=True)
    box = col.box()
    row = box.row()
    row.label(text="Assembly Name: " + assembly.obj_bp.name)
    row.operator('pc_assembly.select_parent',text="",icon='SORT_DESC')

    row = box.row(align=True)
    row.prop(scene_props,'assembly_tabs',expand=True)
    box = col.box()
    if scene_props.assembly_tabs == 'MAIN':
        box.prop(assembly.obj_bp,'name')

        col = box.column(align=True)
        col.label(text="Dimensions:")

        row1 = col.row(align=True)
        row1.prop(assembly.obj_x,'lock_location',index=0,text="")
        if assembly.obj_x.lock_location[0]:
            x = math.fabs(assembly.obj_x.location.x)
            value = str(bpy.utils.units.to_string(unit_system,'LENGTH',x))                 
            row1.label(text='X: ' + value)
        else:
            row1.prop(assembly.obj_x,'location',index=0,text="X")
            row1.prop(assembly.obj_x,'hide_viewport',text="")

        row1 = col.row(align=True)
        row1.prop(assembly.obj_y,'lock_location',index=1,text="")  
        if assembly.obj_y.lock_location[1]:
            y = math.fabs(assembly.obj_y.location.y)
            value = str(bpy.utils.units.to_string(unit_system,'LENGTH',y))                 
            row1.label(text='Y: ' + value)
        else:
            row1.prop(assembly.obj_y,'location',index=1,text="Y")
            row1.prop(assembly.obj_y,'hide_viewport',text="")

        row1 = col.row(align=True)
        row1.prop(assembly.obj_z,'lock_location',index=2,text="")              
        if assembly.obj_z.lock_location[2]:
            z = math.fabs(assembly.obj_z.location.z)
            value = str(bpy.utils.units.to_string(unit_system,'LENGTH',z))                 
            row1.label(text='Z: ' + value)
        else:
            row1.prop(assembly.obj_z,'location',index=2,text="Z")      
            row1.prop(assembly.obj_z,'hide_viewport',text="")                  

        col = box.column()
        s_col = col.split()
        s_col.prop(assembly.obj_bp,'location')
        s_col.prop(assembly.obj_bp,'rotation_euler',text="Rotation")

    if scene_props.assembly_tabs == 'PROMPTS':
        assembly.obj_prompts.pyclone.draw_prompts(box)

    if scene_props.assembly_tabs == 'OBJECTS':

        skip_names = {assembly.obj_bp.name,assembly.obj_x.name,assembly.obj_y.name,assembly.obj_z.name,assembly.obj_prompts.name}

        row = box.row()
        row.label(text="Objects",icon='OUTLINER_OB_MESH')
        row.operator('pc_assembly.add_object',text="Add Object",icon='ADD')

        mesh_col = box.column(align=True)

        for child in assembly.obj_bp.children:
            if child.name not in skip_names:
                row = mesh_col.row(align=True)
                if child == context.object:
                    row.label(text="",icon='RADIOBUT_ON')
                elif child in context.selected_objects:
                    row.label(text="",icon='DECORATE')
                else:
                    row.label(text="",icon='RADIOBUT_OFF')
                row.operator('pc_object.select_object',text=child.name,icon=pc_utils.get_object_icon(child)).obj_name = child.name

    if scene_props.assembly_tabs == 'LOGIC':
        
        box.prop(scene_props,'driver_tabs',text='')
        if scene_props.driver_tabs == 'LOC_X':
            box.prop(assembly.obj_bp,'location',index=0,text="Location X")
            drivers = pyclone_utils.get_drivers(assembly.obj_bp)
            for driver in drivers:
                if driver.data_path == 'location' and driver.array_index == 0:
                    pyclone_utils.draw_driver(layout,assembly.obj_bp,driver)    

        if scene_props.driver_tabs == 'LOC_Y':
            box.prop(assembly.obj_bp,'location',index=1,text="Location Y")
            drivers = pyclone_utils.get_drivers(assembly.obj_bp)
            for driver in drivers:
                if driver.data_path == 'location' and driver.array_index == 1:
                    pyclone_utils.draw_driver(layout,assembly.obj_bp,driver)  

        if scene_props.driver_tabs == 'LOC_Z':
            box.prop(assembly.obj_bp,'location',index=2,text="Location Z")
            drivers = pyclone_utils.get_drivers(assembly.obj_bp)
            for driver in drivers:
                if driver.data_path == 'location' and driver.array_index == 2:
                    pyclone_utils.draw_driver(layout,assembly.obj_bp,driver)  

        if scene_props.driver_tabs == 'ROT_X':
            box.prop(assembly.obj_bp,'rotation_euler',index=0,text="Rotation X")
            drivers = pyclone_utils.get_drivers(assembly.obj_bp)
            for driver in drivers:
                if driver.data_path == 'rotation_euler' and driver.array_index == 0:
                    pyclone_utils.draw_driver(layout,assembly.obj_bp,driver)  

        if scene_props.driver_tabs == 'ROT_Y':
            box.prop(assembly.obj_bp,'rotation_euler',index=1,text="Rotation Y")
            drivers = pyclone_utils.get_drivers(assembly.obj_bp)
            for driver in drivers:
                if driver.data_path == 'rotation_euler' and driver.array_index == 1:
                    pyclone_utils.draw_driver(layout,assembly.obj_bp,driver)  

        if scene_props.driver_tabs == 'ROT_Z':
            box.prop(assembly.obj_bp,'rotation_euler',index=2,text="Rotation Z")
            drivers = pyclone_utils.get_drivers(assembly.obj_bp)
            for driver in drivers:
                if driver.data_path == 'rotation_euler' and driver.array_index == 2:
                    pyclone_utils.draw_driver(layout,assembly.obj_bp,driver)  

        if scene_props.driver_tabs == 'DIM_X':
            box.prop(assembly.obj_x,'location',index=0,text="Dimension X")
            drivers = pyclone_utils.get_drivers(assembly.obj_x)
            for driver in drivers:
                if driver.data_path == 'location' and driver.array_index == 0:
                    pyclone_utils.draw_driver(layout,assembly.obj_x,driver)  

        if scene_props.driver_tabs == 'DIM_Y':
            box.prop(assembly.obj_y,'location',index=1,text="Dimension Y")
            drivers = pyclone_utils.get_drivers(assembly.obj_y)
            for driver in drivers:
                if driver.data_path == 'location' and driver.array_index == 1:
                    pyclone_utils.draw_driver(layout,assembly.obj_y,driver)  

        if scene_props.driver_tabs == 'DIM_Z':
            box.prop(assembly.obj_z,'location',index=2,text="Dimension Z")
            drivers = pyclone_utils.get_drivers(assembly.obj_z)
            for driver in drivers:
                if driver.data_path == 'location' and driver.array_index == 2:
                    pyclone_utils.draw_driver(layout,assembly.obj_z,driver)  

        if scene_props.driver_tabs == 'PROMPTS':
            if len(assembly.obj_prompts.pyclone.prompts) == 0:
                box.label('No Prompts')  
                return    

            box.template_list("PC_UL_prompts"," ", assembly.obj_prompts.pyclone, "prompts", assembly.obj_prompts.pyclone, "prompt_index",rows=5,type='DEFAULT')
            if assembly.obj_prompts.pyclone.prompt_index + 1 > len(assembly.obj_prompts.pyclone.prompts):
                return 

            prompt = assembly.obj_prompts.pyclone.prompts[assembly.obj_prompts.pyclone.prompt_index]

            if prompt:
                drivers = pyclone_utils.get_drivers(assembly.obj_prompts)
                if len(drivers) == 0:
                    box.operator('pc_driver.add_driver')
                else:
                    box.operator('pc_driver.remove_driver')
                for driver in drivers:
                    if driver.data_path == prompt.get_data_path():
                        pyclone_utils.draw_driver(box,assembly.obj_prompts,driver)  

        if scene_props.driver_tabs == 'CALCULATORS':
            if len(assembly.obj_prompts.pyclone.calculators) == 0:
                box.label('No Calculators')  
                return

            box.template_list("PC_UL_calculators"," ", assembly.obj_prompts.pyclone, "calculators", assembly.obj_prompts.pyclone, "calculator_index",rows=5,type='DEFAULT')
            if assembly.obj_prompts.pyclone.calculator_index + 1 > len(assembly.obj_prompts.pyclone.calculators):
                return 
            
            calculator = assembly.obj_prompts.pyclone.calculators[assembly.obj_prompts.pyclone.calculator_index]

            if calculator:
                drivers = pyclone_utils.get_drivers(calculator.distance_obj)
                if len(drivers) == 0:
                    box.operator('pc_driver.add_calculator_driver')
                else:
                    box.operator('pc_driver.remove_calculator_driver')                
                for driver in drivers:
                    pyclone_utils.draw_driver(layout,calculator.distance_obj,driver) 

        if scene_props.driver_tabs == 'SELECTED_OBJECT':
            obj = context.object
            if obj:
                box.label(text="Current Object: " + context.object.name,icon=pc_utils.get_object_icon(obj))
                drivers = pyclone_utils.get_drivers(obj)
                for driver in drivers:
                    pyclone_utils.draw_driver(layout,obj,driver)
                    


class VIEW3D_PT_pc_assembly_properties(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Assembly"
    bl_category = "Assembly"    
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        if context.object and pc_utils.get_assembly_bp(context.object):
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        assembly_bp = pc_utils.get_assembly_bp(context.object)
        assembly = pc_types.Assembly(assembly_bp)   
        draw_assembly_properties(context,layout,assembly)     

classes = (
    VIEW3D_PT_pc_assembly_properties,
)

register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
    register()                