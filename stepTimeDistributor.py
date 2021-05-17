#------------------------------------------------------------------------#
# stepTimeDistributor.py
#------------------------------------------------------------------------#

import re
import traceback

from pycomm3 import CIPDriver, LogixDriver
from rich import print
from rich.table import Table

#------------------------------------------------------------------------#

sequences, seqTags = {}, {}
plcInitOK = False
inputCommands = {
    "discover": "Discover PLC's on the network",
    "init plc": "Initialize a connection to a PLC", 
    "init tags": "Initialize the step time tags using the connected PLC information",
    "clear": "Clear the current data in zzSteptimeLast, zzSteptimeShort and zzSteptimeLong for chosen sequences",
    "view": "View the current data in zzSteptimeLast, zzSteptimeShort and zzSteptimeLong for chosen sequences",
    "write": "Write data to zzStepRefTime for selected model varient and chosen sequences",
    "help": "Show help information", 
    "exit": "Exit the program"}
ipRegex = re.compile(r'''
    (\d{1,3}\.){3}\d{1,3}$ # IPv4
    | ([0-9abcdef]{4}:){7}[0-9abcdef]{4}$ # IPv6
    | ^cancel$ # Cancel the operation
    ''', re.VERBOSE|re.I)
slotRegex = re.compile(r'''
    \d+$ # Any digit
    | ^cancel$ # Cancel the operation
    ''', re.VERBOSE|re.I)
typeRegex = re.compile(r'''
	\d{1,2}$ # 1 or 2 digits only
	| ^cancel$ # Cancel the operation
	''', re.VERBOSE|re.I)
writeRegex = re.compile(r'''
    ^last$ # Write zzSteptimeLast values
    | ^long$ # Write zzSteptimeLong values
    | ^short$ # Write zzSteptimeShort values
    | ^cancel$ # Cancel operation
    ''', re.VERBOSE|re.I)
applyRegex = re.compile(r'''
    ^none$ # User doesn't want to apply any addition time
    | ^percentage$ # Apply a percentage of the time, variable time
    | ^time$ # Apply a fixed time 
    | ^cancel$ # Cancel operation
    ''', re.VERBOSE|re.I)
#------------------------------------------------------------------------#

def displayCommands(commands):
    print("COMMANDS")
    for k, v in commands.items(): # Loop through dictionary printing each key and value
        print(f"{k} : {v}")
    print()

def keySortDict(inDict, rev=False): # Funtion to sort a dictionary based on keys
    outDict = {}
    keys = list(inDict.keys())
    keys.sort(reverse = rev)
    for key in keys: # Append to the outDict using the sorted keys
        outDict.update({key : inDict.get(key)})
    return outDict # Return the key sorted dictionary

def extractSequences(seqDict, userInput): # Function to extract sequence numbers from the user input
    if userInput.find("all") != -1: # If the inputed sequences contains "all" then tags for all sequences will be initiated
        seqs = list(seqDict.keys())
    else: # If "all" was not present then split the inputed sequences by spaces and these are the sequences where the tags will be initiated
        seqs = userInput.split(' ')
        for i, s in enumerate(seqs): # Loop through the inputed sequences and add a leading zeros if there is a single digit
            if len(s) == 1:
                seqs[i] = s.zfill(2)
    return seqs

def discoverPLCs(): # Function to discover any PLC on the network
    plcs = []
    try:
        discovery = CIPDriver.discover() # Return list of all CIP devices on the network
        for device in discovery: # Go through discovery list and append any PLC#'s to a list
            if device['product_type'] == "Programmable Logic Controller":
                plcs.append(device['ip_address'])
        if len(plcs) > 0: # Print the discovered PLC's, if there are any
            print(f"Discovered {len(plcs)} PLC's:")
            plcs.sort()
            for plc in plcs:
                print(plc)
        else:
            print("No PLC's discovered on the network")
    except Exception:
        traceback.print_exc()

def initPLC(ip, slot): # Funtion to initialize a connection to a PLC and retrive data from it
    seqs = {}
    initOK = False
    try:
        print(f"Initializing connection to {ip}/{str(slot)}")
        plc = LogixDriver(f"{ip}/{str(slot)}", init_tags=True, init_program_tags=True) # Set up the LogixDriver for the stated PLC. This is returned to be used within other functions
        if plc.open(): # Open the connection to the PLC and read data from it
            print("Connection to PLC established\n")
            plcInfo = plc.info # Write the PLC info to a variable
            del plcInfo['tasks'] # Remove tasks from plcInfo as it is not required
            del plcInfo['modules'] # Remove modules from plcInfo as it is not required
            programs = plcInfo.pop('programs') # Pop the 'programs' dictionary item into a variable
            for prog in programs.keys(): # Go through the programs and search for a sequence regex (Sxx where x are digits)
                mo1 = re.search(r'^S\d\d', prog)
                if mo1 != None:
                    mo2 = re.search(r'\d\d', mo1.group()) # Search for the digits in the matched object and use them as keys in the sequences dictionary
                    seqs.setdefault(mo2.group(), prog) # Assign the key (sequence number) and value (program name) to the sequences dictionary
            print("PLC Information:") # Display the PLC information to the user
            for k, v in plcInfo.items(): # Loop through dictionary printing each key and value
                print(f"{k} : {v}")
            print("\nSequences:")
            for k, v in keySortDict(seqs).items(): # Sort the sequence alphabeticaly and loop through dictionary printing each key and value
                print(f"{k} : {v}")
            plc.close()
            initOK = True
    except Exception:
        plc.close()
        traceback.print_exc()
    return plc, initOK, keySortDict(seqs) # Return the LogixDriver and a key sorted dictionary of sequence programs in the connected PLC

def initTags(plc, sequences, selSeq): # Funtion to create all the step data tags required to read from and write to the PLC
    tags = {}
    seqs = extractSequences(sequences, selSeq)
    for seq in seqs: # Loop for each sequence selected by the user
        maxStep = 99 # Max step initially set to 99
        try: # Read the max step for the specified sequence
            if seq in list(sequences.keys()): # Check the sequence is in the list of PLC sequences
                plc.open()
                maxStep = plc.read(f"zzSeq[{seq}].MaxStepNo")
                tags.setdefault(seq, 
                    [f"zzSeq[{seq}].MaxStepNo", 
                    f"Program:{sequences[seq]}.zzSteptimeLast[1]{{{maxStep.value}}}", 
                    f"Program:{sequences[seq]}.zzSteptimeLong[1]{{{maxStep.value}}}",
                    f"Program:{sequences[seq]}.zzSteptimeShort[1]{{{maxStep.value}}}",
                    f"Program:{sequences[seq]}.zzStepRefTime[xxTypexx,1]{{{maxStep.value}}}"]) # Add the sequence tags to the dictionary of tags
                print(f"Initialized step tags for sequence {seq}: {sequences[seq]}")
                plc.close()
            else:
                print(f"Sequence {seq} does not exist in the PLC")
        except Exception:
            plc.close()
            traceback.print_exc()     
    return tags # Return the tags to be used within other functions

def clear(plc, tags, selSeq): # Function to clear the current data within the PLC of the step time tags
    seqs = extractSequences(tags, selSeq)
    for seq in seqs: # Loop for each sequence that the user has inputted
        try:
            if seq in list(tags.keys()): # Check the sequence is in the list of PLC sequences where tags have been initialized
                plc.open()
                values = plc.read(tags[seq][0]).value * [0] # Create a list of zeros equal to the length of the max step number
                results = plc.write((tags[seq][1], values), (tags[seq][2], values), (tags[seq][3], values)) # Write to the step time tags 
                if all(results): # Check that writes were successful
                    print(f"Successfully cleared tags in sequence {seq}")
                else:
                    print(f"Failed to clear tags in sequence {seq}")
                plc.close()  
            else:
                print(f"Sequence {seq} tags have not been initialized yet")
        except Exception:
            plc.close()
            traceback.print_exc()

def view(plc, sequences, tags, selSeq): # Function to display the last, longest and shortest step times
    seqs = extractSequences(tags, selSeq)
    for seq in seqs: # Loop for each sequence that the user has inputted
        try:
            if seq in list(tags.keys()): # Check the sequence is in the list of PLC sequences where tags have been initialized
                plc.open() # Open connection
                stepRefTags = []
                for i in range(1, 11): # Create tags to read from the PLC for all types
                    stepRefTags.append(tags[seq][4].replace('xxTypexx', str(i)))
                values = plc.read(tags[seq][0], tags[seq][1], tags[seq][2], tags[seq][3], *stepRefTags) # Read tag values from the PLC
                if all(values): # Only continue is all reads were successful
                    table = Table(title=f'Sequence: {seq} - {sequences[seq]}\nMax Step Number: {values[0].value}', header_style='bold') # Create a table
                    table.add_column('STEP') # Assign column
                    table.add_column('LAST\n(ms)') # Assign column
                    table.add_column('LONG\n(ms)') # Assign column
                    table.add_column('SHORT\n(ms)') # Assign column
                    for i in range(1, 11):
                        table.add_column(f'Ref Time\nType {i}\n(ms)') # Assign column
                    for i in range(values[0].value):
                        table.add_row(f'{i+1}', f'{values[1].value[i]}', f'{values[2].value[i]}', f'{values[3].value[i]}',
                            f'{values[4].value[i]}', f'{values[5].value[i]}', f'{values[6].value[i]}', f'{values[7].value[i]}', 
                            f'{values[8].value[i]}', f'{values[9].value[i]}',f'{values[10].value[i]}', f'{values[11].value[i]}', 
                            f'{values[12].value[i]}', f'{values[13].value[i]}') # Assign row data
                    print(table) # Display the table
                    print()
                else: # Any of the reads were unsuccessful
                    print(f'Failed to read step time data for sequence {seq}\n')
                plc.close() # Close connection
            else:
                print(f"Sequence {seq} tags have not been initialized yet")
        except Exception:
            plc.close()
            traceback.print_exc()

def write(plc, tags, selSeq): # Function to write data to the step refrence time tag in the PLC
    seqs = extractSequences(tags, selSeq)
    while True:
        mo = re.match(typeRegex, input('Input type (1 to 10): ')) # Look for a match from the user input of 1 or 2 digits only or word cancel
        if mo:
            if mo.group().lower() == 'cancel': # If user inputs cancel then return without writing any values
                return # Return from the funtion without writing any tags
            else:
                if int(mo.group()) in range(1, 11): # If the user inputed number is within the range 1 to 10 then run the write funtion
                    type = mo.group() # Set the type to a variable to be used later to set which tags to write to
                    break # Break from the while loop      
        print('Invalid type') # User inputed an incorrect type, try again
    while True:
        mo = re.match(writeRegex, input('Times to write (last, long or short): ')) # Look for match from the user input that refers to last, long, short or the user cancels
        if mo:
            if mo.group().lower() == 'cancel': # If user inputs cancel then return without writing any values
                return # Return from the funtion without writing any tags
            elif mo.group().lower() == 'last':
                readTags = 1 # Set readtags to be the 1 for reference to list position
                break # Break from the while loop 
            elif mo.group().lower() == 'long':
                readTags = 2 # Set readtags to be the 2 for reference to list position
                break # Break from the while loop 
            elif mo.group().lower() == 'short':
                readTags = 3 # Set readtags to be the 3 for reference to list position
                break # Break from the while loop
        print('Invalid selection')
    while True:
        mo = re.match(applyRegex, input('Apply percentage or time (none, percentage or time): ')) # Look for a match from the user input that refers to a percentage, time or neiter
        if mo:
            if mo.group().lower() == 'cancel': # If user inputs cancel then return without writing any values
                return
            if mo.group().lower() == 'none':
                break # Break from the while loop
            if mo.group().lower() == 'percentage': # User inputs percentage
                amount = 1 + (float(input('Enter percentage amount (0 to 100): ')) / 100) # Set amount to the float coverted input
                applyType = 1 # Set applyType to 1 (percentage), this will be used later when extra time is applied
                break # Break from the while loop
            elif mo.group().lower() == 'time': # User inputs time
                amount = float(input('Enter time (s): ')) * 1000 # Set amount to the integer coverted input
                applyType = 2 # Set applyType to 1 (time), this will be used later when extra time is applied
                break # Break from the while loop
        print('Invalid selection')
    for seq in seqs: # Loop for each sequence that the user has inputted
        try:
            if seq in list(tags.keys()): # Check the sequence is in the list of PLC sequences
                plc.open() # Open connection to the plc
                readValues = plc.read(tags[seq][readTags]) # Read the values from the plc for the user specified tags. Either last, long or short
                if readValues: # If read was successful
                    print(f'All values read successfully for sequence {seq}')
                    modValues = []
                    for value in readValues.value: # Loop for each values retrived during the read
                        if applyType == 1: # Apply percentage
                            modValues.append(round(value * amount))
                        elif applyType == 2: # Apply fixed time
                            modValues.append(round(value + amount))
                        else: # Apply nothing
                            modValues.append(value)
                    writeTag = tags[seq][4].replace('xxTypexx', type) # Create the tag to write to by replacing xxTypexx with the user specified type
                    results = plc.write(writeTag, modValues) # Write the modified values to the stepRefTime tags
                    if results: # If write was successful
                        print(f"Successfully wrote step reference times for sequence {seq}, type {type}")
                    else: # If write was unsuccessful
                        print(f"Failed to write step reference times for sequence {seq}, type {type}")
                else: # If read was unsuccessful
                    print(f'Failed to read all the values for sequence {seq}, none were wrote to stepRefTime')
                plc.close() # Close connection to plc
            else:
                print(f"Sequence {seq} does not exist")
        except Exception:
            plc.close()
            traceback.print_exc()

#------------------------------------------------------------------------#

if __name__ == "__main__":
    displayCommands(inputCommands) # Display the avaiable commands to the user
    while True: # Run continuously until the user requests to exit
        command = input("Command: ").strip().lower() # Wait for a command for the user
        # Once a command is recieved, compare it to the avaible commands and run the asscoiated code
        if command == "discover": # DISCOVER - Search the network for ALL CIP devices and return only the PLC's
            discoverPLCs() 
            print()
        elif command == "init plc": # INIT PLC - Initialize a connection to the specified PLC and return/display data from it
            ipOK = False
            while True:
                ip = re.match(ipRegex, input("PLC IP Address: ").strip()) # Request the PLC IP address and check it is the correct format
                if ip: # IP address format OK
                    if ip.group().lower() == 'cancel':
                        print('Operation cancelled\n')
                    else:
                        ipOK = True # IP Address OK, allow user to enter slot
                    break
                else: # IP address format not OK
                    print('Format of IP address was incorrect')
            while ipOK:
                slot = re.match(slotRegex, input("Rack slot: ").strip()) # Request the rack slot number
                if slot: # Slot format OK
                    if slot.group().lower() == 'cancel':
                        print('Operation cancelled\n')
                    else:
                        plc, plcInitOK, sequences = initPLC(ip.group(), slot.group()) # Initialize the connection to the PLC
                        print()
                    break
                else: # Slot format not OK
                    print('Format of slot was incorrect')
        elif command == "init tags": # INIT TAGS - Create the step tags for each sequence discovered in the PLC
            if plcInitOK == True:
                print("Choose the sequences you want to initiate the step time tags for. E.g. 1 2 4 7 or ALL or cancel to exit")
                print(f"PLC Sequences: {' '.join(list(sequences.keys()))}") # Display avaiable sequences 
                selectedSeq = input('Sequence: ').strip().lower() # User input
                if selectedSeq == 'cancel' or selectedSeq == '': # If cancel or blank then dont run initTags
                    print('Operation cancelled or no sequences chosen')
                else:
                    if selectedSeq != 'all':
                        selectedSeq = re.sub(r'\D+', ' ', selectedSeq) # Remove unwanted characters from string
                    seqTags.update(initTags(plc, sequences, selectedSeq.strip())) # Initialize tags for selected sequences 
            else:
                print('A PLC connection has not been initialized yet. Use \'init plc\'')
            print()
        elif command == "clear": # CLEAR - Writes zeros to the step time tags for the selected sequences
            if len(seqTags) > 0:
                print("Choose the sequences you want to clear the step time data for. E.g. 1 2 4 7 or ALL or cancel to exit")
                print(f"Avaiable PLC Sequences: {' '.join(list(seqTags.keys()))}")
                selectedSeq = input('Sequence: ').strip().lower() # User input
                if selectedSeq == 'cancel' or selectedSeq == '': # If cancel or blank then dont run clear
                    print('Operation cancelled or no sequences chosen')
                else:
                    if selectedSeq != 'all':
                        selectedSeq = re.sub(r'\D+', ' ', selectedSeq) # Remove unwanted characters from string
                    clear(plc, seqTags, selectedSeq.strip()) # Clear step time values in last, long and short for selected sequences 
            else:
                print('No tags have been initialized yet. Use \'init tags\'')
            print()
        elif command == "view": # VIEW - Display the last, long and short step times from the selected sequences
            if len(seqTags) > 0:
                print("Choose the sequences you want to clear the step time data for. E.g. 1 2 4 7 or ALL or cancel to exit")
                print(f"Avaiable PLC Sequences: {' '.join(list(seqTags.keys()))}")
                selectedSeq = input('Sequence: ').strip().lower() # User input
                if selectedSeq == 'cancel' or selectedSeq == '': # If cancel or blank then dont run view
                    print('Operation cancelled or no sequences chosen\n')
                else:
                    if selectedSeq != 'all':
                        selectedSeq = re.sub(r'\D+', ' ', selectedSeq) # Remove unwanted characters from string
                    view(plc, sequences, seqTags, selectedSeq.strip()) # Display step time data 
                    print()
            else:
                print('No tags have been initialized yet. Use \'init tags\'\n')
        elif command == "write": # WRITE - Write data to the zzStepRefTime tags
            if len(seqTags) > 0:
                print("Choose the sequences you want to initiate the step time tags for. E.g. 1 2 4 7 or ALL or cancel to exit")
                print(f"Avaiable PLC Sequences: {' '.join(list(seqTags.keys()))}")
                selectedSeq = input('Sequence: ').strip().lower() # User input
                if selectedSeq == 'cancel' or selectedSeq == '': # If cancel or blank then dont run write
                    print('Operation cancelled or no sequences chosen')
                else:
                    if selectedSeq != 'all':
                        selectedSeq = re.sub(r'\D+', ' ', selectedSeq) # Remove unwanted characters from string
                    write(plc, seqTags, selectedSeq.strip()) # Write step times to stepRefTime tags for selected sequences 
            else:
                print('No tags have been initialized yet. Use \'init tags\'')
            print()
        elif command == "help": # HELP - Display the commands avaiable to the user
            displayCommands(inputCommands) # Display the avaiable commands to the user
        elif command == "exit": # EXIT - Terminiate the program
            print("EXITING PROGRAM")
            exit()
        else: # No valid command was inputed by the user
            print('Invalid command\nType "help" for a list of commands\n')

#------------------------------------------------------------------------#
