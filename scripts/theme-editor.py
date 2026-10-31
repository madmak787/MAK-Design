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
