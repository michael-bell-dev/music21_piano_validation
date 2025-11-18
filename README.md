To run this program, python 3.9+ or higher is required, as well as the Music21 library. Install using pip: pip install music21. To view the .musicxml output files, MuseScore should be installed.

Use the following format to run the program:  
python music21_piano_validation.py *(file_path to .xml, .mxl, or .musicxml file)* (*output_file name without extension*)  
For example:  
python music21_piano_validation.py examples/Fra_Missa_Brevis_Mozart.mxl mozart_combined_and_validated

This program takes an existing score and determines if it is possible to play the piece on the piano without compromising the original composition.  It combines all parts/staffs into a single part, then algorithmically splits it into plausible left and right hand parts, completing various checks to ensure playability.  If a certain chord is impossible, it will be highlighted in red.  The output file will be in .musicxml format and appear in the same directory as the music21_piano_validation.py file.
