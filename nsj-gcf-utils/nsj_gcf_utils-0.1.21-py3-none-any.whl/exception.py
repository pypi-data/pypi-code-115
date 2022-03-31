class ERPException(Exception):
    mope_code: str
    message: str

    def __init__(self, mope_code: str, message: str):
        super().__init__(f'{mope_code} - {message}')
        self.mope_code = mope_code
        self.message = message
