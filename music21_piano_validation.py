from sys import argv, platform
from music21 import *

MAX_INTERVAL = 16  # maximum interval in semitones between the lowest and highest note one hand can play
COLOR_ERROR = '#ED1111'
COLOR_CORRECT = '#000000'

# copies a list of notes in replacement of copy.deepcopy()
# returns: new_notes
def copy_notes(notes):
    new_notes = []
    for n in notes:
        new_note = note.Note(n.pitch)
        new_note.quarterLength = n.quarterLength
        new_note.tie = n.tie
        new_note.style.color = n.style.color
        new_notes.append(new_note)
    return new_notes

# colors notes red to indicate they are impossible to play
# colors notes black to indicate they are possible to play
def color_notes(left_hand_notes, right_hand_notes, color):
    for note_object in left_hand_notes:
        note_object.style.color = color
    for note_object in right_hand_notes:
        note_object.style.color = color

# checks if notes are possible to play based on the notes and their spacing
# I am aware that this function is very much based on the size of my own hands.
# Future versions should allow the user to input their own hand size parameters.
# Also this should probably be refactored to do one hand at a time; I tried once but I broke it
# returns: left_possible, right_possible, left_tie_issue, right_tie_issue
def check_spacing(left_hand_notes, right_hand_notes, last_left_notes, last_right_notes):
    
    # LEFT HAND

    left_possible = True
    left_index_list = []
    left_tie_issue = None

    # check if a note played in the left hand is tied from a note played in the right hand
    for note_object in left_hand_notes:
        if note_object.tie is not None and (note_object.tie.type == 'continue' or note_object.tie.type == 'stop'):
            for lastNote in last_right_notes:
                if note_object.pitch == lastNote.pitch:
                    left_possible = False
                    left_tie_issue = note_object.pitch

    if left_possible and len(left_hand_notes) > 0:
        left_index_list.append(0)

        # if two notes can be played by the same finger, group them together as a single index
        # thumb can play consecutive black or white keys, other fingers just white
        i = 1
        while i < len(left_hand_notes):
            if (abs(left_hand_notes[i].pitch.midi - left_hand_notes[i - 1].pitch.midi) < 3):
                if (0 == left_hand_notes[i].pitch.alter == left_hand_notes[i - 1].pitch.alter) or (i == len(left_hand_notes) - 2 and left_hand_notes[i].pitch.alter == left_hand_notes[i + 1].pitch.alter):
                    i += 1
            left_index_list.append(i)
            i += 1
        if len(left_hand_notes) == left_index_list[-1]:
            left_index_list = left_index_list[:-1]

        # check if there are too many fingers
        if(len(left_index_list) > 5):
            left_possible = False
        # check if second and fourth finger are too far apart
        elif(len(left_index_list) > 3) and (abs(left_hand_notes[left_index_list[1]].pitch.midi - left_hand_notes[left_index_list[-2]].pitch.midi) > 8):
            left_possible = False
        # check if pinky is too far away from other fingers
        else:
            for i in range(1, len(left_index_list)):
                if i > 1 and i != len(left_index_list) - 1:
                    if abs(left_hand_notes[0].pitch.midi - left_hand_notes[left_index_list[i]].pitch.midi) >= ((5 - len(left_index_list)) + i) * 4:
                        left_possible = False
                        break
                else:
                    if abs(left_hand_notes[0].pitch.midi - left_hand_notes[left_index_list[i]].pitch.midi) > ((5 - len(left_index_list)) + i) * 4:
                        left_possible = False
                        break


    # RIGHT HAND
    
    right_possible = True
    right_index_list = []
    
    # check if a note played in the right hand is tied from a note played in the left hand
    for note_object in right_hand_notes:
        if note_object.tie is not None and (note_object.tie.type == 'continue' or note_object.tie.type == 'stop'):
            for lastNote in last_left_notes:
                if note_object.pitch == lastNote.pitch:
                    return left_possible, False, left_tie_issue, note_object.pitch

    # if two notes can be played by the same finger, group them together as a single index
    # thumb can play consecutive black or white keys, other fingers just white
    i = 0
    while i < len(right_hand_notes) - 1:
        right_index_list.append(i)
        if (abs(right_hand_notes[i].pitch.midi - right_hand_notes[i + 1].pitch.midi) < 3):
            if (0 == right_hand_notes[i].pitch.alter == right_hand_notes[i + 1].pitch.alter) or (i == 0 and right_hand_notes[i].pitch.alter == right_hand_notes[i + 1].pitch.alter):
                i += 1
        i += 1
    # add last index and remove second to last if it was grouped with the last
    if len(right_index_list) > 0 and right_index_list[-1] == i - 1:
        right_index_list.pop()
    right_index_list.append(len(right_hand_notes) - 1)

    # check if there are too many fingers
    if(len(right_index_list) > 5):
        right_possible = False
    # check if second and fourth finger are too far apart
    elif(len(right_index_list) > 3) and (abs(right_hand_notes[right_index_list[1]].pitch.midi - right_hand_notes[right_index_list[-2]].pitch.midi) > 8):
        right_possible = False
    # check if pinky is too far away from other fingers
    else:
        for i in range(0, len(right_index_list) - 1):
            if i in (1, 2):
                if abs(right_hand_notes[-1].pitch.midi - right_hand_notes[right_index_list[i]].pitch.midi) >= (4 - i) * 4:
                    right_possible = False
                    break
            else:
                if abs(right_hand_notes[-1].pitch.midi - right_hand_notes[right_index_list[i]].pitch.midi) > (4 - i) * 4:
                    right_possible = False
                    break

    return left_possible, right_possible, left_tie_issue, None

# check if either hand has notes that are impossible to play and attempt to fix them
# returns: left_hand_notes, right_hand_notes, success, left_tie_issue, right_tie_issue
def adjust_chord(left_hand_notes, right_hand_notes, last_left_notes, last_right_notes):
    left_possible = False
    right_possible = False
    left_prev = True
    right_prev = True
    tie_loop = False
    tie_issue = False
    last_left_tie_issue = None
    last_right_tie_issue = None

    # iteratively try to fix problems with each hand until both hands are possible or they cannot be fixed.
    while not left_possible or not right_possible or tie_issue:
        left_possible, right_possible, left_tie_issue, right_tie_issue = check_spacing(left_hand_notes, right_hand_notes, last_left_notes, last_right_notes)
        if left_tie_issue is None and right_tie_issue is None:
            tie_issue = False
        else:
            tie_issue = True

        # prevent back and forth infinite loop
        if left_possible != left_prev and right_possible != right_prev:
            if not tie_issue or tie_loop:
                color_notes(left_hand_notes, right_hand_notes, COLOR_ERROR)
                return left_hand_notes, right_hand_notes, False, last_left_tie_issue, last_right_tie_issue
            elif tie_issue:
                tie_loop = True

        left_prev = left_possible
        right_prev = right_possible
        
        if not left_possible:
            if not right_possible:
                if not tie_issue or tie_loop:
                    # if both hands are impossible, the chord cannot be played
                    color_notes(left_hand_notes, right_hand_notes, COLOR_ERROR)
                    return left_hand_notes, right_hand_notes, False, last_left_tie_issue, last_right_tie_issue
                elif tie_issue:
                    tie_loop = True
            
            # attempt to fix the left hand by moving the highest note to the right hand
            # make sure right hand can still play the notes
            if len(right_hand_notes) == 0:
                right_hand_notes.insert(0, left_hand_notes.pop())
            elif abs(left_hand_notes[-1].pitch.midi - right_hand_notes[-1].pitch.midi) > MAX_INTERVAL and not tie_issue:
                color_notes(left_hand_notes, right_hand_notes, COLOR_ERROR)
                return left_hand_notes, right_hand_notes, False, None, None
            else:
                right_hand_notes.insert(0, left_hand_notes.pop())
            
        elif not right_possible:
            # attempt to fix the right hand by moving the lowest note to the right hand
            # make sure left hand can still play the notes
            if len(left_hand_notes) == 0:
                left_hand_notes.append(right_hand_notes.pop(0))
            elif abs(left_hand_notes[0].pitch.midi - left_hand_notes[-1].pitch.midi) > MAX_INTERVAL and not tie_issue:
                color_notes(left_hand_notes, right_hand_notes, COLOR_ERROR)
                return left_hand_notes, right_hand_notes, False, None, None
            else:
                left_hand_notes.append(right_hand_notes.pop(0))
        
        last_left_tie_issue = left_tie_issue
        last_right_tie_issue = right_tie_issue

    color_notes(left_hand_notes, right_hand_notes, COLOR_CORRECT)
    return left_hand_notes, right_hand_notes, True, None, None

# If a chord is impossible due to ties, attempt to switch tied notes between hands to fix it
def switch_ties(destination_hand, problem_hand, tie_issue, measure_number):
    overall_success = True
    cur_measure_number = measure_number
    should_return = False

    old_errors = 0
    new_errors = 0

    # travel backwards through chords and measures until the start of the tie
    while True:
        problem_chords = []
        for problem_chord_object in problem_hand.measure(cur_measure_number).getElementsByClass(chord.Chord):
            problem_chords.append(problem_chord_object)
        problem_chords.reverse()

        chord_index = 0
        for problem_chord_object in problem_chords:
            if should_return:
                return overall_success
            should_return = True

            chord_index -= 1
            for problem_note_object in problem_chord_object.notes:
                if problem_note_object.pitch == tie_issue:
                    if problem_note_object.style.color == COLOR_ERROR:
                        old_errors += 1
                    # flip the note to the destination hand
                    problem_chord_object.remove(problem_note_object)
                    elements = list(destination_hand.measure(cur_measure_number).getElementsByClass((chord.Chord, note.Rest)))
                    if elements[chord_index].isRest:
                        elements[chord_index] = chord.Chord()
                        elements[chord_index].quarterLength = problem_note_object.quarterLength
                        new_note = note.Note()
                        new_note.pitch = problem_note_object.pitch
                        new_note.quarterLength = problem_note_object.quarterLength
                        elements[chord_index].add(new_note)
                    else:
                        new_note = note.Note()
                        new_note.pitch = problem_note_object.pitch
                        new_note.quarterLength = problem_note_object.quarterLength
                        elements[chord_index].add(new_note)
                    
                    # check possible chords and recolor accordingly
                    destination_possible, problem_possible, _, _ = check_spacing(elements[chord_index].notes, problem_chord_object.notes, [], [])
                    if not destination_possible or not problem_possible:
                        color_notes(elements[chord_index].notes, problem_chord_object.notes, COLOR_ERROR)
                        overall_success = False
                        new_errors += 1
                    else:
                        color_notes(elements[chord_index].notes, problem_chord_object.notes, COLOR_CORRECT)
                    
                    # flipped set to true when all chords with tie have been flipped
                    if problem_note_object.tie is not None and problem_note_object.tie.type == 'start':
                        if new_errors > old_errors:
                            _ = switch_ties(problem_hand, destination_hand, tie_issue, measure_number)
                        return overall_success
                    
                    should_return = False
                    break
        cur_measure_number -= 1

# find the best place to split a chord into two hands
# returns: left_hand_notes, right_hand_notes
def find_split_point(chord_object):
    equal_ties = True
    
    # split at the largest interval between notes
    if(equal_ties):
        greatest_interval = -1
        split_index = -1
        i = 0
        while i < len(chord_object.notes) - 1:
            current_interval = chord_object.notes[i + 1].pitch.midi - chord_object.notes[i].pitch.midi
            if current_interval >= greatest_interval:
                greatest_interval = current_interval
                split_index = i
            i += 1
    
    left_hand_notes = [chord_object.notes[i] for i in range(0, split_index + 1)]
    right_hand_notes = [chord_object.notes[i] for i in range(split_index + 1, len(chord_object.notes))]

    return left_hand_notes, right_hand_notes

# main function to check if piece can be played by a piano
# returns: overall_success
def check_playability(combined, right_hand, left_hand):
    overall_success = True

    last_left_notes = []
    last_right_notes = []

    # traverse by measures because Partstaffs need you to do that that
    for measure in combined.getElementsByClass(stream.Measure):
        right_measure = right_hand.measure(measure.number)
        left_measure = left_hand.measure(measure.number)

        # clear out any existing rests because otherwise notes will be added on top of them, extending the measure
        for rest in right_measure.getElementsByClass('Rest'):
            right_measure.remove(rest)
        for rest in left_measure.getElementsByClass('Rest'):
            left_measure.remove(rest)

        # handle the actual rests
        rests = measure.getElementsByClass('Rest')
        for rest_object in rests:
            rest = note.Rest()
            rest.quarterLength = rest_object.quarterLength
            left_measure.insert(rest_object.offset, rest)
            rest = note.Rest()
            rest.quarterLength = rest_object.quarterLength
            right_measure.insert(rest_object.offset, rest)
        
        # traverse chords
        chords = measure.recurse().getElementsByClass(chord.Chord)
        for chord_object in chords:
            # assign notes to left and right parts
            # single note chords (not really chords but whatever) are played by the right hand
            left_hand_notes, right_hand_notes = find_split_point(chord_object)
            
            # make sure both hands can actually play the notes they have
            left_hand_notes, right_hand_notes, success, left_tie_issue, right_tie_issue = adjust_chord(left_hand_notes, right_hand_notes, last_left_notes, last_right_notes)

            # deep copy notes to avoid reference issues
            # notes from both hands are references to the same chord object which causes problems later
            left_hand_notes = copy_notes(left_hand_notes)
            right_hand_notes = copy_notes(right_hand_notes)
            
            # insert notes into respective measures
            if left_hand_notes == []:
                rest = note.Rest()
                rest.quarterLength = chord_object.quarterLength
                left_measure.insert(chord_object.offset, rest)
                left_chord = chord.Chord()
            else:
                left_chord = chord.Chord(left_hand_notes)
                left_chord.quarterLength = chord_object.quarterLength
                left_measure.insert(chord_object.offset, left_chord)
            if right_hand_notes == []:
                rest = note.Rest()
                rest.quarterLength = chord_object.quarterLength
                right_measure.insert(chord_object.offset, rest)
                right_chord = chord.Chord()
            else:
                right_chord = chord.Chord(right_hand_notes)
                right_chord.quarterLength = chord_object.quarterLength
                right_measure.insert(chord_object.offset, right_chord)
            
            if not success:
                # checks if failure is due to a tied note being forced into one hand by seeing if the
                # previous tied notes can be switched to the other hand to fix the issue
                if left_tie_issue is not None:
                    print(f"Switching tied note {left_tie_issue} in measure {measure.number} from right hand to left hand. Other chords may become impossible in the process.")
                    overall_success = switch_ties(left_hand, right_hand, left_tie_issue, measure.number) and overall_success
                elif right_tie_issue is not None:
                    print(f"Switching tied note {right_tie_issue} in measure {measure.number} from left hand to right hand. Other chords may become impossible in the process.")
                    overall_success = switch_ties(right_hand, left_hand, right_tie_issue, measure.number) and overall_success
                else:
                    overall_success = False
                    print(f"Impossible chord - Measure: {measure.number} Offset: {chord_object.offset}")
            
            last_left_notes = left_chord.notes
            last_right_notes = right_chord.notes

    # fix tie weirdness (more details in function)
    fix_ties_and_rests(left_hand)
    fix_ties_and_rests(right_hand)
    return overall_success

# this function combines tied notes and rests where possible to make the resulting music easier to read
# the .chordify() function combines all notes into chords in a single partstaff object
# this creates ties anywhere two notes with different lengths are played at the same time
# when splitting the chords into two hands, many unnecessary ties are left over
def fix_ties_and_rests(part):
    for measure in part.getElementsByClass(stream.Measure):
        chords = measure.getElementsByClass(chord.Chord)
        i = len(chords) - 1

        # go backwards from the end of the measure merging tied notes where possible
        while i > 0:
            merge = True
            # dont merge unless all notes are tied from the previous chord
            for note_object in chords[i].notes:
                if note_object.style.color == COLOR_ERROR or note_object.tie is None or note_object.tie.type == 'start':
                    merge = False
            # make sure the previous chord's notes are all tied to the current chord
            if merge:
                for note_object in chords[i - 1].notes:
                    if note_object.style.color == COLOR_ERROR or note_object.tie is None or note_object.tie.type == 'stop':
                        merge = False
            # combine chords
            if merge:
                chords[i - 1].quarterLength += chords[i].quarterLength
                measure.remove(chords[i])
                chords = measure.getElementsByClass(chord.Chord)
            i -= 1
        
        # simpler version for rests
        rests = measure.getElementsByClass(note.Rest)
        i = len(rests) - 1
        while i > 0:
            if rests[i - 1].offset + rests[i - 1].quarterLength == rests[i].offset:
                rests[i - 1].quarterLength += rests[i].quarterLength
                measure.remove(rests[i])
                rests = measure.getElementsByClass(note.Rest)
            i -= 1
        

# set up the environment
if platform == 'win32':
    # Windows
    path = 'C:/Program Files/MuseScore 4/bin/Musescore4.exe' # (TODO?: not hardcode the musicxml reader path?)
elif platform == 'darwin':
    # Mac OS - TODO
    pass
else:
    # assume Linux
    path = '/usr/bin/musescore'
env = environment.Environment()
env['musicxmlPath'] = path

argc = len(argv)
if argc < 3:
    print('arguments: [input file] [output name (no extension)]')
else:
    song = converter.parse(argv[1])
    print(f"\nStarting at {len(song.parts)} parts...\n")

    # combine all parts into one PartStaff
    combined = song.chordify()

    # create empty parts for right and left hand
    right_hand = combined.template()
    left_hand = combined.template()
    
    # main function
    success = check_playability(combined, right_hand, left_hand)

    # create empty final score
    final = stream.Score()

    # create piano staff grouping
    piano_staff = layout.StaffGroup([right_hand, left_hand], name='Piano', symbol='brace')

    # set clefs for left hand
    left_hand.getElementsByClass(stream.Measure)[0].removeByClass(clef.Clef)
    left_hand.getElementsByClass(stream.Measure)[0].insert(0, clef.BassClef())

    # set instruments for both hands
    instruments_right = [inst for inst in right_hand.recurse().getElementsByClass(instrument.Instrument)]
    instruments_left = [inst for inst in left_hand.recurse().getElementsByClass(instrument.Instrument)]
    for inst in instruments_right + instruments_left:
        inst.activeSite.remove(inst)

    right_hand.insert(0, instrument.Piano())
    left_hand.insert(0, instrument.Piano())

    # insert dynamics
    for measure in song.parts[0].getElementsByClass(stream.Measure):
        for dynamic in measure.getElementsByClass(dynamics.Dynamic):
            new_dynamic = dynamics.Dynamic()
            new_dynamic.value = dynamic.value
            right_hand.measure(measure.number).insert(dynamic.offset, new_dynamic)

    # assemble final score
    final.insert(0, piano_staff)
    final.append(right_hand)
    final.append(left_hand)

    # set metadata
    final.insert(0, metadata.Metadata())
    final.metadata = song.metadata
    final.parts[0].partName = 'Pno'
    final.parts[1].partName = 'Pno'

    # write output file
    final.write("musicxml", argv[2] + '.musicxml')
    if success:
        print("\nPiece can be played by a piano.\n")
    else:
        print("\nPiece cannot be played by a piano.\n")
