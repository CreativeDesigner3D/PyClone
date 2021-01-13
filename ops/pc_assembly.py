import bpy
from bpy.types import (
        Operator,
        Panel,
        UIList,
        PropertyGroup,
        AddonPreferences,
        )
from bpy.props import (
        StringProperty,
        BoolProperty,
        IntProperty,
        CollectionProperty,
        BoolVectorProperty,
        PointerProperty,
        FloatProperty,
        )
import os, math
from ..pc_lib import pc_types, pc_utils

class pc_assembly_OT_create_new_assembly(Operator):
    bl_idname = "pc_assembly.create_new_assembly"
    bl_label = "Create New Assembly"
    bl_description = "This will create a new assembly"
    bl_options = {'UNDO'}

    assembly_name: StringProperty(name="Assembly Name",default="New Assembly")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        assembly = pc_types.Assembly()
        assembly.create_assembly(self.assembly_name)
        assembly.obj_x.location.x = 1
        assembly.obj_y.location.y = 1
        assembly.obj_z.location.z = 1
        assembly.obj_bp.select_set(True)
        assembly.obj_bp["PROMPT_ID"] = "pc_assembly.show_properties"
        context.view_layer.objects.active = assembly.obj_bp
        return {'FINISHED'}

    def invoke(self,context,event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Enter the name of the assembly to add.")
        layout.prop(self,'assembly_name')


class pc_assembly_OT_delete_assembly(Operator):
    bl_idname = "pc_assembly.delete_assembly"
    bl_label = "Delete Assembly"
    bl_description = "This will delete the assembly"
    bl_options = {'UNDO'}

    obj_bp_name: StringProperty(name="Base Point Name")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        if self.obj_bp_name in bpy.data.objects:
            obj_bp = bpy.data.objects[self.obj_bp_name]
            pc_utils.delete_object_and_children(obj_bp)
        return {'FINISHED'}

    def invoke(self,context,event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Are you sure you want to delete the assembly?")
        layout.label(text=self.obj_bp_name)


class pc_assembly_OT_select_base_point(Operator):
    bl_idname = "pc_assembly.select_base_point"
    bl_label = "Select Assembly Base Point"
    bl_description = "This will select the assembly base point"
    bl_options = {'UNDO'}

    obj_bp_name: StringProperty(name="Base Point Name")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')
        if self.obj_bp_name in bpy.data.objects:
            obj_bp = bpy.data.objects[self.obj_bp_name]
            obj_bp.hide_viewport = False
            obj_bp.select_set(True)
        return {'FINISHED'}


class pc_assembly_OT_duplicate_assembly(Operator):
    bl_idname = "pc_assembly.duplicate_assembly"
    bl_label = "Duplicate Assembly"
    bl_description = "This will duplicate the assembly"
    bl_options = {'UNDO'}

    obj_bp_name: StringProperty(name="Base Point Name")

    @classmethod
    def poll(cls, context):
        return True

    def select_obj_and_children(self,obj):
        obj.hide_viewport = False
        obj.select_set(True)
        for child in obj.children:
            obj.hide_viewport = False
            child.select_set(True)
            self.select_obj_and_children(child)

    def hide_empties_and_boolean_meshes(self,obj):
        if obj.type == 'EMPTY' or obj.hide_render:
            obj.hide_viewport = True
        for child in obj.children:
            self.hide_empties_and_boolean_meshes(child)

    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')
        if self.obj_bp_name in bpy.data.objects:
            obj_bp = bpy.data.objects[self.obj_bp_name]

            bpy.ops.object.select_all(action='DESELECT')
            self.select_obj_and_children(obj_bp)
            bpy.ops.object.duplicate_move()
            self.hide_empties_and_boolean_meshes(obj_bp)   

            obj = context.object
            obj_bp = pc_utils.get_assembly_bp(obj)
            self.hide_empties_and_boolean_meshes(obj_bp)   
            obj_bp.hide_viewport = False
            obj_bp.select_set(True)

        return {'FINISHED'}


class pc_assembly_OT_add_object(Operator):
    bl_idname = "pc_assembly.add_object"
    bl_label = "Add Object to Assembly"
    bl_description = "This will add a new object to the assembly"
    bl_options = {'UNDO'}

    assembly_name: StringProperty(name="Assembly Name",default="New Assembly")

    object_name: StringProperty(name="Object Name",default="New Object")
    object_type: bpy.props.EnumProperty(name="Object Type",
                                        items=[('MESH',"Mesh","Add an Mesh Object"),
                                               ('EMPTY',"Empty","Add an Empty Object"),
                                               ('CURVE',"Curve","Add an Curve Object"),
                                               ('LIGHT',"Light","Add an Light Object")],
                                        default='MESH')
    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        obj_bp = pc_utils.get_assembly_bp(context.object)
        assembly = pc_types.Assembly(obj_bp)
        if self.object_type == 'EMPTY':
            assembly.add_empty(self.object_name)

        if self.object_type == 'MESH':
            obj_mesh = pc_utils.create_cube_mesh(self.object_name,(assembly.obj_x.location.x,
                                                                   assembly.obj_y.location.y,
                                                                   assembly.obj_z.location.z))

            if 'PROMPT_ID' in assembly.obj_bp:
                obj_mesh['PROMPT_ID'] = assembly.obj_bp['PROMPT_ID']
            
            assembly.add_object(obj_mesh)

            # MAKE NORMALS CONSISTENT
            context.view_layer.objects.active = obj_mesh
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.normals_make_consistent(inside=False)
            bpy.ops.object.editmode_toggle()

        if self.object_type == 'CURVE':
            curve = bpy.data.curves.new(self.object_name,'CURVE')
            obj_curve = bpy.data.objects.new(self.object_name,curve)
            spline = obj_curve.data.splines.new('BEZIER')
            spline.bezier_points.add(count=1)                 
            obj_curve.data.splines[0].bezier_points[0].co = (0,0,0)
            obj_curve.data.splines[0].bezier_points[1].co = (assembly.obj_x.location.x,0,0)
            assembly.add_object(obj_curve)
        if self.object_type == 'LIGHT':
            assembly.add_light(self.object_name,'POINT')
        return {'FINISHED'}

    def invoke(self,context,event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        layout.prop(self,'object_type',expand=True)
        layout.prop(self,'object_name')

class pc_assembly_OT_connect_mesh_to_hooks_in_assembly(Operator):
    bl_idname = "pc_assembly.connect_meshes_to_hooks_in_assembly"
    bl_label = "Connect Mesh to Hooks In Assembly"
    bl_description = "This connects all mesh hooks to a mesh"
    bl_options = {'UNDO'}
    
    obj_name: StringProperty(name="Object Name")
    
    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        obj = bpy.data.objects[self.obj_name]
        obj_bp = pc_utils.get_assembly_bp(obj)
        if obj_bp:
            hooklist = []

            for child in obj_bp.children:
                if child.type == 'EMPTY' and 'obj_prompts' not in child:
                    hooklist.append(child)

            if obj.mode == 'EDIT':
                bpy.ops.object.editmode_toggle()
            
            pc_utils.apply_hook_modifiers(context,obj)
            for vgroup in obj.vertex_groups:
                for hook in hooklist:
                    if hook.name == vgroup.name:
                        pc_utils.hook_vertex_group_to_object(obj,vgroup.name,hook)

            obj.lock_location = (True,True,True)
                
        return {'FINISHED'}

class pc_assembly_OT_create_assembly_script(Operator):
    bl_idname = "pc_assembly.create_assembly_script"
    bl_label = "Create Assembly Script"
    bl_description = "This will create a script of the selected assembly. This is in development."
    bl_options = {'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        obj = context.object
        coll = pc_utils.get_assembly_collection(obj)
        assembly = pc_types.Assembly(coll)

        #Create New Script
        text = bpy.data.texts.new(coll.name)

        #Add Imports
        text.write('import bpy\n')
        #Figure out how to import bp_types
                
        #Add Class Def
        text.write('class ' + coll.name + '(bp_types.Assembly):\n')
        text.write('    def draw(self):\n')
        text.write('    self.create_assembly()\n')

        #Add Prompts
        for prompt in assembly.obj_prompts.prompt_page.prompts:
            pass

        #Add Empty Objects Except Built-in Assembly Objects
        #for obj in assembly.empty_objs:
        for obj in assembly.obj_bp.children:
            if obj.type == 'EMPTY':
                pass #Assign Drivers and Constraints

        #Add Mesh Objects This needs to be done after empties for hooks
        #for obj in assembly.mesh_objs:
        for obj in assembly.obj_bp.children:
            pass
        return {'FINISHED'}


class pc_assembly_OT_select_parent_assembly(bpy.types.Operator):
    bl_idname = "pc_assembly.select_parent"
    bl_label = "Select Parent Assembly"
    bl_description = "This selects the parent assembly"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        obj_bp = pc_utils.get_assembly_bp(context.object)
        if obj_bp and obj_bp.parent:    
            return True
        else:
            return False

    def select_children(self,obj):
        obj.select_set(True)
        for child in obj.children:
            child.select_set(True)
            self.select_children(child)

    def execute(self, context):
        obj_bp = pc_utils.get_assembly_bp(context.object)
        assembly = pc_types.Assembly(obj_bp)

        if assembly:
            if assembly.obj_bp.parent:
                assembly.obj_bp.parent.select_set(True)
                context.view_layer.objects.active = assembly.obj_bp.parent

                self.select_children(assembly.obj_bp.parent)

        return {'FINISHED'}


class pc_assembly_OT_create_assembly_view(Operator):
    bl_idname = "pc_assembly.create_assembly_view"
    bl_label = "Create Assembly View"
    bl_description = "This will create a new scene and link the assembly to that scene"
    bl_options = {'UNDO'}

    obj_bp_name: StringProperty(name="Base Point Name")
    
    view_name: StringProperty(name="View Name")

    include_front_view: BoolProperty(name="Include Front View")
    include_top_view: BoolProperty(name="Include Top View")
    include_size_view: BoolProperty(name="Include Size View")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')

        if self.obj_bp_name in bpy.data.objects:
            obj_bp = bpy.data.objects[self.obj_bp_name]

            #CREATE COLLECTION FROM ASSEMBLY
            pc_utils.select_object_and_children(obj_bp)
            bpy.ops.collection.create(name=self.view_name)

            #CREATE NEW SCENE
            world = context.scene.world
            bpy.ops.scene.new(type='EMPTY')
            context.scene.name = self.view_name
            context.scene.world = world
            #TODO: Assign scene.is_view_scene to load UI for Settings

            #INSTANCE ASSEMBLY COLLECTION
            bpy.ops.object.collection_instance_add(collection=self.view_name)

            #TODO: Create all selected Views
            #TODO: Create dimensions

            #CREATE CAMERA
            cam = bpy.data.cameras.new('Camera ' + self.view_name)
            cam.type = 'ORTHO'
            cam_obj = bpy.data.objects.new('Camera ' + self.view_name,cam)
            cam_obj.location.x = 0
            cam_obj.location.y = -5
            cam_obj.location.z = 0
            cam_obj.rotation_euler.x = math.radians(90)
            cam_obj.rotation_euler.y = 0
            cam_obj.rotation_euler.z = 0
            context.view_layer.active_layer_collection.collection.objects.link(cam_obj)   
            context.scene.camera = cam_obj

            #CHANGE RENDERING SETTINGS FOR FREE STYLE
        
        return {'FINISHED'}

    def invoke(self,context,event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        layout.prop(self,'view_name')
        box = layout.box()
        box.label(text="What views of the assembly do you want to include?")
        row = box.row()
        row.prop(self,'include_front_view',text="Front")
        row.prop(self,'include_front_view',text="Top")
        row.prop(self,'include_front_view',text="Side")
        

classes = (
    pc_assembly_OT_create_new_assembly,
    pc_assembly_OT_delete_assembly,
    pc_assembly_OT_select_base_point,
    pc_assembly_OT_duplicate_assembly,
    pc_assembly_OT_add_object,
    pc_assembly_OT_connect_mesh_to_hooks_in_assembly,
    pc_assembly_OT_create_assembly_script,
    pc_assembly_OT_select_parent_assembly,
    pc_assembly_OT_create_assembly_view
)

register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
    register()