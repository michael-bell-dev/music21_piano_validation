from music21 import *

# checks the number of fingers and checks the distances between each one, comparing to user constraints
# returns: hand_is_possible
def check_constraints(notes, constraints, index_list):
    # impossible if number of fingers required is greater than 5
    if len(index_list) > 5:
        return False
    
    # definitely possible if number if fingers required is 0 or 1
    if len(index_list) < 2:
        return True
    
    two = False
    if len(index_list) == 2:
        two = True

    # check finger distance constraints when all fingers are in use
    if len(index_list) == 5 or two:
        for constraint in constraints:
            constraint_index0 = constraint[0]
            constraint_index1 = constraint[1]

            # if chord is only two fingers, ignore any constraint that isn't pinky and thumb
            if two:
                if constraint[0] not in [0, 4] or constraint[1] not in [0, 4]:
                    continue
                if constraint[0] == 4:
                    constraint_index0 = 1
                elif constraint[1] == 4:
                    constraint_index1 = 1

            # make sure finger distances are within accepted range
            if abs(notes[index_list[constraint_index0]].pitch.midi - notes[index_list[constraint_index1]].pitch.midi) > constraint[2]:
                return False
            # check to see if notes can be different colors at max distance
            # if not, checks to see if they are max distance and different colors
            if not constraint[3]:
                if abs(notes[index_list[constraint_index0]].pitch.midi - notes[index_list[constraint_index1]].pitch.midi) == constraint[2]:
                    if notes[index_list[constraint_index0]].pitch.alter != notes[index_list[constraint_index1]].pitch.alter:
                        return False
        
        return True

    # check finger distance constraints when 3 fingers are in use
    if len(index_list) == 3:
        for i in [1, 3, 2]:
            hand_is_possible = True
            for constraint in constraints:
                if constraint[0] not in [0, i, 4] or constraint[1] not in [0, i, 4]:
                    continue
                
                # remapping to keep indices in bounds
                constraint_index0 = constraint[0]
                if constraint[0] == 4:
                    constraint_index0 = 2
                elif constraint[0] == i:
                    constraint_index0 = 1
                    
                constraint_index1 = constraint[1]
                if constraint[1] == 4:
                    constraint_index1 = 2
                elif constraint[1] == i:
                    constraint_index1 = 1

                # make sure finger distances are within accepted range
                if abs(notes[index_list[constraint_index0]].pitch.midi - notes[index_list[constraint_index1]].pitch.midi) > constraint[2]:
                    hand_is_possible = False
                # check to see if notes can be different colors at max distance
                # if not, checks to see if they are max distance and different colors
                if not constraint[3]:
                    if abs(notes[index_list[constraint_index0]].pitch.midi - notes[index_list[constraint_index1]].pitch.midi) == constraint[2]:
                        if notes[index_list[constraint_index0]].pitch.alter != notes[index_list[constraint_index1]].pitch.alter:
                            hand_is_possible = False
            if hand_is_possible:
                return True
            
        return False
    
    # check finger distance constraints when 4 fingers are in use
    for i in [[1, 2], [2, 3], [1, 3]]:
        hand_is_possible = True
        for constraint in constraints:
            if constraint[0] not in [0, i[0], i[1], 4] or constraint[1] not in [0, i[0], i[1], 4]:
                continue
            
            # remapping to keep indices in bounds
            constraint_index0 = constraint[0]
            if constraint[0] == 4:
                constraint_index0 = 3
            elif constraint[0] == i[0]:
                constraint_index0 = 1
            elif constraint[0] == i[1]:
                constraint_index0 = 2
                
            constraint_index1 = constraint[1]
            if constraint[1] == 4:
                constraint_index1 = 3
            elif constraint[1] == i:
                constraint_index1 = 1
            elif constraint[1] == i[1]:
                constraint_index1 = 2

            # make sure finger distances are within accepted range
            if abs(notes[index_list[constraint_index0]].pitch.midi - notes[index_list[constraint_index1]].pitch.midi) > constraint[2]:
                hand_is_possible = False
            # check to see if notes can be different colors at max distance
            # if not, checks to see if they are max distance and different colors
            if not constraint[3]:
                if abs(notes[index_list[constraint_index0]].pitch.midi - notes[index_list[constraint_index1]].pitch.midi) == constraint[2]:
                    if notes[index_list[constraint_index0]].pitch.alter != notes[index_list[constraint_index1]].pitch.alter:
                        hand_is_possible = False
        if hand_is_possible:
            return True
        
    return False