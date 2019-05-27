help_page = '''
!status
Returns a list of past and ongoing ctf still kept in the server.

!ctf status
Returns a list of ongoing challenges in the ctf

!ctf create <ctf_name>
create a CTF category with text channel and role in the category for a ctf.

!ctf delete <ctf_name>
delete a CTF category with all its channel and its user role.

!ctf setcreds <username> <password>
Sets shared credentials to be used by the team members to login to the CTF

!ctf showcreds
Displays shared credentials used by the team members to login to the CTF

!ctf description <description>
Sets the description of an existing CTF

!ctf addchallenge <chall_name> <category>
Creates a private channel for a challenge. Valid category names are: crypto, web, misc, pwn, reverse, stego 

!ctf workon <chall_name>
Adds you to the private channel of that challenge. Use !ctf status to see active challenges.
'''