class_name DayNight
extends Node3D
# Суточный цикл района: солнце/луна, небо, свет, туман и тонометрия.
# Полные сутки forтся DAY_LENGTH секунд реального времени.
# `night_amount` (0 — день, 1 — ночь) читают фонари и любой другой код.

const DAY_LENGTH := 480.0

var time_minutes := 600.0  # игра начинается в 10:00
var night_amount := 0.0

var sun: DirectionalLight3D
var world_environment: WorldEnvironment
var environment: Environment
var sky_material: ProceduralSkyMaterial
var star_mesh: MultiMeshInstance3D
var star_material: ShaderMaterial

func _ready() -> void:
	environment = Environment.new()
	sky_material = ProceduralSkyMaterial.new()
	var sky := Sky.new()
	sky.sky_material = sky_material
	environment.sky = sky
	environment.background_mode = Environment.BG_SKY
	environment.tonemap_mode = Environment.TONE_MAPPER_ACES
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	environment.fog_enabled = true
	environment.glow_enabled = true
	environment.glow_blend_mode = Environment.GLOW_BLEND_MODE_ADDITIVE
	world_environment = WorldEnvironment.new()
	world_environment.environment = environment
	add_child(world_environment)
	sun = DirectionalLight3D.new()
	sun.name = "SunMoon"
	sun.shadow_enabled = true
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	sun.directional_shadow_max_distance = 650.0
	add_child(sun)
	_make_stars()
	_apply()

func _process(delta: float) -> void:
	time_minutes = fposmod(time_minutes + delta * 1440.0 / DAY_LENGTH, 1440.0)
	_apply()

func clock_text() -> String:
	var m := int(time_minutes)
	return "%02d:%02d" % [m / 60, m % 60]

# Возвращает направление, в которое летит свет, и возвышение в градусах.
# t = 0 в 06:00 (восход), t = 0.5 в 18:00 (закат).
func _orbit(t: float) -> Dictionary:
	var elevation := sin(t * TAU) * deg_to_rad(62.0)
	var azimuth := t * TAU
	var shine := Vector3(cos(azimuth) * cos(elevation),
		-sin(elevation), sin(azimuth) * cos(elevation))
	return {'shine': shine, 'elevation_deg': rad_to_deg(elevation)}

func _apply() -> void:
	var t := (time_minutes - 360.0) / 1440.0
	var orbit := _orbit(t)
	var elev: float = orbit.elevation_deg
	# Четыре состояния неба и веса их смешивания по высоте солнца.
	var day_w := smoothstep(-2.0, 14.0, elev)
	var night_w := 1.0 - smoothstep(-14.0, 2.0, elev)
	var transition := (1.0 - day_w) * (1.0 - night_w)
	var golden_w := transition * smoothstep(-8.0, 8.0, elev)
	var dusk_w := transition * (1.0 - smoothstep(-8.0, 8.0, elev))
	var w := PackedFloat32Array([day_w, golden_w, dusk_w, night_w])
	night_amount = 1.0 - smoothstep(-6.0, 6.0, elev)
	# Небо, земля, свет, туман, экспозиция, свечение.
	var sky_top := _mix_color(w, [Color("4a7fb5"), Color("5d7fa8"), Color("333a6e"), Color("060b1c")])
	var horizon := _mix_color(w, [Color("d3e2e8"), Color("f6c089"), Color("e08a58"), Color("182338")])
	var ground := _mix_color(w, [Color("b9c3c6"), Color("c9b2a2"), Color("6f5f5c"), Color("10151f")])
	var ambient := _mix_color(w, [Color("d4e3ef"), Color("f2d8c2"), Color("c8a28a"), Color("8aa2cc")])
	var ambient_e := _mix(w, [0.55, 0.42, 0.24, 0.15])
	var light_color := _mix_color(w, [Color("fff4e0"), Color("ffc99a"), Color("ff9e6a"), Color("a9bedb")])
	var light_e := _mix(w, [1.05, 0.95, 0.42, 0.16])
	var fog_color := _mix_color(w, [Color("c4d4dc"), Color("dcc2a8"), Color("7d6c7c"), Color("0e1420")])
	var fog_d := _mix(w, [0.0011, 0.0015, 0.0021, 0.0028])
	var exposure := _mix(w, [1.0, 0.98, 0.92, 0.9])
	var glow := _mix(w, [0.10, 0.16, 0.22, 0.34])
	sky_material.sky_top_color = sky_top
	sky_material.sky_horizon_color = horizon
	sky_material.ground_horizon_color = ground
	sky_material.ground_bottom_color = ground.darkened(0.35)
	star_material.set_shader_parameter("star_alpha", night_w * 0.95)
	environment.ambient_light_color = ambient
	environment.ambient_light_energy = ambient_e
	environment.fog_light_color = fog_color
	environment.fog_light_energy = 0.18
	environment.fog_density = fog_d
	environment.tonemap_exposure = exposure
	environment.glow_intensity = glow
	# Ночью в освещении участвует «луна» — та же орбита со смещением на сутки/2.
	var light_t := t if elev >= 0.0 else fposmod(t + 0.5, 1.0)
	var shine: Vector3 = _orbit(light_t).shine
	sun.rotation = _rotation_from_shine(shine)
	sun.light_color = light_color
	sun.light_energy = light_e

func _mix(w: PackedFloat32Array, values: Array) -> float:
	var v := 0.0
	for i in values.size():
		v += values[i] * w[i]
	return v

func _mix_color(w: PackedFloat32Array, colors: Array) -> Color:
	var c := Color.BLACK
	for i in colors.size():
		c.r += colors[i].r * w[i]
		c.g += colors[i].g * w[i]
		c.b += colors[i].b * w[i]
	c.a = 1.0
	return c

# Сфера радиуса ~1900 м с мелкими светящимися точками; видна только ночью,
# туман на неё не действует (render_mode fog_disabled).
func _make_stars() -> void:
	var code := "shader_type spatial;\n"
	code += "render_mode unshaded, fog_disabled, cull_disabled;\n"
	code += "uniform float star_alpha : hint_range(0.0, 1.0) = 0.0;\n"
	code += "uniform vec3 star_color : source_color = vec3(0.92, 0.94, 1.0);\n"
	code += "varying float v_brightness;\n"
	code += "varying float v_phase;\n"
	code += "varying float v_offset;\n"
	code += "void vertex() {\n"
	code += "\tv_brightness = INSTANCE_CUSTOM.x;\n"
	code += "\tv_phase = 0.6 + INSTANCE_CUSTOM.y;\n"
	code += "\tv_offset = INSTANCE_CUSTOM.z;\n"
	code += "}\n"
	code += "void fragment() {\n"
	code += "\tfloat facing = max(dot(NORMAL, VIEW), 0.0);\n"
	code += "\tfloat dot2 = pow(facing, 16.0);\n"
	code += "\tfloat tw = 0.78 + 0.22 * sin(TIME * v_phase + v_offset);\n"
	code += "\tALBEDO = star_color * dot2 * tw * v_brightness;\n"
	code += "\tALPHA = star_alpha * dot2;\n"
	code += "}\n"
	star_material = ShaderMaterial.new()
	star_material.shader = Shader.new()
	star_material.shader.code = code
	star_material.set_shader_parameter("star_alpha", 0.0)
	var geometry := SphereMesh.new()
	geometry.radius = 1.0
	geometry.height = 2.0
	geometry.radial_segments = 6
	geometry.rings = 3
	geometry.material = star_material
	var multi := MultiMesh.new()
	multi.transform_format = MultiMesh.TRANSFORM_3D
	multi.mesh = geometry
	multi.use_custom_data = true
	multi.instance_count = 260
	var rnd := RandomNumberGenerator.new()
	rnd.seed = 42
	for i in 260:
		var dir := Vector3(rnd.randf_range(-1.0, 1.0), rnd.randf_range(0.06, 1.0), rnd.randf_range(-1.0, 1.0)).normalized()
		var scale := rnd.randf_range(1.6, 4.5)
		multi.set_instance_transform(i, Transform3D(Basis.IDENTITY, dir * 1900.0).scaled(Vector3.ONE * scale))
		multi.set_instance_custom_data(i, Color(rnd.randf_range(0.5, 1.0), rnd.randf_range(0.3, 1.6), rnd.randf_range(0.0, TAU), 1.0))
	star_mesh = MultiMeshInstance3D.new()
	star_mesh.name = "Stars"
	star_mesh.multimesh = multi
	star_mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(star_mesh)

# Поворот узла так, чтобы его -Z (направление света) совпал с `shine`.
func _rotation_from_shine(shine: Vector3) -> Vector3:
	var yaw := atan2(shine.x, shine.z)
	var pitch := asin(clampf(shine.y, -1.0, 1.0))
	return Vector3(pitch, yaw, 0.0)
