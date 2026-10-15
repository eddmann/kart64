# Courses

[Back to Kart64](../README.md)

Editable custom courses for Kart64 and native
[SpaghettiKart](https://github.com/HarbourMasters/SpaghettiKart).
[Silverstone](silverstone/README.md) is the first.

Each course keeps its Blender projects, original textures, generators and source
data in `project/`, its build notes in `docs/`, and its compressed runtime
archive in `runtime/`. Build output is ignored by Git.

The shared editing tools are pinned in `requirements.txt` and `setup_fast64.py`,
which fetches Fast64 into `.cache/course-tools/fast64`; neither the engine nor
the addon is vendored.

A course plays in Kart64 once its archive is listed in `web/courses.json`; the
page loads it at startup and the in-game **Custom** browser offers it.
