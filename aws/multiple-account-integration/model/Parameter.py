class Parameter:

    default = None  # type : string
    min_length = None  # type : int
    max_length = None  # type : int
    allowed_pattern = None  # type :  string
    message = None  # type :  string

    def __init__(self):
        return

    def _extract_default(self, param):
        if 'Default' in param:
            self.default = param['Default']
        else:
            self.default = None

    def _extract_min_length(self, param):
        if 'MinLength' in param:
            self.min_length = param['MinLength']
        else:
            self.min_length = None

    def _extract_max_length(self, param):
        if 'MaxLength' in param:
            self.max_length = param['MaxLength']
        else:
            self.max_length = None

    def _extract_allowed_pattern(self, param):
        if 'AllowedPattern' in param:
            self.allowed_pattern = param['AllowedPattern']
        else:
            self.allowed_pattern = None

    def _extract_message(self, param):
        if 'ConstraintDescription' in param:
            self.message = param['ConstraintDescription']
        else:
            self.message = None

    def extract_data(self, param):
        if not param:
            param = {}
        self._extract_allowed_pattern(param)
        self._extract_default(param)
        self._extract_max_length(param)
        self._extract_min_length(param)
        self._extract_message(param)
