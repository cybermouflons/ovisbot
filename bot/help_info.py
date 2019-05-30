help_page = '''
!status
Returns a list of past and ongoing ctf still kept in the server.

!ctf status
Returns a list of ongoing challenges in the ctf

!ctf create <ctf_name>
Create a CTF category with text channel and role in the category for a ctf.

!ctf join <ctf_name>
Join an ongoing ctf. Use `status` to see available CTFs. 

!ctf delete <ctf_name>
Delete a CTF category with all its channel and its user role.

!ctf setcreds <username> <password>
Sets shared credentials to be used by the team members to login to the CTF

!ctf showcreds
Displays shared credentials used by the team members to login to the CTF

!ctf description <description>
Sets the description of an existing CTF

!ctf addchallenge <chall_name> <category>
Creates a private channel for a challenge. Valid category names are: crypto, web, misc, pwn, reverse, stego 

!ctf attempt <chall_name>
Adds you to the private channel of that challenge. Use `!ctf status` to see active challenges.

!ctf solve [<member> <member> ...]
Sets the current challenge as solved by you. Addition of team mates that helped to solve is optional

!ctftime upcoming
Returns the 3 most recent upcoming CTFs from ctftime.

!utils stol <string>
Converts a string to long

!utils ltos <long>
Converts a logn number to string
'''
