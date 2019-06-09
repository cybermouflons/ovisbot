# Setting up a development environment

1. Create a new [application with Discord](https://discordapp.com/developers/applications/)
2. Select "Bot" from the settings side bar on the left
3. Name your bot 🤖
4. Copy the Token provided by Discord for your bot (this is sensitive and should be kept secret)
5. Create a file named `.env` at the top level of the project and put the following environment variable in the file: `DISCORD_BOT_TOKEN=<the token you copied at step 4>`
6. Invite the bot to your Discord channel ([Instructions](https://github.com/jagrosh/MusicBot/wiki/Adding-Your-Bot-To-Your-Server))
7. From the top level of the project run `docker-compose up`
8. Once the bot is ready you'll see its status as Online in your channel. That means it's up and ready to start receiving commands 🎉
