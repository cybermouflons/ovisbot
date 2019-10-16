# KyriosZolo CTF Discord Bot

> ### _A [discord.py](http://discordpy.readthedocs.io/en/latest/) bot focused on providing CTF tools for collaboration in Discord servers. If you have a feature request, make it a GitHub issue_

# How to Use

## General

- `!help` Displays help information and more information about available commands of the bot

- `!status` Returns the current status of the server with regards to CTFs. i.e. Information about which CTFs have been finished/are active, how many members are working on it and the number of challenges solved/unsolved.

## CTF

> This bot has commands for encoding/decoding, ciphers, and other commonly accessed tools during CTFs. But, the main use of the bot is to easily set up a CTF for your discord server to play as a team. The following commands listed are probably going to be used the most.

- `!ctf create <ctf_name>` This is the command you'll use when you want to begin a new CTF. This command will make a private category channel with a general text channel in your server, with your supplied name.

- `!ctf delete <ctf_name>` Deletes category, channels and roles related to the ctf. Note that the data are still kept in the DB.
  **Must have manage channels and roles permissions to do that**

- `!ctf join <ctf_name>` Using this command will either give or remove the role of a created ctf to/from you.

- `!ctf archive <ctf_name>` Arcive a CTF to the DB and remove it from discord.

_NOTE: the following ctf specific commands will only be accepted under the category created for that ctf. This is to avoid clashes with multiple ctfs going on in the same server._

- `!ctf status` This displays the status of the CTF. It displays the added challenges, who's working on what, and if a challenge is solved (and by who).

- `!ctf addchallenge <challenge_name>` Allows users to add challenges to a list. Creates a new private text channel with the challenge name given.

- `!ctf rmchall <challenge_name>` Removes the challenge with the given name.

- `!ctf attempt <challenge_name>` Gives you permission to view the text channel of the challenge given and adds you to the members working on it. Note the challenge name must match the exact name from `!ctf status`

- `!ctf solve [<teammate> <teammate> ...]` Marks the challenge as solved and sets you as the solver. To work you must be in a text channel of a challenge. If other teammates helped solving the challenge you can add them as optional mentions in the arguments and they will be added to the solvers as well.

- `!ctf unsolve` Resets solved status of a challenges. Simarly with the solve command you have to be in the text channel of the challenge. The purpose of this is to allow you to rollback accidental changes when running solve. (Forgot to add teammates, etc..)

- `!ctf notes` Shows the notebook url for the particular challenge channel that you are currently in. If this command is run outside of a challenge channel, then Kyrios Zolos gets mad.

- `!ctf setcreds <username> <password> [<link>]` Sets shared credentials to be used by the team

- `!ctf showcreds` Reveals shared credentials that have been set for the CTF

---
## Ctftime

 - `!ctftime upcoming` Returns the 3 most recent upcoming CTFs from ctftime.

 - `!ctftime writeups <number (default:3)>` Returns the most recent writeups from ctftime.

---
## Utils

- `!utils stol <string>` Converts a string to long. Useful for crypto challenges

- `!utils ltos <long>` Converts a long to string

# Contributors

- [apogiatzis](https://github.com/apogiatzis)
- [kgeorgiou](https://github.com/kgeorgiou)
- [condiom](https://github.com/condiom)
- [npitsillos](https://github.com/npitsillos)

## Have a feature request? Make a GitHub issue and feel free to contribute.
