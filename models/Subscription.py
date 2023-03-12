# TODO?
class Subscription():
    """
    The Subscription class is used to represent a subscription to alerts for a Chat.

    Attributes
    ----------
    CEPs : list : str
        List of subscribed CEPs. This should be a relation with a different entity in a relational database.
    activated : bool
        Whether the subscription is activated or not.
    """

    def __init__(self, CEPs: list, activated: bool):
        self.CEPs = CEPs
        self.activated = activated

    def __str__(self):
        return f"CEPs: {self.CEPs}\nActivated: {self.activated}"
