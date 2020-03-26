import os


def setupenv():
    env = {}
    env["DISCORD_BOT_TOKEN"] = input(
        "\033[1mPlease enter your Discord Bot token: \033[0m")
    env["WOLFRAM_ALPHA_APP_ID"] = input(
        "\033[1mPlease enter your Wolfram Alpha App ID: \033[0m")

    ROOT_DIR = os.path.abspath(os.curdir)

    with open(os.path.join(ROOT_DIR, ".env"), "w") as f:
        for k, v in env.items():
            f.write("{0}={1}\n".format(k, v))


if __name__ == "__main__":
    setupenv()
