TODO
====
Essential
---------
* Remove whitespace from end of input command
* In initTags and clear functions, allow more than one space between inputed sequences - regex required?
* Change keys in seqs in function init plc to be str not int type
    * Change need to be made throughout the other functions to suit this change
        * Once complete, uncomment '#print(f"PLC Sequences: {' '.join(list(sequences.keys()))}")' in lines 149 & 155
* Don't display any sequences that are unscheduled
* Add protection to prevent the user from initializing tags before a PLC has been initialized
* Add protection to prevent the user from clearing tags before tags have been initialized
* Add function to write data to the step ref time tags selected sequences of all
    * Choose from last, short or long
    * Can apply additional time or % to each
* Add protection to prevent the user from writing tags before tags have been initialized
* Add function to view current step time data in table format for selected sequences or all

Non-essential
-------------
* Add funtion to reset session that clears all the current data retrived from the PLC
    * Clear logixdriver
    * Clear tags
    * Clear viewed data
* Before exiting session use the reset function to clear the current data retrived from the PLC

Completed
---------
* Allow user to init tags for selected sequences or all