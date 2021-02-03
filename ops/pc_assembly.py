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
from .. import pyclone_utils
from ..pc_lib import pc_types, pc_utils, pc_unit

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


class pc_assembly_OT_create_assembly_layout(Operator):
    bl_idname = "pc_assembly.create_assembly_layout"
    bl_label = "Create Assembly Layout"
    bl_description = "This will create a new scene and link the assembly to that scene"
    bl_options = {'UNDO'}

    obj_bp_name: StringProperty(name="Base Point Name")
    
    view_name: StringProperty(name="View Name",default="New Layout View")

    include_front_view: BoolProperty(name="Include Front View",default=True)
    include_top_view: BoolProperty(name="Include Top View")
    include_side_view: BoolProperty(name="Include Side View")

    VISIBLE_LINESET_NAME = "Visible Lines"
    HIDDEN_LINESET_NAME = "Hidden Lines"
    HIDDEN_LINE_DASH_PX = 10
    HIDDEN_LINE_GAP_PX = 10

    @classmethod
    def poll(cls, context):
        return True

    def create_linestyles(self):
        linestyles = bpy.data.linestyles
        linestyles.new(self.VISIBLE_LINESET_NAME)
        
        hidden_linestyle = linestyles.new(self.HIDDEN_LINESET_NAME)
        hidden_linestyle.use_dashed_line = True
        hidden_linestyle.dash1 = self.HIDDEN_LINE_DASH_PX
        hidden_linestyle.dash2 = self.HIDDEN_LINE_DASH_PX
        hidden_linestyle.dash3 = self.HIDDEN_LINE_DASH_PX
        hidden_linestyle.gap1 = self.HIDDEN_LINE_GAP_PX
        hidden_linestyle.gap2 = self.HIDDEN_LINE_GAP_PX
        hidden_linestyle.gap3 = self.HIDDEN_LINE_GAP_PX

    def create_linesets(self, scene):
        temp_dim = pc_types.Dimension()
        f_settings = scene.view_layers[0].freestyle_settings
        linestyles = bpy.data.linestyles
        
        visible_lineset = f_settings.linesets.new(self.VISIBLE_LINESET_NAME)
        visible_lineset.linestyle = linestyles[self.VISIBLE_LINESET_NAME]
        visible_lineset.select_by_collection = True
        visible_lineset.collection_negation = 'EXCLUSIVE'
        visible_lineset.collection = temp_dim.get_dimension_collection()

        hidden_lineset = f_settings.linesets.new(self.HIDDEN_LINESET_NAME)
        hidden_lineset.linestyle = linestyles[self.HIDDEN_LINESET_NAME]
        
        hidden_lineset.select_by_visibility = True
        hidden_lineset.visibility = 'HIDDEN'
        hidden_lineset.select_by_edge_types = True
        hidden_lineset.select_by_face_marks = False
        hidden_lineset.select_by_collection = True
        hidden_lineset.select_by_image_border = False
        
        hidden_lineset.select_silhouette = True
        hidden_lineset.select_border = False
        hidden_lineset.select_contour = False
        hidden_lineset.select_suggestive_contour = False
        hidden_lineset.select_ridge_valley = False
        hidden_lineset.select_crease = False
        hidden_lineset.select_edge_mark = True
        hidden_lineset.select_external_contour = False
        hidden_lineset.select_material_boundary = False
        hidden_lineset.collection_negation = 'EXCLUSIVE'
        hidden_lineset.collection = temp_dim.get_dimension_collection()

    def clear_unused_linestyles(self):
        for linestyle in bpy.data.linestyles:
            if linestyle.users == 0:
                bpy.data.linestyles.remove(linestyle)

    def create_view_scene(self,context):
        world = context.scene.world
        bpy.ops.scene.new(type='EMPTY')
        new_scene = context.scene
        props = pyclone_utils.get_scene_props(new_scene)
        props.is_view_scene = True
        new_scene.name = self.view_name
        new_scene.world = world
        new_scene.render.use_freestyle = True
        view_settings = new_scene.view_settings
        view_settings.view_transform = 'Standard'
        view_settings.look = 'High Contrast'
        view_settings.exposure = 4

        self.create_linesets(context.scene)

    def execute(self, context):
        self.create_linestyles()

        bpy.ops.object.select_all(action='DESELECT')

        if self.obj_bp_name in bpy.data.objects:
            obj_bp = bpy.data.objects[self.obj_bp_name]

            assembly = pc_types.Assembly(obj_bp)
            a_width = math.fabs(assembly.obj_x.location.x)
            a_depth = math.fabs(assembly.obj_y.location.y)
            a_height = math.fabs(assembly.obj_z.location.z)
            view_gap = .5

            #CREATE COLLECTION FROM ASSEMBLY
            pc_utils.select_object_and_children(obj_bp)
            bpy.ops.collection.create(name=self.view_name)

            collection = bpy.data.collections[self.view_name]
            collection.pyclone.assembly_bp = obj_bp

            #CREATE NEW SCENE
            self.create_view_scene(context)

            #INSTANCE ASSEMBLY COLLECTION
            # bpy.ops.object.collection_instance_add(collection=self.view_name)

            # coll_obj = context.object
            # obj_props = pyclone_utils.get_object_props(coll_obj)
            # obj_props.is_view_object = True

            if self.include_front_view:
                front_obj = bpy.data.objects.new(self.view_name + ' - Front',None)
                front_obj.instance_type = 'COLLECTION'
                front_obj.instance_collection = collection
                front_obj.empty_display_size = .01
                # front_obj.show_instancer_for_viewport = False
                front_obj.location = (0,0,0)
                front_obj.rotation_euler = (0,0,0)
                context.view_layer.active_layer_collection.collection.objects.link(front_obj)   
                front_obj.select_set(True)
                obj_props = pyclone_utils.get_object_props(front_obj)
                obj_props.is_view_object = True

            if self.include_side_view:
                side_obj = bpy.data.objects.new(self.view_name + ' - Side',None)
                side_obj.instance_type = 'COLLECTION'
                side_obj.instance_collection = collection
                side_obj.empty_display_size = .01
                # side_obj.show_instancer_for_viewport = False
                side_obj.location = (a_width + a_depth + view_gap,0,0)
                side_obj.rotation_euler = (0,0,math.radians(-90))
                context.view_layer.active_layer_collection.collection.objects.link(side_obj) 
                side_obj.select_set(True)  
                obj_props = pyclone_utils.get_object_props(side_obj)
                obj_props.is_view_object = True

            if self.include_top_view:
                top_obj = bpy.data.objects.new(self.view_name + ' - Top',None)
                top_obj.instance_type = 'COLLECTION'
                top_obj.instance_collection = collection
                top_obj.empty_display_size = .01
                # top_obj.show_instancer_for_viewport = False
                top_obj.location = (0,0,a_height + a_depth + view_gap)
                top_obj.rotation_euler = (math.radians(90),0,0)
                context.view_layer.active_layer_collection.collection.objects.link(top_obj) 
                top_obj.select_set(True)  
                obj_props = pyclone_utils.get_object_props(top_obj)
                obj_props.is_view_object = True

            #TODO: Create dimensions
            #Append Data

            #CREATE CAMERA
            cam = bpy.data.cameras.new('Camera ' + self.view_name)
            cam.type = 'ORTHO'
            cam_obj = bpy.data.objects.new('Camera ' + self.view_name,cam)
            obj_props = pyclone_utils.get_object_props(cam_obj)
            obj_props.is_view_object = True
            cam_obj.location.x = 0
            cam_obj.location.y = -5
            cam_obj.location.z = 0
            cam_obj.rotation_euler.x = math.radians(90)
            cam_obj.rotation_euler.y = 0
            cam_obj.rotation_euler.z = 0
            context.view_layer.active_layer_collection.collection.objects.link(cam_obj)   
            context.scene.camera = cam_obj

            bpy.ops.view3d.camera_to_view_selected()
            bpy.ops.view3d.view_camera()
            bpy.ops.view3d.view_center_camera()

            self.clear_unused_linestyles()

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
        row.prop(self,'include_top_view',text="Top")
        row.prop(self,'include_side_view',text="Side")
        

class pc_assembly_OT_create_assembly_dimension(bpy.types.Operator):
    bl_idname = "pc_assembly.create_assembly_dimension"
    bl_label = "Create Assembly Dimension"
    bl_description = "This creates an assembly dimension"
    bl_options = {'UNDO'}

    add_x_dimension: BoolProperty(name="Add X Dimension")
    add_y_dimension: BoolProperty(name="Add Y Dimension")
    add_z_dimension: BoolProperty(name="Add Z Dimension")

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self,context,event):
        dim_bp = pc_utils.get_assembly_bp(context.object)
        self.dimension = pc_types.Dimension(dim_bp)  
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=400)

    def get_selected_collection(self,context):
        sel_obj = context.object
        if sel_obj.instance_type == 'COLLECTION':
            return sel_obj.instance_collection

    def get_assembly_collection(self,collection):
        obj_bp = collection.pyclone.assembly_bp
        assembly = pc_types.Assembly(obj_bp)
        return assembly

    def execute(self, context):
        sel_obj = context.object
        collection = self.get_selected_collection(context)
        assembly = self.get_assembly_collection(collection)

        if self.add_x_dimension:
            dim = pc_types.Dimension()
            dim.create_dimension()
            dim.obj_bp.rotation_euler.x = math.radians(-90)
            dim.obj_bp.rotation_euler.y = 0
            dim.obj_y.location.y = .2
            dim.obj_bp.parent = sel_obj
            dim.obj_bp.location = assembly.obj_bp.location
            dim.obj_x.location.x = assembly.obj_x.location.x
            dim.update_dim_text()

        if self.add_y_dimension:
            dim = pc_types.Dimension()
            dim.create_dimension()
            dim.obj_bp.rotation_euler.x = math.radians(90)
            dim.obj_bp.rotation_euler.y = math.radians(0)
            dim.obj_bp.rotation_euler.z = math.radians(-90)
            dim.obj_y.location.y = -.2
            dim.obj_bp.parent = sel_obj
            dim.obj_bp.location = assembly.obj_bp.location
            dim.obj_x.location.x = math.fabs(assembly.obj_y.location.y)
            dim.update_dim_text()

        if self.add_z_dimension:
            dim = pc_types.Dimension()
            dim.create_dimension()
            dim.obj_bp.rotation_euler.x = math.radians(90)
            dim.obj_bp.rotation_euler.y = math.radians(-90)
            dim.obj_y.location.y = .2
            dim.obj_bp.parent = sel_obj
            dim.obj_bp.location = assembly.obj_bp.location
            dim.obj_x.location.x = assembly.obj_z.location.z
            dim.update_dim_text()            
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self,'add_x_dimension')
        layout.prop(self,'add_y_dimension')
        layout.prop(self,'add_z_dimension')      


class pc_assembly_OT_add_title_block(bpy.types.Operator):
    bl_idname = "pc_assembly.add_title_block"
    bl_label = "Add Title Block"
    bl_description = "This adds a title block to the current layout"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    # def get_selected_collection(self,context):
    #     sel_obj = context.object
    #     if sel_obj.instance_type == 'COLLECTION':
    #         return sel_obj.instance_collection

    # def get_title_block(self,context):
    #     collection = self.get_selected_collection(context)

    #     ROOT_PATH = os.path.dirname(__file__)
    #     PATH = os.path.join(os.path.dirname(ROOT_PATH),'assets',"Title_Block.blend")

    #     with bpy.data.libraries.load(PATH, False, False) as (data_from, data_to):
    #         data_to.objects = data_from.objects

    #     for obj in data_to.objects:
    #         collection.objects.link(obj)

    def execute(self, context):
        title_block = pc_types.Title_Block()
        title_block.create_title_block()
        return {'FINISHED'}


class pc_assembly_OT_show_dimension_properties(Operator):
    bl_idname = "pc_assembly.show_dimension_properties"
    bl_label = "Show Dimension Properties"
    bl_description = "This will show the dimension properties"
    bl_options = {'UNDO'}

    obj_bp_name: StringProperty(name="Base Point Name")

    dimension = None

    def execute(self, context):
        self.dimension.update_dim_text()
        return {'FINISHED'}

    def check(self, context):
        self.dimension.update_dim_text()
        return True

    def invoke(self,context,event):
        dim_bp = pc_utils.get_assembly_bp(context.object)
        self.dimension = pc_types.Dimension(dim_bp)  
        self.dimension.update_dim_text()
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        self.dimension.draw_ui(context,layout)


classes = (
    pc_assembly_OT_create_new_assembly,
    pc_assembly_OT_delete_assembly,
    pc_assembly_OT_select_base_point,
    pc_assembly_OT_duplicate_assembly,
    pc_assembly_OT_add_object,
    pc_assembly_OT_connect_mesh_to_hooks_in_assembly,
    pc_assembly_OT_create_assembly_script,
    pc_assembly_OT_select_parent_assembly,
    pc_assembly_OT_create_assembly_layout,
    pc_assembly_OT_create_assembly_dimension,
    pc_assembly_OT_show_dimension_properties,
    pc_assembly_OT_add_title_block
)

register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
    register()