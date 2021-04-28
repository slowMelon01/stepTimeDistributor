#------------------------------------------------------------------------#
# stepTimeDistributor.py
#------------------------------------------------------------------------#

import re, traceback
from pycomm3 import CIPDriver, LogixDriver

#------------------------------------------------------------------------#

sequences, seqTags = {}, {}
inputCommands = {
    "discover": "Discover PLC's on the network",
    "init plc": "Initialize a connection to a plc", 
    "init tags": "Initialize the step time tags using the connected PLC information",
    "clear": "Clear the current data in zzSteptimeLast, zzSteptimeShort and zzSteptimeLong for chosen sequences",
    "view": "View the current data in zzSteptimeLast, zzSteptimeShort and zzSteptimeLong for chosen sequences",
    "apply": "Apply data to zzStepRefTime for selected model varient and chosen sequences",
    "help": "Show help information", 
    "exit": "Exit the program"}

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
                    seqs.setdefault(int(mo2.group()), prog) # Assign the key (sequence number) and value (program name) to the sequences dictionary
            print("PLC Information:") # Display the PLC information to the user
            for k, v in plcInfo.items(): # Loop through dictionary printing each key and value
                print(f"{k} : {v}")
            print("\nSequences:")
            for k, v in keySortDict(seqs).items(): # Sort the sequence alphabeticaly and loop through dictionary printing each key and value
                print(f"{k} : {v}")
            plc.close()
    except Exception:
        plc.close()
        traceback.print_exc() 
    return plc, keySortDict(seqs) # Return the LogixDriver and a key sorted dictionary of sequence programs in the connected PLC

def initTags(plc, seqs): # Funtion to create all the step data tags required to read from and write to the PLC
    tags = {}
    for seq in seqs.keys(): # Loop for each sequence in the plc
        maxStep = 99 # Max step initially set to 99
        try: # Read the max step for the specified sequence
            plc.open()
            maxStep = plc.read(f"zzSeq[{seq}].MaxStepNo")
            plc.close()
        except Exception:
            plc.close()
            traceback.print_exc() 
        tags.setdefault(seq, 
            [f"zzSeq[{seq}].MaxStepNo", 
            f"Program:{seqs[int(seq)]}.zzSteptimeLast[1]{{{maxStep.value}}}", 
            f"Program:{seqs[int(seq)]}.zzSteptimeLong[1]{{{maxStep.value}}}",
            f"Program:{seqs[int(seq)]}.zzSteptimeShort[1]{{{maxStep.value}}}"]) # Add the sequence tags to the dictionary of tags
        print(f"Initialized step tags for sequence {seq}, {seqs[int(seq)]}")
    return tags # Return the tags to be used within other functions

#------------------------------------------------------------------------#

if __name__ == "__main__":
    displayCommands(inputCommands) # Display the avaiable commands to the user
    while True: # Run continuously until the user requests to exit
        command = input("Command: ") # Wait for a command for the user
        # Once a command is recieved, compare it to the avaible commands and run the asscoiated code
        if command.lower() == "discover": # DISCOVER - Search the network for ALL CIP devices and return only the PLC's
            discoverPLCs() 
            print()
        elif command.lower() == "init plc": # INIT PLC - Initialize a connection to the specified PLC and return/display data from it
            ip = input("PLC IP Address: ") # Request the PLC IP address 
            slot = input("Rack slot: ") # Request the rack slot number
            plc, sequences = initPLC(ip, slot) # Initialize the connection to the PLC
            print()
        elif command.lower() == "init tags": # INIT TAGS - Create the step tags for each sequence discovered in the PLC
            seqTags = initTags(plc, sequences)
            print()
        elif command.lower() == "help": # HELP - Display the commands avaiable to the user
            displayCommands(inputCommands) # Display the avaiable commands to the user
        elif command.lower() == "exit": # EXIT - Terminiate the program
            print("EXITING PROGRAM")
            exit()
        else: # No valid command was inputed by the user
            print('Invalid command\nType "help" for a list of commands\n')

#------------------------------------------------------------------------#