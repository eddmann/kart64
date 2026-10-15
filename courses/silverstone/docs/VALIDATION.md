# Validation

[Back to Silverstone](../README.md)

## Every build

`build.py` stops on a failed check. It checks:

- resource references, archive integrity, coordinate/UV bounds and texture/TMEM limits
- case-insensitive uniqueness of texture names, filenames and resource paths
- waypoint continuity, road boundaries and item-box height
- mesh faces, vertex colours, packed images and linked dependencies
- scenery clearance from the GP and pit corridors
- HD texture dimensions, hashes and replacement paths

Results go under the ignored `build/`, with the archive checksum in
`build/build-info.json`. ZIP metadata can change an archive's hash, so compare
resource content when checking a rebuild.

The 1.9 course has 71,001 triangles, within the 72,000 budget. Its scenery
check sampled 126,620 points with no intrusions into the racing corridors.
Against 1.8, the 33 driving resources (road, kerbs, barriers, pit asphalt, AI
paths, items and minimap) are byte-identical, and all 15 new scenery sections
are non-collidable.

## Native SpaghettiKart

Tested on `aedcf9ada627f4f8e861f12d8b48f587de521e6b`:

- 1.8 (2026-10-04): with ordinary keyboard controls, Mario took the pit
  shortcut, the GP route, then the pit shortcut again. Every crossing counted
  a lap, and all seven CPU rivals finished via the GP route.
- 1.9 (2026-10-06): Mario completed three AI-assisted GP laps, with every
  sample on asphalt and no rescues or spinouts. The gallery lap comes from
  this run.

## Kart64

`make test/course` drives Silverstone through the game's own menus in Chromium,
with rendering on. It covers Custom from the cup row, a standalone three-lap
Grand Prix against seven CPU rivals, Change Course, and a Time Trial that saves
only to the course's own EEPROM.

## Still to check

- a complete rendered race on a real phone
- pit-shortcut driving and recovery cases in the browser
- human shortcut timing and balance, Lakitu towing, and unusual collision or camera cases
- mirror mode; multiplayer and cups are not offered for custom courses
