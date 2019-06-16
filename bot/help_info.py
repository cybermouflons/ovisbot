help_page = {}

help_page['misc'] = '''
!help [<page1> <page2> ...] (optional)
Display the help pages(default all pages)
Current pages are: {}

!status
Returns a list of past and ongoing ctf still kept in the server.

!chucknorris
Returns a chuck norris joke

!contribute
Return the github link for KyriosZolos

!frappe
Return a frappe for you
'''.format(" ".join(help_page.keys()))

help_page['ctf'] = '''
!ctf status
Returns a list of ongoing challenges in the ctf

!ctf create <ctf_name>
Create a CTF category with text channel and role in the category for a ctf.

!ctf finish <ctf_name>
Marks CTF as finished. (Requires manage channels permissions)

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

!ctf attempt --all
Adds you to the private channels of all challenges

!ctf solve [<member> <member> ...]
Sets the current challenge as solved by you. Addition of team mates that helped to solve is optional

!ctf unsolve
Sets the current challenge as unsolved. Allows to to rollback accidental solves.
'''

help_page['ctftime'] = '''
!ctftime upcoming
Returns the 3 most recent upcoming CTFs from ctftime.

!ctftime writeups <number>(optional)
Returns the number(default=3) most recent writeups from ctftime.
'''

help_page['utils'] = '''
!utils stol <string>
Converts a string to long

!utils ltos <long>
Converts a long number to string
'''
