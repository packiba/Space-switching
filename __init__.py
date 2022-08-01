bl_info = {
    "name": "Space switching",
    "author": "Pavel Kiba",
    "version": (1, 0, 1),
    "blender": (3, 0, 0),
    "location": "View3D > N-Panel > Animation",
    "description": "Add space switching for bones",
    "warning": "",
    "doc_url": "",
    "category": "Animation", }

import bpy
from bpy.utils import register_class, unregister_class
from bpy.props import EnumProperty, BoolProperty, FloatProperty, IntProperty, PointerProperty
from bpy.types import Operator, Scene, Panel, PropertyGroup

LOC = 'loc'
ROT = 'rot'
axes = [
    ('X', ' X', 'Select  X', 0),
    ('-X', '-X', 'Select  -X', 1),
    ('Y', ' Y', 'Select  Y', 2),
    ('-Y', '-Y', 'Select  -Y', 3),
    ('Z', ' Z', 'Select  Z', 4),
    ('-Z', '-Z', 'Select  -Z', 5),
]

zbd_chars = [
    'captain_leet',
    'pala',
    'hesh',
    'diggley',
    'hesh_small'
]


def upper_case_name(name):
    return '_'.join(name.upper().split())

# Функция для поиска во "вью-лейере" нужной коллекции по названию
# 1 переменная - слот для переменной во "вью-лейере", 2 переменная - название коллекции
def get_recur_layer_coll(layercoll, collname):
    found = None
    if (layercoll.name == collname):
        if layercoll.collection.library is None:
            return layercoll
    for layer in layercoll.children:
        found = get_recur_layer_coll(layer, collname)
        if found:
            return found

# Функция для назначения коллекции активной во "вью-лейере" по названию.
def set_active_layer_coll(coll_name):
    layer_coll = bpy.context.view_layer.layer_collection
    coll_layer = get_recur_layer_coll(layer_coll,
                                      coll_name)
    bpy.context.view_layer.active_layer_collection = coll_layer


class SpaceSwitchingProps(PropertyGroup):
    axis: EnumProperty(
        name="Bone Axis",
        items=axes,
        description="Select axis to space switch",
        default="Y",
    )
    
    is_zbd: BoolProperty(
        name="ZBD character",
        description="This rig is ZBD character",
        default=False,
    )

    some_bone: BoolProperty(
        name="Enable for selected bone",
        description="Enable space switching for selected bone",
        default=False,
    )

    hands_on: BoolProperty(
        name="Enable for hands",
        description="Enable space switching for hands",
        default=False,
    )

    hand_L_on: BoolProperty(
        name="Enable for left hand",
        description="Enable space switching for left hand",
        default=False,
    )

    hand_R_on: BoolProperty(
        name="Enable for right hand",
        description="Enable space switching for right hand",
        default=False,
    )

    rot_distance: FloatProperty(
        name="Distance to rotation target",
        description="Distance to rotation target",
        default=0.15,
        soft_min=0.05,
        soft_max=0.25,
        subtype='FACTOR'
    )

    value_displacement: FloatProperty(
        name="Displacement value",
        description="Displacement value",
        default=0.5,
        min=0,
        max=1,
        soft_min=0,
        soft_max=1,
        subtype='FACTOR'
    )


class SpaceSwitch(Operator):
    """
    Enable space switching for the bones
    """

    bl_idname = 'scene.space_switch'
    bl_label = 'space switch'

    @classmethod
    def add_target_constraint(cls, constraint, armature, bone):
        bpy.ops.object.constraint_add(type=upper_case_name(constraint))
        bpy.context.active_object.constraints[constraint].target = bpy.data.objects[armature]
        bpy.context.object.constraints[constraint].subtarget = bone.name

    
    def translate_target(self, props, bone):
        if props.hands_on and not props.some_bone and props.is_zbd:
            if bone.name.split('.')[-1] == 'L':
                bpy.ops.transform.translate(value=(props.rot_distance, 0, 0), orient_type='LOCAL')
            else:
                bpy.ops.transform.translate(value=(-props.rot_distance, 0, 0), orient_type='LOCAL')
        else:
            print('axis', props.axis)
            print('rot_distance', props.rot_distance)
            if props.axis == 'X':
                bpy.ops.transform.translate(value=(props.rot_distance, 0, 0), orient_type='LOCAL')
            elif props.axis == '-X':
                bpy.ops.transform.translate(value=(-props.rot_distance, 0, 0), orient_type='LOCAL')
            elif props.axis == 'Y':
                bpy.ops.transform.translate(value=(0, props.rot_distance, 0), orient_type='LOCAL')
            elif props.axis == '-Y':
                bpy.ops.transform.translate(value=(0, -props.rot_distance, 0), orient_type='LOCAL')
            elif props.axis == 'Z':
                bpy.ops.transform.translate(value=(0, 0, props.rot_distance), orient_type='LOCAL')
            elif props.axis == '-Z':
                bpy.ops.transform.translate(value=(0, 0, -props.rot_distance), orient_type='LOCAL')

    def create_target(self, scene, props, armature, bone, type):
        character = armature.split('_armature')[0]
        st_frame = scene.frame_start
        end_frame = scene.frame_end
        if type == LOC:
            constraint_type = 'Copy Location'
        else:
            constraint_type = 'Copy Transforms'

        name = f'{character}_{bone.name}_{type}_target'
        set_active_layer_coll(f'{character}_space_switching')
        bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD')
        target = bpy.context.selected_objects[0]
        target.empty_display_size = 0.1
        target.name = name
        bpy.ops.object.constraints_clear()
        self.add_target_constraint(constraint_type, armature, bone)
        bpy.ops.object.visual_transform_apply()
        bpy.ops.constraint.delete(constraint=constraint_type, owner='OBJECT')
        if type == ROT:
            self.translate_target(props, bone)
        self.add_target_constraint('Child Of', armature, bone)
        bpy.ops.constraint.childof_set_inverse(constraint="Child Of", owner='OBJECT')
        bpy.ops.nla.bake(frame_start=st_frame, frame_end=end_frame, only_selected=False,
                         visual_keying=True, clear_constraints=True, bake_types={'OBJECT'})

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        scene = context.scene
        props = scene.space_switching
        armature = bpy.context.active_object.name
        character = armature.split('_armature')[0]
        print(character)
        bones = []        
        for char in zbd_chars:
            if char in armature:
                props.is_zbd = True

        if props.is_zbd:
            if props.hand_L_on:
                bones.append(bpy.data.objects[armature].pose.bones['hand.L'])
            if props.hand_R_on:
                bones.append(bpy.data.objects[armature].pose.bones['hand.R'])
            if props.some_bone:
                bones = bpy.context.selected_pose_bones
        else:
            bones = bpy.context.selected_pose_bones

        bpy.ops.object.posemode_toggle()


        if props.is_zbd:
            set_active_layer_coll(character)
            
        if not get_recur_layer_coll(bpy.context.view_layer.layer_collection, f'{character}_space_switching'):
            collection = bpy.context.blend_data.collections.new(name=f'{character}_space_switching')
            bpy.context.collection.children.link(collection)

        for bone in bones:
            self.create_target(scene, props, armature, bone, LOC)
            self.create_target(scene, props, armature, bone, ROT)

        obj = bpy.data.objects[armature]


        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        bpy.ops.object.posemode_toggle()

        for bone in bones:
            name1 = f'{character}_{bone.name}_{ROT}_target'
            name2 = f'{character}_{bone.name}_{LOC}_target'
            bone.constraints.new(type='DAMPED_TRACK')
            print(name1)
            print(name2)
            bone.constraints["Damped Track"].target = bpy.data.objects[name1]
            if props.hands_on and not props.some_bone and props.is_zbd:
                if bone.name.split('.')[-1] == 'L':
                    bone.constraints["Damped Track"].track_axis = 'TRACK_X'
                else:
                    bone.constraints["Damped Track"].track_axis = 'TRACK_NEGATIVE_X'
            else:
                if props.axis == 'X':
                    bone.constraints["Damped Track"].track_axis = 'TRACK_X'
                elif props.axis == '-X':
                    bone.constraints["Damped Track"].track_axis = 'TRACK_NEGATIVE_X'
                elif props.axis == 'Y':
                    bone.constraints["Damped Track"].track_axis = 'TRACK_Y'
                elif props.axis == '-Y':
                    bone.constraints["Damped Track"].track_axis = 'TRACK_NEGATIVE_Y'
                elif props.axis == 'Z':
                    bone.constraints["Damped Track"].track_axis = 'TRACK_Z'
                elif props.axis == '-Z':
                    bone.constraints["Damped Track"].track_axis = 'TRACK_NEGATIVE_Z'

            bone.constraints.new(type='COPY_LOCATION')
            bone.constraints["Copy Location"].target = bpy.data.objects[name2]
            bone.constraints["Copy Location"].influence = props.value_displacement

        return {'FINISHED'}


class OBJECT_PT_SpaceSwitching(Panel):
    bl_label = 'Space switching'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Animation'

    def draw(self, context):
        armature = context.active_object.name
        is_ZBD_char = False
        for char in zbd_chars:
            if char in armature:
                is_ZBD_char = True
        bones = context.selected_pose_bones
        props = context.scene.space_switching

        layout = self.layout
        if is_ZBD_char:
            if not props.some_bone:
                row = layout.row(align=True)
                col = row.column()
                col.prop(props, "hands_on", text='hands', toggle=True)
                if props.hands_on:
                    row.separator()
                    row = row.row(align=True)
                    row.prop(props, "hand_L_on", text='L', toggle=True)
                    row.prop(props, "hand_R_on", text='R', toggle=True)

        row = layout.row(align=True)
        col = row.column()

        if is_ZBD_char:
            if props.some_bone:
                if len(bones) == 0:
                    col.prop(props, "some_bone", text=' select bone', toggle=True)
                elif len(bones) > 1:
                    col.prop(props, "some_bone", text=' select only one bone', toggle=True)
                else:
                    sel_bone_name = bones[0].name
                    col.prop(props, "some_bone", text=sel_bone_name, toggle=True)
                    row.separator()
                    col = row.column()
                    col.enabled = props.some_bone
                    col.prop(props, "axis", text='', icon='EMPTY_ARROWS')
            else:
                col.prop(props, "some_bone", text='selected bone', toggle=True)
        else:
            if bones and len(bones) == 0:
                col.prop(props, "some_bone", text=' select bone', toggle=True)
            elif bones and len(bones) > 1:
                col.prop(props, "some_bone", text=' select only one bone', toggle=True)
            else:
                if bones:
                    sel_bone_name = bones[0].name
                    col.label(text=sel_bone_name)
                col = row.column()
                col.prop(props, "axis", text='', icon='EMPTY_ARROWS')

        col = layout.column()
        col.prop(props, "rot_distance")
        col.prop(props, "value_displacement")
        col.separator()

        col = layout.column()
        if props.some_bone and len(bones) == 1:
            col.operator(SpaceSwitch.bl_idname, text="Start space switch")
        elif props.hands_on and not props.some_bone and (props.hand_L_on or props.hand_R_on):
            col.operator(SpaceSwitch.bl_idname, text="Start space switch")
        else:            
            col.label(text='Nothing to space switch')
            col.alignment = 'CENTER'


classes = [
    SpaceSwitchingProps,
    SpaceSwitch,
    OBJECT_PT_SpaceSwitching,
]


def register():
    for cl in classes:
        register_class(cl)

    bpy.types.Scene.space_switching = PointerProperty(type=SpaceSwitchingProps)


def unregister():
    for cl in reversed(classes):
        register_class(cl)


if __name__ == "__main__":
    register()
