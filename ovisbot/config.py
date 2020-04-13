from ovisbot.db_models import BotConfig


def create_config():
    config = BotConfig()
    config.REMINDERS_CHANNEL = 579049835064197157
    config.IS_MAINTENANCE = False
    config.save()
    return config


def get_config():
    try:
        return BotConfig.objects.all().first()
    except BotConfig.DoesNotExist:
        return create_config()
