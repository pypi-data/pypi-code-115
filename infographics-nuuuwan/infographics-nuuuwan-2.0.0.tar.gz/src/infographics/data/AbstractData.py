from abc import abstractmethod


class AbstractData:
    @abstractmethod
    def get_data(self):
        pass

    def keys(self):
        return self.get_data().keys()

    def __getitem__(self, id):
        return self.get_data().get(id)

    def __len__(self):
        return len(self.keys())
