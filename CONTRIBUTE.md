# Setting up a development environment

1. Create a new [application with Discord](https://discordapp.com/developers/applications/)
2. Select "Bot" from the settings side bar on the left
3. Name your bot 🤖
4. Copy the Token provided by Discord for your bot (this is sensitive and should be kept secret)
5. Create a file named `.env` at the top level of the project, this file must include all the required environment variables
   - `DISCORD_BOT_TOKEN` is the token copied at step 4
   - You can see `.env.example` for the expected environment variables.
     - If any of the required ones are missing, you'll run into this error "Couldn't launch bot. Not configured properly"
6. Invite the bot to your Discord channel ([Instructions](https://github.com/jagrosh/MusicBot/wiki/Adding-Your-Bot-To-Your-Server))
7. From the top level of the project run `docker-compose up` (or `docker-compose up --build` to also re-build images)
8. Once the bot is ready you'll see its status as Online in your channel. That means it's up and ready to start receiving commands 🎉
