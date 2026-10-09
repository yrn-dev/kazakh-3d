extends Node3D
var players: Array[AnimationPlayer] = []
var camera: Camera3D
var t := 0.0
var paused := false
const FILES = ['teen-boy','cartoon_asian__boy','free_stylized_cartoon_girl_rigged_character','free_cartoon_game_man_character_rigged']
const NAMES = ['Teen Boy','Asian Boy','Cartoon Girl','Cartoon Man']
func _ready():
 var env = WorldEnvironment.new()
 env.environment = Environment.new()
 env.environment.background_mode = Environment.BG_COLOR
 env.environment.background_color = Color('#243348')
 env.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
 env.environment.ambient_light_color = Color('#d8e7ff')
 env.environment.ambient_light_energy = 0.7
 add_child(env)
 var light = DirectionalLight3D.new()
 light.rotation_degrees = Vector3(-45,-25,0)
 light.light_energy = 1.3
 light.shadow_enabled = true
 add_child(light)
 var floor_mesh = MeshInstance3D.new()
 var box = BoxMesh.new()
 box.size = Vector3(20,0.1,12)
 floor_mesh.mesh=box
 floor_mesh.position.y = -0.05
 var mat=StandardMaterial3D.new()
 mat.albedo_color=Color('#405269')
 floor_mesh.material_override=mat
 add_child(floor_mesh)
 for i in range(4):
  var model=load('res://assets/characters/'+FILES[i]+'_walk.glb').instantiate()
  model.position.x=(i-1.5)*2.1
  add_child(model)
  var ap=model.find_children('*','AnimationPlayer',true,false)[0] as AnimationPlayer
  var chosen: StringName
  for a in ap.get_animation_list():
   if a != 'RESET': chosen=a;break
  ap.get_animation(chosen).loop_mode=Animation.LOOP_LINEAR
  ap.play(chosen)
  ap.seek(0,true)
  players.append(ap)
  print('WALK_LOADED ',FILES[i],' clip=',chosen,' length=',ap.get_animation(chosen).length)
  var label=Label3D.new()
  label.text=NAMES[i]
  label.position=Vector3(model.position.x,2.05,0)
  label.font_size=44
  label.pixel_size=0.005
  label.billboard=BaseMaterial3D.BILLBOARD_ENABLED
  add_child(label)
 camera=Camera3D.new()
 camera.position=Vector3(0,2.4,8.8)
 add_child(camera)
 camera.look_at(Vector3(0,1,0))
 camera.fov=48
 var canvas=CanvasLayer.new()
 add_child(canvas)
 var info=Label.new()
 info.text='ХОДЬБА JANE → 4 ПЕРСОНАЖА\nПробел — пауза   ← / → — поворот обзора   Esc — выход'
 info.position=Vector2(24,20)
 info.add_theme_font_size_override('font_size',22)
 canvas.add_child(info)
 if '--capture-walk' in OS.get_cmdline_user_args():capture()
func capture():
 for p in players:p.pause()
 for i in range(4):
  for p in players:p.seek(float(i)*31.0/120.0,true)
  await get_tree().process_frame
  await RenderingServer.frame_post_draw
  get_viewport().get_texture().get_image().save_png(ProjectSettings.globalize_path("res://").path_join("../previews/walk_phase_%d.png"%i))
 print('WALK_CAPTURE_OK')
 get_tree().quit()
func _unhandled_key_input(event):
 if event is InputEventKey and event.pressed and not event.echo:
  if event.keycode==KEY_ESCAPE:get_tree().quit()
  if event.keycode==KEY_SPACE:
   paused=not paused
   for p in players:
    if paused:p.pause()
    else:p.play()
func _process(delta):
 var turn=Input.get_axis('ui_left','ui_right')
 t+=turn*delta
 if turn!=0:
  camera.position=Vector3(sin(t)*8.8,2.4,cos(t)*8.8)
  camera.look_at(Vector3(0,1,0))
