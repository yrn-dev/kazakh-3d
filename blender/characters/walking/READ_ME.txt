Ходьба Everyday Jane перенесена на Teen Boy, Asian Boy, Cartoon Girl и Cartoon Man.

Открыть просмотр: ./run-walk (Linux/macOS), run-walk.bat (Windows)
Пробел — пауза; стрелки влево/вправо — поворот камеры; Esc — закрыть.

Blender: файлы *_walk.blend в этой папке, действие Walk, кадры 1–32 при 30 fps.
Godot: kazakh-3d/godot/assets/characters/*_walk.glb, клип Walk, цикл около 1.033 секунды.
Это ходьба на месте: перемещение NPC по карте подключается отдельно.

Рабочие копии нормализованы по росту, текстуры сохранены. Скелет экспорта содержит
деформирующие кости с запечённой анимацией; оригинальные риги остаются в папке выше.
На этих копиях нет исходных управляющих IK-контроллеров и лицевых shape keys.
Для дальнейшего редактирования лиц/ригов используйте оригинальные .blend.

Анимация: Everyday Jane, автор XRProfXR, CC BY 4.0.
https://sketchfab.com/3d-models/everyday-jane-casual-modern-woman-rigged-4c32c738e0074637beac26bbe670aca3
Авторство каждой модели: kazakh-3d/CREDITS.txt.
Изменения: перенос анимации, запекание, нормализация роста и контакта с полом.

Воспроизвести подготовку: Blender --background --python scripts/retarget_walk.py,
затем python3 scripts/finalize_walk_glb.py; проверка scripts/check_walk.py через Blender.
