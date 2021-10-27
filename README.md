# BoxToolBox

BoxToolBox is simple python application build around openCV library.
It is not full featured application to guide you trought the whole process.
It is missing piece in your toolchain between Lightroom and Photoshop.
You still need to take you box pictures as straight as possible with
the same camera settings and pre-process them to match the lighting.

**It will help you to**
* correct perspective of the source photos
* quickly test the layout and arrangement
* place photos to correct location
* generate grid to recolor or use as mask to hide the seams

**It will not**
* unify brightness and colors of source photos
* magicaly correct photos taken from bad perspective
* assemble final picture

## How to install (Linux)
Just clone or download this repository and run the main script.
You will also need opencv installed
```bash
pip install opencv-python
git clone https://github.com/fhorinek/BoxToolBox.git
cd BoxToolBox
python BoxToolBox.py
```
## How to install (Windows)
Just download and execute pre build exe file.

## How to use it
There is quick start video on youtube.

### Perspective editor
One is window act as input for defining box corners and second window show transformation previu. 
Controls on the second window sets transformed image width and height. The resolution for the final picture will be
`Width * Grid W` x `Height * Grid H`. Margin define how much of the image will be preserved around the defined box.
Preview scale will define size of the temporary pictures used in layout editor. Smaller scale will make the editor go faster,
larger scale will provide better quality.

![norm](https://user-images.githubusercontent.com/9072684/139096784-211a36b4-ba3d-4d45-8586-e730aef331dd.png)

**Controls:**
* `Mouse wheel` - zoom
* `Left button` - Pan
* `Middle button` - Select point
* `N` key and `M` key - Open previous and next image
* `Q` - Close editor

*Normally you only need to define transformation box for the first photo. The transformation will be applied to all following pictures. If you bump the camera during the session you can find the first image that is affected and redefine the transformation box. All following images will use that correction.*


### Layout editor
You can use this window to compose the final image. Here you can change geometry for final image. Set scaling and spacing for the images. You can use `Transparent spacer` to define very precise scale.

![layout](https://user-images.githubusercontent.com/9072684/139096747-427747e8-3880-4a9a-a025-ccdf9060ad49.png)

**Controls:**

* `Mouse wheel` - zoom
* `Left button` - Pan
* `Drag picture` - Swap images
* `N` key and `M` key - set previous and next image
* `E` key - Open perspective editor for image
* `C` key - Toggle Crop or Full flag for image
* `S` key - Show full image with marker lines
* `Q` key - Close editor
* `Render` - Show final image in full resolution
* `Output` - Reneder final image in layers

Use different slots to experiment with mulitple layous and geometries.

### Output
Output for the image will consinst of multiple images placed inside directory `slot_n`.
Photos in images will be placed to correct location on transparent background. You will also find the generated grid image.
Import thease images as layers to any photo editor to compose final image.

![gimp](https://user-images.githubusercontent.com/9072684/139096725-65a175be-cd47-4d14-b4c2-f7e1f4f3cdca.png)

## Disclamer
This tool is my hobby project, done in my free time for my personal use.
However I think that other people might found it usefull so I made extre steps to make it more friendly and easier to install.
If you found a bug or want something to add, feel free to open an issue. Pull requests are also welcomed!

If you found it usefull and want to thank me, you can [buy me a bear :-)](https://paypal.me/horinek)
