import sys

_, title, subtitle, screenshot_b64_file, out_html = sys.argv

icon_b64 = open("icon.b64").read().strip()
shot_b64 = open(screenshot_b64_file).read().strip()
tpl = open("screenshot_template.html").read()

tpl = (tpl
       .replace("__TITLE__", title)
       .replace("__SUBTITLE__", subtitle)
       .replace("__ICON_B64__", icon_b64)
       .replace("__SCREENSHOT_B64__", shot_b64))

open(out_html, "w").write(tpl)
print("wrote", out_html)
