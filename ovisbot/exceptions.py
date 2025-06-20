class OvisBotException(Exception):
    message: str = ""


class ChallengeDoesNotExistException(OvisBotException):
    message = "Παρέα μου... εν κουτσιάς... Εν έσιει έτσι challenge!"


class ChallengeExistsException(OvisBotException):
    message = "Να μου γελάσεις ρε κοπελλούι; This challenge already exists!"


class ChallengeAlreadySolvedException(OvisBotException):
    def __init__(self, solved_by: list[str]):
        self.solved_by = solved_by
        self.message = f"Άρκησες! This challenge has already been solved by {', '.join(self.solved_by)}!"


class ChallengeNotSolvedException(OvisBotException):
    message = "Ρε κουμπάρε.. αφού ένεν λυμένη η άσκηση."


class FewParametersException(OvisBotException):
    message = "Ρε παρέα μου κάτι σου λύφκεται. You need to provide more parameters for this command."


class NotInChallengeChannelException(OvisBotException):
    message = "Ρε πελλοβρεμένε! For this command you have to be in a ctf challenge channel created by `!ctf addchallenge`."


class NotInCTFChannelException(OvisBotException):
    message = "Ρε πελλοβρεμένε! For this command you have to be in a ctf channel created by `!ctf create`."


class CTFAlreadyExistsException(OvisBotException):
    message = "Ρε κουμπάρε! This CTF name already exists! Pick another one"


class CTFSharedCredentialsNotSet(OvisBotException):
    message = "This CTF has no shared credentials set!"


class CTFAlreadyFinishedException(OvisBotException):
    message = "This CTF has already finished!"


# TODO: remove
class CtfimeNameDoesNotMatch(Exception):
    pass


class DateMisconfiguredException(OvisBotException):
    message = "Έκαμες τα σαλάτα με τις ημερομηνίες παλε... Πρέπει Start date > End Date"


class MissingStartDateException(OvisBotException):
    message = "Φιλούδιν... πρέπει να βάλεις ενα start date (!ctf startdate ...) πρώτα!"


class CryptoHackApiException(Exception):
    pass
