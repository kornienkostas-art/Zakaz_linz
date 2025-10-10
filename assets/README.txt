Place your brand assets here.

Expected files:
- logo.png — used in previews and can be used in the app header.
  Recommendations: PNG, transparent background, around 128x128 or 256x256.

- app.ico — Windows application icon for the EXE.
  Recommendations: multi-size ICO containing at least 256x256, 128x128, 64x64, 32x32, 16x16.

How to create app.ico from your PNG:
1) Online converters:
   - https://cloudconvert.com/png-to-ico
   - https://icoconvert.com/

2) In GIMP or Photoshop: export as Windows Icon (.ico) with multiple sizes.

3) PowerShell (requires ImageMagick installed and in PATH):
   magick convert logo.png -define icon:auto-resize=256,128,64,48,32,16 app.ico

Build script:
- scripts\build_exe.bat automatically uses app.ico if it exists.
- It also bundles assets\logo.png into the EXE (as data) if present.