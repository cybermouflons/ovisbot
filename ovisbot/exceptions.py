class ChallengeDoesNotExistException(Exception):
    pass


class ChallengeExistsException(Exception):
    pass


class ChallengeInvalidCategory(Exception):
    pass

class ChallengeInvalidDifficulty(Exception):
    pass

class ChallengeAlreadySolvedException(Exception):
    def __init__(self, solved_by, *args, **kwargs):
        self.solved_by = solved_by


class ChallengeNotSolvedException(Exception):
    pass


class UserAlreadyInChallengeChannelException(Exception):
    pass


class FewParametersException(Exception):
    pass


class NotInChallengeChannelException(Exception):
    pass


class CTFAlreadyExistsException(Exception):
    pass


class CTFSharedCredentialsNotSet(Exception):
    pass


class CTFAlreadyFinishedException(Exception):
    pass


class CtfimeNameDoesNotMatch(Exception):
    pass


class DateMisconfiguredException(Exception):
    pass


class MissingStartDateException(Exception):
    pass


class MissingEndDateException(Exception):
    pass


class CryptoHackApiException(Exception):
    pass
