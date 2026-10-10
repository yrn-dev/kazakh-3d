class_name StreetLights
extends Node3D
# Уличные фонари вдоль проезжих улиц (маршруты, чьё название содержит
# «sidewalk»). Ставятся в стороне от тротуара, без коллизий (декор),
# зажигаются на закате по `day_night.night_amount`.

const LAMP_INTERVAL := 20.0
const SIDE_OFFSET := 0.55
const MAX_LAMPS := 16
const MIN_SPACING := 10.0

var day_night: Node3D

var _lights: Array[OmniLight3D] = []
var _bulb_materials: Array[StandardMaterial3D] = []

func _ready() -> void:
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string('res://pedestrian_routes.json'))
	if data == null:
		return
	for definition in data.routes:
		if _lights.size() >= MAX_LAMPS:
			break
		var name: String = definition.name
		if not name.contains('sidewalk'):
			continue
		var points := PackedVector3Array()
		var distances := PackedFloat32Array([0.0])
		for point in definition.points:
			points.append(Vector3(point[0], point[1], point[2]))
		for i in range(1, points.size()):
			distances.append(distances[distances.size() - 1] + points[i].distance_to(points[i - 1]))
		_place_lamps(points, distances)

func _place_lamps(points: PackedVector3Array, distances: PackedFloat32Array) -> void:
	var total: float = distances[distances.size() - 1]
	var next_at := 6.0
	var last := Vector3.INF
	for s in range(6, int(total)):
		if s < next_at or _lights.size() >= MAX_LAMPS:
			continue
		var at := _sample(points, distances, float(s))
		# «Вправо» от направления движения — к проезжей части.
		var side: Vector3 = at.direction.cross(Vector3.UP)
		var pos: Vector3 = at.position + side * SIDE_OFFSET
		if last != Vector3.INF and pos.distance_to(last) < MIN_SPACING:
			continue
		last = pos
		next_at = float(s) + LAMP_INTERVAL
		_make_lamp(pos)

func _sample(points: PackedVector3Array, distances: PackedFloat32Array, distance: float) -> Dictionary:
	var d := fposmod(distance, float(distances[distances.size() - 1]))
	var lo := 0
	var hi := distances.size() - 1
	while hi - lo > 1:
		var mid := (lo + hi) / 2
		if distances[mid] <= d:
			lo = mid
		else:
			hi = mid
	var span := distances[hi] - distances[lo]
	var weight := (d - distances[lo]) / maxf(span, 0.0001)
	var direction := points[hi] - points[lo]
	direction.y = 0
	return {'position': points[lo].lerp(points[hi], weight), 'direction': direction.normalized()}

func _make_lamp(pos: Vector3) -> void:
	var lamp := Node3D.new()
	lamp.name = 'StreetLamp_%d' % (_lights.size() + 1)
	lamp.position = pos
	add_child(lamp)
	var pole_material := StandardMaterial3D.new()
	pole_material.albedo_color = Color("2c3138")
	pole_material.roughness = 0.85
	pole_material.metallic = 0.6
	var pole := MeshInstance3D.new()
	var pole_mesh := CylinderMesh.new()
	pole_mesh.top_radius = 0.05
	pole_mesh.bottom_radius = 0.07
	pole_mesh.height = 3.1
	pole_mesh.radial_segments = 8
	pole_mesh.rings = 1
	pole.mesh = pole_mesh
	pole.material_override = pole_material
	pole.position = Vector3(0, 1.55, 0)
	lamp.add_child(pole)
	var bulb_material := StandardMaterial3D.new()
	bulb_material.albedo_color = Color("6b6257")
	bulb_material.emission = Color("ffc37a")
	bulb_material.emission_energy = 0.0
	var bulb := MeshInstance3D.new()
	var bulb_mesh := SphereMesh.new()
	bulb_mesh.radius = 0.09
	bulb_mesh.height = 0.18
	bulb_mesh.radial_segments = 10
	bulb_mesh.rings = 6
	bulb.mesh = bulb_mesh
	bulb.material_override = bulb_material
	bulb.position = Vector3(0, 3.12, 0)
	lamp.add_child(bulb)
	var light := OmniLight3D.new()
	light.light_color = Color("ffc98a")
	light.light_energy = 0.0
	light.omni_range = 9.0
	light.omni_attenuation = 1.7
	light.position = Vector3(0, 3.05, 0)
	lamp.add_child(light)
	_lights.append(light)
	_bulb_materials.append(bulb_material)

func _process(_delta: float) -> void:
	if day_night == null:
		return
	var n: float = day_night.night_amount
	for i in _lights.size():
		_lights[i].light_energy = 3.0 * n
		_bulb_materials[i].emission_energy = 2.6 * n
