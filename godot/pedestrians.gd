extends Node3D

const MODELS = [
 'res://assets/characters/teen-boy_walk.glb',
 'res://assets/characters/cartoon_asian__boy_walk.glb',
 'res://assets/characters/free_stylized_cartoon_girl_rigged_character_walk.glb',
 'res://assets/characters/free_cartoon_game_man_character_rigged_walk.glb',
 'res://assets/characters/everyday_jane_walk.glb']
var walkers: Array[Dictionary] = []
var routes: Array[Dictionary] = []
var camera_start := Vector3.ZERO
var camera_yaw := 0.0
var observer: Node3D
var inspection_index := -1

func _ready() -> void:
 var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string('res://pedestrian_routes.json'))
 camera_start = vec(data.camera_start)
 camera_yaw = data.camera_yaw
 var packed: Array[PackedScene] = []
 for path in MODELS: packed.append(load(path) as PackedScene)
 for definition in data.routes:
  var points := PackedVector3Array()
  var distances := PackedFloat32Array([0.0])
  for point in definition.points: points.append(vec(point))
  for i in range(1, points.size()): distances.append(distances[-1] + points[i].distance_to(points[i-1]))
  var route := {'name':definition.name, 'points':points, 'distances':distances, 'length':distances[-1]}
  routes.append(route)
  var route_id := routes.size()-1
  for j in range(3):
   var id := walkers.size()
   var model_id := id % MODELS.size()
   var root := Node3D.new()
   root.name='Pedestrian_%02d'%id
   add_child(root)
   var visual := packed[model_id].instantiate() as Node3D
   root.add_child(visual)
   for mesh in visual.find_children('*','MeshInstance3D',true,false):
    mesh.visibility_range_end=115.0
    mesh.visibility_range_end_margin=12.0
   var ap := visual.find_children('*','AnimationPlayer',true,false)[0] as AnimationPlayer
   var clip := ap.get_animation('Walk')
   clip.loop_mode=Animation.LOOP_LINEAR
   ap.play('Walk')
   ap.seek(float(id)*0.173,true)
   var body := AnimatableBody3D.new()
   body.name='PedestrianBody'
   body.sync_to_physics=false
   body.collision_layer=2
   body.collision_mask=0
   var shape := CollisionShape3D.new()
   var capsule := CapsuleShape3D.new()
   capsule.radius=0.28
   capsule.height=1.15 if model_id==1 else 1.65
   shape.shape=capsule
   shape.position.y=capsule.height*0.5
   body.add_child(shape)
   root.add_child(body)
   var start := 5.0+float(j)*8.0 if route_id==0 else float(j)*float(route.length)/3.0
   var pace := randf_range(1.0,1.4) if model_id==1 else randf_range(0.95,1.35)
   var walker := {'node':root,'animation':ap,'route':route_id,'distance':start,'speed':pace,
    'stride':0.63 if model_id==1 else 0.95,'travelled':0.0,'model':model_id,
    'pause_left':0.0,'next_pause':randf_range(12.0,30.0),'look_yaw':0.0}
   var at := sample_route(route,start)
   root.position=at.position
   root.rotation.y=atan2(at.direction.x,at.direction.z)
   walkers.append(walker)
 print('PEDESTRIANS_READY | count=',walkers.size(),' | sidewalk routes=',routes.size())

func vec(value: Array) -> Vector3:
 return Vector3(value[0],value[1],value[2])

func sample_route(route: Dictionary, distance: float) -> Dictionary:
 distance=fposmod(distance,float(route.length))
 var cumulative: PackedFloat32Array=route.distances
 var points: PackedVector3Array=route.points
 var lo := 0
 var hi := cumulative.size()-1
 while hi-lo>1:
  var mid := (lo+hi)/2
  if cumulative[mid]<=distance:lo=mid
  else:hi=mid
 var span := cumulative[hi]-cumulative[lo]
 var weight := (distance-cumulative[lo])/maxf(span,0.0001)
 var direction := points[hi]-points[lo]
 direction.y=0
 return {'position':points[lo].lerp(points[hi],weight),'direction':direction.normalized()}

func _physics_process(delta: float) -> void:
 for walker in walkers:
  var node: Node3D=walker.node
  var route: Dictionary=routes[walker.route]
  var animation: AnimationPlayer=walker.animation
  # Остановка-оглядка: стоит, медленно поворачивает голову, потом идёт дальше.
  if walker.pause_left>0.0:
   walker.pause_left-=delta
   animation.speed_scale=0.0
   node.rotation.y=lerp_angle(node.rotation.y,walker.look_yaw,1.0-exp(-1.5*delta))
   continue
  var next := sample_route(route,walker.distance+walker.speed*delta)
  var blocked := false
  for other in walkers:
   if other.node==node:continue
   var separation: Vector3=other.node.position-node.position
   separation.y=0
   if separation.length()<0.83 and separation.dot(next.direction)>0.08:
    blocked=true
    break
  if is_instance_valid(observer):
   var difference: Vector3=observer.global_position-node.global_position
   if absf(difference.y)<2.2:
    difference.y=0
    if difference.length()<0.85 and difference.dot(next.direction)>0.03:blocked=true
  var nearby := not is_instance_valid(observer) or node.global_position.distance_to(observer.global_position)<115
  if blocked:
   animation.speed_scale=0.0
   continue
  # Планируем следующую остановку (первые секунды все идут — нужны для проверки).
  walker.next_pause-=delta
  if walker.next_pause<=0.0:
   walker.pause_left=randf_range(1.0,4.5)
   walker.next_pause=randf_range(9.0,30.0)
   walker.look_yaw=node.rotation.y+randf_range(-1.2,1.2)
   animation.speed_scale=0.0
   continue
  walker.distance=fposmod(walker.distance+walker.speed*delta,float(route.length))
  walker.travelled+=walker.speed*delta
  node.position=next.position
  node.rotation.y=lerp_angle(node.rotation.y,atan2(next.direction.x,next.direction.z),1-exp(-9.0*delta))
  animation.speed_scale=walker.speed/walker.stride if nearby else 0.0

func inspection_view() -> Dictionary:
 inspection_index=(inspection_index+1)%walkers.size()
 var walker: Dictionary=walkers[inspection_index]
 var route: Dictionary=routes[walker.route]
 var behind := sample_route(route,walker.distance-4.5)
 var at := sample_route(route,walker.distance)
 return {'position':behind.position+Vector3.UP*1.8,'target':at.position+Vector3.UP*1.15}
