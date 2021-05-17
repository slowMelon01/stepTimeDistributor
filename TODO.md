TODO
====
Bugs
----

***
Essential
---------
* #22 Modifiy clear funtion to allow the user to clear the step reference times as well
* #15 Add funtion to reset session that clears all the current data retrived from the PLC  
    * Clear logixdriver  
    * Clear tags  
* #24 Allow user to write step reference times to multiple types
***
Non-essential
-------------
* #21 Use Rich library to impove GUI
***
To Be Tested
------------
* #23 User can not input 'all' anymore as any non-digits get replaced by spaces
***
Completed
---------
* #1 Allow user to init tags for selected sequences or all
* #2 Remove whitespace from the start and end of the input command
* #3 Remove whitespace from the start and end of user inputs once they had requested one of the input commands
* #4 BUG - if user inputs incorrect ip address and slot then this error occurs  
    >Exception has occurred: UnboundLocalErrorlocal variable 'plc' referenced before assignment  
    >File "~\stepTimeDistributor\stepTimeDistributor.py", line 78, in initPLC  
    >plc.close()  
    >File "~\stepTimeDistributor\stepTimeDistributor.py", line 145, in <module>  
    >plc, sequences = initPLC(ip, slot) # Initialize the connection to the PLC 
* #5 Allow the user to cancel init tags or clear after they request it - when asked which sequences they want 
* #6 In initTags and clear functions, allow more than one space between inputed sequences - regex required?
* #11 Add function to write data to the step ref time tags selected sequences or all  
    * Choose from last, short or long  
    * Can apply additional time or % to each
* #14 BUG - Move code that replaces anything thing that is not s digit from what the user has inputed into functions.  
Currently the user cannot input "cancel" as all the characters will be replaces with a space.  
Code to be moved `selectedSeq = re.sub(r'\D+', ' ', input("Sequences: ").strip().lower())` 3 occurances.
* #17 Change keys in seqs in function init plc to be str not int type  
    * Change need to be made throughout the other functions to suit this change  
    * Once complete, uncomment `#print(f"PLC Sequences: {' '.join(list(sequences.keys()))}")`
* #7 Create function that extracts the sequences from the user inputed text
* #12 Add function to view current step time data in table format for selected sequences or all
* #9 Add protection to prevent the user from initializing tags before a PLC has been initialized
* #10 Add protection to prevent the user from clearing tags before tags have been initialized
* #18 Add protection to prevent the user from writing tags before tags have been initialized
* #19 Allow user to cancel when initializing a plc connection. When entering ip address or slot number
* #20 For clear, write and view functions, only display sequences where the tags have been initialized to the user
* #13 Re-running init tags will discard anything already within the tags global dictionary. Add to this if possible and dont init tags that are already existing unless user requests it
***
Discarded
---------
* #8 Don't display any sequences that are unscheduled
    * Not possible as the info doesn't say which task the program belongs to
* #16 Before exiting session use the reset function to clear the current data retrived from the PLC
    * Not needed