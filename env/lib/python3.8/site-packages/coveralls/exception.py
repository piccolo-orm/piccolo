class CoverallsException(Exception):
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return str(self) == str(other)
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(str(self))
