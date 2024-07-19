class Config:
    """
    Holds configuration options.
    """

    def __init__(self) -> None:
        self.allow_plugins = True
        self.serviceable = False
        self.non_serviceable = False
        self.critSysTerm = False
        self.hidden = False
        self.hex = False
        self.rev = False
        self.extension = None
        self.severities = []
        self.only = False
        self.plid = None
        self.src = None
        self.bmcID = None
        self.pelID = None
        self.srcExcludeFile = None
