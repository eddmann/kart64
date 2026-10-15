"""Make the exported materials independent of the game's previous RDP state.

Fast64 omits commands equal to its scene defaults. The native game can enter
custom courses with different defaults, so each material establishes its state.
"""
import xml.etree.ElementTree as ET


def stabilize_export(track_dir):
    count = 0
    for path in sorted(track_dir.glob('mat_*')):
        if path.name.startswith('mat_revert_'):
            continue
        original = ET.parse(path).getroot()
        texture = original.find('SetTextureImage')
        cutout = texture is not None and texture.get('Path').rsplit('/', 1)[-1] in ('fence', 'cloud', 'spectators')
        root = ET.Element('DisplayList', Version='0')
        ET.SubElement(root, 'PipeSync')
        ET.SubElement(root, 'ClearGeometryMode', G_LIGHTING='1', G_FOG='1',
                      G_CULL_BACK='1', G_CULL_FRONT='1', G_TEXTURE_GEN='1', G_TEXTURE_GEN_LINEAR='1')
        ET.SubElement(root, 'SetGeometryMode', G_SHADE='1', G_SHADING_SMOOTH='1', G_ZBUFFER='1')
        ET.SubElement(root, 'SetCycleType', G_CYC_1CYCLE='1')
        mode = 'G_RM_AA_ZB_TEX_EDGE' if cutout else 'G_RM_AA_ZB_OPA_SURF'
        ET.SubElement(root, 'SetRenderMode', Mode1=mode, Mode2=mode+'2')
        for command in original:
            if command.tag in ('PipeSync', 'ClearGeometryMode', 'SetGeometryMode', 'SetCycleType', 'SetRenderMode'):
                continue
            if command.tag == 'Texture' and texture is None:
                command.set('On', '0')
            if command.tag == 'SetCombineLERP':
                for key in ('Ad0', 'Ad1'):
                    if command.get(key) == 'G_ACMUX_1':
                        command.set(key, 'G_ACMUX_SHADE')
            root.append(command)
        ET.indent(root, space='\t')
        path.write_bytes(ET.tostring(root)+b'\n')
        count += 1
    return count
