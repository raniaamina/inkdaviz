# Inkdaviz - Inkscape Extension

Inkdaviz is an Inkscape extension that generates SVG chart from CSV data directly in Inkscape.. 

## Dependencies
This extension use matplot library to generate chart. Make sure this package already installed in your system:
- python3-matplotlib
- python3-tinycss2

## Installation
1. Download the files `inkdaviz.py` and `inkdaviz.inx`.
2. Copy both files to the `extensions` directory in Inkscape's configuration folder:
   - **Linux**: `~/.config/inkscape/extensions/`
   - **Windows**: `%APPDATA%\inkscape\extensions\`
3. Restart Inkscape.


## Usage
1. Open extension the menu **Extensions > Generate > Inkdaviz..
3. Select CSV file and fill the fiels. See help tab to get more info for each field.
4. Click **Apply**.

## Notes
- You need to ungroup generated chart to make the object movable.


## Disclaimer 
We don't guarantee anything about this tool/extension, so please use it at your own risk. We can't give 24/7 support if you have a problem when using Magibox. 

If you feel that this tool has helped you to create, feel free to donate a cup of coffee on the [Support Dev](https://saweria.co/raniaamina) :")
