"""Apply MAK's floral UI tokens to a pinned FigCraft source checkout. Never alter document paint."""
from pathlib import Path
import re
import sys
root=Path(sys.argv[1])
p=root/'crates/ui-egui/src/theme.rs'
s=p.read_text()
def color(hex_value):
    return 'Color32::from_rgb('+', '.join('0x'+hex_value[i:i+2].upper() for i in (0,2,4))+')'
for name,value in {'BRAND':'f060a6','ACCENT':'ad2367','ACCENT_ON':'40152f'}.items():
    s,n=re.subn(r'(pub const '+name+r': Color32 = )Color32::from_rgb\([^\n]+\);',lambda m:m[1]+color(value)+';',s)
    if n!=1:raise SystemExit('Unexpected upstream constant: '+name)
light={'bg':'fffafb','panel':'fffafb','canvas':'f5edf4','border':'ead9e5','border_strong':'d8b9d0','text':'43233e','text_secondary':'806378','text_tertiary':'8f7287','icon':'43233e','icon_secondary':'806378','hover':'f6e9f2','pressed':'f2d7e9','field':'f8eff5','field_hover_border':'ce9fbe','accent_hover':'d7448c','accent_text':'98215b','selected_row':'f6dbea','selected_row_child':'fcecf5','component_row':'f0e3fb','tab_bar':'f2e6ef','tab_active':'fffafb','menu':'43233e','menu_hover':'ad2367','menu_dim':'c4a4ba','focus':'98215b'}
dark={'bg':'29262d','panel':'29262d','canvas':'201c24','border':'49404d','border_strong':'62516a','text':'fff5fc','text_secondary':'cbb6c6','text_tertiary':'ae94a6','icon':'fff5fc','icon_secondary':'cbb6c6','hover':'3b2e3d','pressed':'4b3348','field':'382e3b','field_hover_border':'74556e','accent_hover':'ff8cc3','accent_text':'ff8cc3','selected_row':'50243f','selected_row_child':'422137','component_row':'412e54','tab_bar':'201c24','tab_active':'342a37','menu':'2e2231','menu_hover':'ad2367','menu_dim':'b998af','focus':'f060a6'}
for name,palette,next_marker in [('light',light,'    pub fn dark()'),('dark',dark,'    pub fn get(')]:
    start=s.index('    pub fn '+name+'()');end=s.index(next_marker,start)
    block=s[start:end]
    for key,value in palette.items():
        block,n=re.subn(r'(?m)^(\s+'+key+r': )[^\n]+,\s*$',lambda m:m[1]+color(value)+',',block)
        if n!=1:raise SystemExit('Unexpected upstream theme field: '+name+'.'+key)
    s=s[:start]+block+s[end:]
p.write_text(s)
print('MAK floral light/dark UI themes applied. Design document colours are unchanged.')
# Original vector blossom drawn from primitives; no external product artwork.
s=p.read_text().replace('"Fig".into(), font.clone()', '"MAK".into(), font.clone()').replace('"Craft", font, t.accent_text', '" Design", font, t.accent_text')
start=s.index('pub fn paint_app_icon(')
end=s.index('\npub fn regular(',start)
s=s[:start]+'''pub fn paint_app_icon(ui: &egui::Ui, rect: egui::Rect) {
    let scale = rect.width().min(rect.height()) / 80.0;
    let center = rect.center();
    let colors = [
        Color32::from_rgb(0xF4, 0x3E, 0x87),
        Color32::from_rgb(0xFF, 0x85, 0x55),
        Color32::from_rgb(0xFF, 0xBC, 0x42),
        Color32::from_rgb(0xF6, 0x65, 0xA5),
        Color32::from_rgb(0xA6, 0x70, 0xE8),
        Color32::from_rgb(0xD4, 0x41, 0xA0),
    ];
    for (index, color) in colors.into_iter().enumerate() {
        let angle = index as f32 * std::f32::consts::TAU / 6.0;
        let (sin, cos) = angle.sin_cos();
        let points = (0..24).map(|step| {
            let t = step as f32 * std::f32::consts::TAU / 24.0;
            let x = 12.0 * t.cos();
            let y = -20.0 + 19.0 * t.sin();
            center + egui::vec2((x * cos - y * sin) * scale, (x * sin + y * cos) * scale)
        }).collect();
        ui.painter().add(egui::Shape::convex_polygon(points, color, Stroke::NONE));
    }
    ui.painter().circle_filled(center, 15.0 * scale, Color32::from_rgb(0x49, 0x20, 0x47));
    ui.painter().text(center, egui::Align2::CENTER_CENTER, "M", semibold(19.0 * scale), Color32::from_rgb(0xFF, 0xF9, 0xE8));
}
''' + s[end:]
p.write_text(s)
about=root/'crates/ui-egui/src/dialogs.rs'
s=about.read_text().replace('Interface design and prototyping. A free, open-source, clean-room design tool written from scratch in Rust, part of the ArtCraft Crafting Apps.', 'MAK Design personal workspace. Based on the open-source FigCraft engine by the ArtCraft team and community.').replace('Dual-licensed MIT OR Apache-2.0. Made by the ArtCraft team and community.', 'FigCraft engine: MIT OR Apache-2.0. MAK Design customizations by madmak787.')
about.write_text(s)
index=root/'apps/figcraft-web/index.html'
index.write_text(index.read_text().replace('<title>FigCraft</title>','<title>MAK Design editor</title>').replace('Loading FigCraft&hellip;', 'Loading MAK Design&hellip;'))
