# Notion CTF Database

## Proposed Idea:
A Notion Integration with Ovisbot which will be used as a note taking app for each CTF challenge. The Notion Database will be used also as an archived database for all the previous writeups and CTFs the team has participated.

## Idea Overview:
A database will be created which will include all the CTFs the team played with the following characteristics:

- CTF Name
- Format
- Date
- URL
- Weight

A new CTF will be created when the `!ctf create {CTF-Name}` command is invoked.

For each CTF, a new Challenges  Database will be created which will contain the following characteristics:

- Challenge Name
- Active Team Member
- Catergory
- Description
- Difficulty
- Status

A new challenge will be created when the `!ctf addchall {Chl-Name}` command is invoked inside a valid CTF discord channel.