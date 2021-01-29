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
        EnumProperty,
        )
import os
import inspect
import math

prompt_types = [('FLOAT',"Float","Float"),
                ('DISTANCE',"Distance","Distance"),
                ('ANGLE',"Angle","Angle"),
                ('QUANTITY',"Quantity","Quantity"),
                ('PERCENTAGE',"Percentage","Percentage"),
                ('CHECKBOX',"Checkbox","Checkbox"),
                ('COMBOBOX',"Combobox","Combobox"),
                ('TEXT',"Text","Text")]

def add_driver_variables(driver,variables):
    for var in variables:
        new_var = driver.driver.variables.new()
        new_var.type = 'SINGLE_PROP'
        new_var.name = var.name
        new_var.targets[0].data_path = var.data_path
        new_var.targets[0].id = var.obj


class Variable():

    obj = None
    data_path = ""
    name = ""

    def __init__(self,obj,data_path,name):
        self.obj = obj
        self.data_path = data_path
        self.name = name


class Combobox_Item(PropertyGroup):
    pass    


class Library_Item(bpy.types.PropertyGroup):
    package_name: bpy.props.StringProperty(name="Package Name")
    module_name: bpy.props.StringProperty(name="Module Name")
    class_name: bpy.props.StringProperty(name="Class Name")
    placement_id: bpy.props.StringProperty(name="Placement ID")
    prompts_id: bpy.props.StringProperty(name="Prompts ID")
    render_id: bpy.props.StringProperty(name="Render ID")
    category_name: bpy.props.StringProperty(name="Category Name")


class Library(bpy.types.PropertyGroup):
    library_items: bpy.props.CollectionProperty(name="Library Items", type=Library_Item)
    activate_id: bpy.props.StringProperty(name="Activate ID",description="This is the operator id that gets called when you activate the library")
    drop_id: bpy.props.StringProperty(name="Drop ID",description="This is the operator id that gets called when you drop a file onto the 3D Viewport")
    icon: bpy.props.StringProperty(name="Icon",description="This is the icon to display in the panel")

    def load_library_items_from_module(self,module):
        package_name1, package_name2, module_name = module.__name__.split(".")
        for name, obj in inspect.getmembers(module):
            if hasattr(obj,'show_in_library') and name != 'ops' and obj.show_in_library:
                item = self.library_items.add()
                item.package_name = package_name1 + "." + package_name2
                item.category_name = obj.category_name
                item.module_name = module_name
                item.class_name = name
                item.name = name


class Pointer_Slot(bpy.types.PropertyGroup):
    pointer_name: StringProperty(name="Pointer Name", description="")


class Prompt(PropertyGroup):
    prompt_type: EnumProperty(name="Prompt Type",items=prompt_types)

    float_value: FloatProperty(name="Float Value")
    distance_value: FloatProperty(name="Distance Value",subtype='DISTANCE',precision=2)
    angle_value: FloatProperty(name="Angle Value",subtype='ANGLE')
    quantity_value: IntProperty(name="Quantity Value",subtype='DISTANCE',min=0)
    percentage_value: FloatProperty(name="Percentage Value",subtype='PERCENTAGE',min=0,max=1)
    checkbox_value: BoolProperty(name="Checkbox Value", description="")
    text_value: StringProperty(name="Text Value", description="")

    calculator_index: IntProperty(name="Calculator Index")

    combobox_items: CollectionProperty(type=Combobox_Item, name="Tabs")
    combobox_index: IntProperty(name="Combobox Index", description="")
    combobox_columns: IntProperty(name="Combobox Columns",default=1,min=1)

    def get_var(self,name):
        prompt_path = 'pyclone.prompts["' + self.name + '"]'
        if self.prompt_type == 'FLOAT':
            return Variable(self.id_data, prompt_path + '.float_value',name)
        if self.prompt_type == 'DISTANCE':
            return Variable(self.id_data, prompt_path + '.distance_value',name)
        if self.prompt_type == 'ANGLE':
            return Variable(self.id_data, prompt_path + '.angle_value',name)
        if self.prompt_type == 'QUANTITY':
            return Variable(self.id_data, prompt_path + '.quantity_value',name)
        if self.prompt_type == 'PERCENTAGE':
            return Variable(self.id_data, prompt_path + '.percentage_value',name)
        if self.prompt_type == 'CHECKBOX':
            return Variable(self.id_data, prompt_path + '.checkbox_value',name)
        if self.prompt_type == 'COMBOBOX':
            return Variable(self.id_data, prompt_path + '.combobox_index',name) #TODO: IMPLEMENT UI LIST
        if self.prompt_type == 'TEXT':
            return Variable(self.id_data, prompt_path + '.text_value',name)       

    def get_value(self):
        if self.prompt_type == 'FLOAT':
            return self.float_value
        if self.prompt_type == 'DISTANCE':
            return self.distance_value
        if self.prompt_type == 'ANGLE':
            return self.angle_value
        if self.prompt_type == 'QUANTITY':
            return self.quantity_value
        if self.prompt_type == 'PERCENTAGE':
            return self.percentage_value
        if self.prompt_type == 'CHECKBOX':
            return self.checkbox_value
        if self.prompt_type == 'COMBOBOX':
            return self.combobox_index #TODO: IMPLEMENT UI LIST
        if self.prompt_type == 'TEXT':
            return self.text_value

    def set_value(self,value):
        self.id_data.hide_viewport = False
        if self.prompt_type == 'FLOAT':
            self.float_value = value
        if self.prompt_type == 'DISTANCE':
            self.distance_value = value
        if self.prompt_type == 'ANGLE':
            self.angle_value = math.radians(value)
        if self.prompt_type == 'QUANTITY':
            self.quantity_value = value
        if self.prompt_type == 'PERCENTAGE':
            self.percentage_value = value
        if self.prompt_type == 'CHECKBOX':
            self.checkbox_value = value
        if self.prompt_type == 'COMBOBOX':
            self.combobox_index = value #TODO: IMPLEMENT UI LIST
        if self.prompt_type == 'TEXT':
            self.text_value = value
        self.id_data.hide_viewport = True

    def set_formula(self,expression,variables):
        data_path = self.get_data_path()
        driver = self.id_data.driver_add(data_path)
        add_driver_variables(driver,variables)
        driver.driver.expression = expression

    def get_data_path(self):
        prompt_path = 'pyclone.prompts["' + self.name + '"]'
        data_path = ""
        if self.prompt_type == 'FLOAT':
            data_path = prompt_path + '.float_value'
        if self.prompt_type == 'DISTANCE':
            data_path = prompt_path + '.distance_value'
        if self.prompt_type == 'ANGLE':
            data_path = prompt_path + '.angle_value'
        if self.prompt_type == 'QUANTITY':
            data_path = prompt_path + '.quantity_value'
        if self.prompt_type == 'PERCENTAGE':
            data_path = prompt_path + '.precentage_value'
        if self.prompt_type == 'CHECKBOX':
            data_path = prompt_path + '.checkbox_value'
        if self.prompt_type == 'COMBOBOX':
            data_path = prompt_path + '.combobox_index'
        if self.prompt_type == 'TEXT':
            data_path = prompt_path + '.text_value'
        return data_path

    def draw_prompt_properties(self,layout):
        pass #RENAME PROMPT, #LOCK VALUE,  #IF COMBOBOX THEN COLUMN NUMBER

    def draw(self,layout,allow_edit=True):
        row = layout.row()
        row.label(text=self.name)
        if self.prompt_type == 'FLOAT':
            row.prop(self,"float_value",text="")
        if self.prompt_type == 'DISTANCE':
            row.prop(self,"distance_value",text="")
        if self.prompt_type == 'ANGLE':
            row.prop(self,"angle_value",text="")
        if self.prompt_type == 'QUANTITY':
            row.prop(self,"quantity_value",text="")
        if self.prompt_type == 'PERCENTAGE':
            row.prop(self,"percentage_value",text="")
        if self.prompt_type == 'CHECKBOX':
            row.prop(self,"checkbox_value",text="")
        if self.prompt_type == 'COMBOBOX':
            if allow_edit:
                props = row.operator('pc_prompts.add_combobox_value',text="",icon='ADD')
                props.obj_name = self.id_data.name
                props.prompt_name = self.name
                props = row.operator('pc_prompts.delete_combobox_value',text="",icon='X')
                props.obj_name = self.id_data.name
                props.prompt_name = self.name   
                col = layout.column()
                col.template_list("PC_UL_combobox"," ", self, "combobox_items", self, "combobox_index",
                                rows=len(self.combobox_items)/self.combobox_columns,type='GRID',columns=self.combobox_columns)
            else:
                row.template_list("PC_UL_combobox"," ", self, "combobox_items", self, "combobox_index",
                                rows=len(self.combobox_items)/self.combobox_columns,type='GRID',columns=self.combobox_columns)

        if self.prompt_type == 'TEXT':
            row.prop(self,"text_value",text="")

        if allow_edit:
            props = row.operator('pc_prompts.delete_prompt',text="",icon="X",emboss=False)
            props.obj_name = self.id_data.name
            props.prompt_name = self.name


class Calculator_Prompt(PropertyGroup):
    distance_value: FloatProperty(name="Distance Value",subtype='DISTANCE')
    equal: BoolProperty(name="Equal",default=True)

    def draw(self,layout):
        row = layout.row()
        row.active = False if self.equal else True
        row.prop(self,'distance_value',text=self.name)
        row.prop(self,'equal',text="")

    def get_var(self,calculator_name,name):
        prompt_path = 'pyclone.calculators["' + calculator_name + '"].prompts["' + self.name + '"]'
        return Variable(self.id_data, prompt_path + '.distance_value',name)    

class Calculator(PropertyGroup):
    prompts: CollectionProperty(name="Prompts",type=Calculator_Prompt)
    distance_obj: PointerProperty(name="Distance Obj",type=bpy.types.Object)

    def set_total_distance(self,expression="",variables=[],value=0):
        data_path = 'pyclone.calculator_distance'
        driver = self.distance_obj.driver_add(data_path)
        add_driver_variables(driver,variables)
        driver.driver.expression = expression

    def draw(self,layout):
        col = layout.column(align=True)
        box = col.box()
        row = box.row()
        row.label(text=self.name)
        props = row.operator('pc_prompts.add_calculator_prompt',text="",icon='ADD')
        props.calculator_name = self.name
        props.obj_name = self.id_data.name
        props = row.operator('pc_prompts.edit_calculator',text="",icon='OUTLINER_DATA_GP_LAYER')
        props.calculator_name = self.name
        props.obj_name = self.id_data.name
        
        box.prop(self.distance_obj.pyclone,'calculator_distance')
        box = col.box()
        for prompt in self.prompts:
            prompt.draw(box)
        box = col.box()
        row = box.row()
        row.scale_y = 1.3
        props = row.operator('pc_prompts.run_calculator')
        props.calculator_name = self.name
        props.obj_name = self.id_data.name        

    def add_calculator_prompt(self,name):
        prompt = self.prompts.add()
        prompt.name = name
        return prompt

    def get_calculator_prompt(self,name):
        if name in self.prompts:
            return self.prompts[name]

    def remove_calculator_prompt(self,name):
        pass

    def calculate(self):
        self.distance_obj.hide_viewport = False

        non_equal_prompts_total_value = 0
        equal_prompt_qty = 0
        calc_prompts = []
        for prompt in self.prompts:
            if prompt.equal:
                equal_prompt_qty += 1
                calc_prompts.append(prompt)
            else:
                non_equal_prompts_total_value += prompt.distance_value

        if equal_prompt_qty > 0:
            prompt_value = (self.distance_obj.pyclone.calculator_distance - non_equal_prompts_total_value) / equal_prompt_qty

            for prompt in calc_prompts:
                prompt.distance_value = prompt_value

            self.id_data.location = self.id_data.location 


class PC_Object_Props(PropertyGroup):
    show_object_props: BoolProperty(name="Show Object Props", default=False)
    object_tabs: EnumProperty(name="Object Tabs",
                              items=[('MAIN',"Main","Show the Main Properties"),
                                     ('DATA',"Data","Show the Data"),
                                     ('MATERIAL',"Material","Show the Materials")],
                              default='MAIN')
    show_driver_debug_info: BoolProperty(name="Show Driver Debug Info", default=False)
    pointers: bpy.props.CollectionProperty(name="Pointer Slots", type=Pointer_Slot)
    prompts: CollectionProperty(type=Prompt, name="Prompts")
    calculators: CollectionProperty(type=Calculator, name="Calculators")
    calculator_distance: FloatProperty(name="Calculator Distance",subtype='DISTANCE')
    prompt_index: IntProperty(name="Prompt Index")
    calculator_index: IntProperty(name="Calculator Index")

    is_view_object: BoolProperty(name="Is View Object", default=False)

    def add_prompt(self,prompt_type,prompt_name):
        prompt = self.prompts.add()
        prompt.prompt_type = prompt_type
        prompt.name = prompt_name
        return prompt

    def add_calculator(self,calculator_name,calculator_object):
        calculator = self.calculators.add()
        calculator.distance_obj = calculator_object
        calculator.name = calculator_name
        return calculator

    def add_data_driver(self,property_name,index,expression,variables):
        if index == -1:
            driver = self.id_data.data.driver_add(property_name)
        else:
            driver = self.id_data.data.driver_add(property_name,index)
        add_driver_variables(driver,variables)
        driver.driver.expression = expression

    def add_driver(self,property_name,index,expression,variables):
        if index == -1:
            driver = self.id_data.driver_add(property_name)
        else:
            driver = self.id_data.driver_add(property_name,index)
        add_driver_variables(driver,variables)
        driver.driver.expression = expression

    def delete_prompt(self,name):
        for index, prompt in enumerate(self.prompts):
            if prompt.name == name:
                self.prompts.remove(index)

    def draw_prompts(self,layout):
        row = layout.row(align=True)
        row.scale_y = 1.3
        props = row.operator('pc_prompts.add_prompt',icon='LINENUMBERS_ON')
        props.obj_name = self.id_data.name
        props = row.operator('pc_prompts.add_calculator',icon='SYNTAX_ON')
        props.obj_name = self.id_data.name        
        for prompt in self.prompts:
            prompt.draw(layout)
        for cal in self.calculators:
            cal.draw(layout)

    def get_var(self,data_path,name):
        return Variable(self.id_data,data_path,name)

    def get_prompt(self,prompt_name):
        if prompt_name in self.prompts:
            return self.prompts[prompt_name]

    def modifier(self,modifier,property_name,index=-1,expression="",variables=[]):
        driver = modifier.driver_add(property_name,index)
        add_driver_variables(driver,variables)
        driver.driver.expression = expression

    def hide(self,expression,variables):
        driver = self.id_data.driver_add('hide_viewport')
        add_driver_variables(driver,variables)
        driver.driver.expression = expression
        driver = self.id_data.driver_add('hide_render')
        add_driver_variables(driver,variables)
        driver.driver.expression = expression

    def loc_x(self,expression="",variables=[],value=0):
        if expression == "":
            self.id_data.location.x = value
            return
        driver = self.id_data.driver_add('location',0)
        add_driver_variables(driver,variables)
        driver.driver.expression = expression

    def loc_y(self,expression="",variables=[],value=0):
        if expression == "":
            self.id_data.location.y = value        
            return
        driver = self.id_data.driver_add('location',1)
        add_driver_variables(driver,variables)
        driver.driver.expression = expression

    def loc_z(self,expression="",variables=[],value=0):
        if expression == "":
            self.id_data.location.z = value        
            return
        driver = self.id_data.driver_add('location',2)
        add_driver_variables(driver,variables)
        driver.driver.expression = expression

    def rot_x(self,expression="",variables=[],value=0):
        if expression == "":
            self.id_data.rotation_euler.x = value        
            return
        driver = self.id_data.driver_add('rotation_euler',0)
        add_driver_variables(driver,variables)
        driver.driver.expression = expression

    def rot_y(self,expression="",variables=[],value=0):
        if expression == "":
            self.id_data.rotation_euler.y = value      
            return  
        driver = self.id_data.driver_add('rotation_euler',1)
        add_driver_variables(driver,variables)
        driver.driver.expression = expression

    def rot_z(self,expression="",variables=[],value=0):
        if expression == "":
            self.id_data.rotation_euler.z = value        
            return
        driver = self.id_data.driver_add('rotation_euler',2)
        add_driver_variables(driver,variables)
        driver.driver.expression = expression

    @classmethod
    def register(cls):
        bpy.types.Object.pyclone = PointerProperty(name="PyClone",description="PyClone Properties",type=cls)
        
    @classmethod
    def unregister(cls):
        del bpy.types.Object.pyclone


class PC_Window_Manager_Props(bpy.types.PropertyGroup):
    libraries: CollectionProperty(name="Libraries",type=Library)

    def add_library(self,name,activate_id,drop_id,icon):
        lib = self.libraries.add()
        lib.name = name
        lib.activate_id = activate_id
        lib.drop_id = drop_id
        lib.icon = icon
        return lib

    def remove_library(self,name):
        for i, lib in enumerate(self.libraries):
            if lib.name == name:
                self.libraries.remove(i)

    @classmethod
    def register(cls):
        bpy.types.WindowManager.pyclone = bpy.props.PointerProperty(
            name="PyClone",
            description="PyClone Properties",
            type=cls,
        )
        
    @classmethod
    def unregister(cls):
        del bpy.types.WindowManager.pyclone    

def update_page_scale(self,context):
    cam_obj = context.scene.camera
    cam_obj.data.ortho_scale = .279
    cam_obj.location.x = .1395
    cam_obj.location.y = -2.0573
    cam_obj.location.z = 0.0784

    #TODO: SETUP ALL DIFFERENT OBJECT SCALE
    if self.page_scale == '1:1':
        scale = (1,1,1)
    elif self.page_scale == '1/2in_1ft':
        scale = (0.04166,0.04166,0.04166)    
    elif self.page_scale == '1/4in_1ft':
        scale = (0.02083,0.02083,0.02083)    
    elif self.page_scale == '1in_1ft':
        scale = (.08332,.08332,.08332)    
    else:
        scale = (.08332,.08332,.08332)

    for obj in context.visible_objects:
        if obj.pyclone.is_view_object and obj.type == 'EMPTY' and obj.instance_type == 'COLLECTION':
            obj.scale = scale

class PC_Scene_Props(PropertyGroup):
    assembly_tabs: EnumProperty(name="Assembly Tabs",
                                items=[('MAIN',"Main","Show the Main Properties"),
                                       ('PROMPTS',"Prompts","Show the Prompts"),
                                       ('OBJECTS',"Objects","Show the Objects"),
                                       ('LOGIC',"Logic","Show the Assembly Logic")],
                                default='MAIN')

    driver_tabs: EnumProperty(name="Driver Tabs",
                              items=[('LOC_X',"Location X","Show the X Location Driver"),
                                     ('LOC_Y',"Location Y","Show the Y Location Driver"),
                                     ('LOC_Z',"Location Z","Show the Z Location Driver"),
                                     ('ROT_X',"Rotation X","Show the X Rotation Driver"),
                                     ('ROT_Y',"Rotation Y","Show the Y Rotation Driver"),
                                     ('ROT_Z',"Rotation Z","Show the Z Rotation Driver"),
                                     ('DIM_X',"Dimension X","Show the X Dimension Driver"),
                                     ('DIM_Y',"Dimension Y","Show the Y Dimension Driver"),
                                     ('DIM_Z',"Dimension Z","Show the Z Dimension Driver"),
                                     ('PROMPTS',"Prompts","Show the Prompt Drivers"),
                                     ('CALCULATORS',"Calculators","Show the Calculator Drivers"),
                                     ('SELECTED_OBJECT',"Selected Object","Show the Drivers for the Selected Object")],
                              default='SELECTED_OBJECT')

    driver_override_object: PointerProperty(name="Active Library Name",type=bpy.types.Object)

    active_library_name: StringProperty(name="Active Library Name",default="")

    is_view_scene: BoolProperty(name="Is View Scene",default=False)

    page_size: EnumProperty(name="Page Size",
                            items=[('LETTER',"Letter 216 x 279 mm (8.5 X 11 in)","Letter 216 x 279 mm (8.5 X 11 in)"),
                                   ('LEGAL',"Legal 216 x 356 mm (8.5 X 14 in)","Legal 216 x 356 mm (8.5 X 14 in)"),
                                   ('ANSI_A',"ANSI A 216 x 279 mm (8.5 X 11 in)","ANSI A 216 x 279 mm (8.5 X 11 in)"),
                                   ('ANSI_B',"ANSI B 279 x 432 mm (11 X 17 in)","ANSI B 279 x 432 mm (11 X 17 in)"),
                                   ('ANSI_C',"ANSI C 432 x 559 mm (17 X 22 in)","ANSI C 432 x 559 mm (17 X 22 in)"),
                                   ('ANSI_D',"ANSI D 559 x 864 mm (22 X 34 in)","ANSI D 559 x 864 mm (22 X 34 in)"),
                                   ('ANSI_E',"ANSI E 216 x 279 mm (34 X 44 in)","ANSI E 216 x 279 mm (34 X 44 in)"),
                                   ('ARCH_A',"ARCH A 229 × 305 mm (9 X 12 in)","ARCH A 229 × 305 mm (9 X 12 in)"),
                                   ('ARCH_B',"ARCH B 305 × 457 mm (12 X 18 in)","ARCH B 305 × 457 mm (12 X 18 in)"),
                                   ('ARCH_C',"ARCH C 457 × 610 mm (18 X 24 in)","ARCH C 457 × 610 mm (18 X 24 in)"),
                                   ('ARCH_D',"ARCH D 610 × 914 mm (24 X 36 in)","ARCH D 610 × 914 mm (24 X 36 in)"),
                                   ('ARCH_E',"ARCH E 914 × 1219 mm (36 X 48 in)","ARCH E 914 × 1219 mm (36 X 48 in)")],
                              default='LETTER')

    fit_to_paper: BoolProperty(name="Fit to Paper",default=True,update=update_page_scale)

    page_scale: EnumProperty(name="Page Scale",
                            items=[('1:1',"1:1","1:1"),
                                   ('1/4in_1ft',"1/4 in = 1 ft","1:1"),
                                   ('3/8in_1ft',"3/8 in = 1 ft","1:1"),
                                   ('1/2in_1ft',"1/2 in = 1 ft","1:1"),
                                   ('3/4in_1ft',"3/4 in = 1 ft","1:1"),
                                   ('1in_1ft',"1 in = 1 ft","1 inch = 1 foot"),
                                   ('1-1/2in_1ft',"3/4 in = 1 ft","1:1")],
                            default='1:1',
                            update=update_page_scale)

    page_style: EnumProperty(name="Page Style",
                             items=[('BLACK_AND_WHITE',"Black and White","Black and White"),
                                    ('FULL_COLOR',"Full Color","Full Color"),
                                    ('MONOCHROME',"Monochrome","Monochrome"),
                                    ('SCREENING_100%',"Screening 100%","Screening 100%"),
                                    ('SCREENING_25%',"Screening 25%","Screening 25%"),
                                    ('SCREENING_50%',"Screening 50%","Screening 50%"),
                                    ('SCREENING_75%',"Screening 75%","Screening 75%"),
                                    ('New...',"New..","New...")],
                             default='FULL_COLOR')

    @classmethod
    def register(cls):
        bpy.types.Scene.pyclone = PointerProperty(
            name="PyClone",
            description="PyClone Properties",
            type=cls,
        )
        
    @classmethod
    def unregister(cls):
        del bpy.types.Scene.pyclone


classes = (
    Combobox_Item,
    Library_Item,
    Library,
    Pointer_Slot,
    Prompt,
    Calculator_Prompt,
    Calculator,
    PC_Object_Props,
    PC_Window_Manager_Props,
    PC_Scene_Props,
)

register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
    register()