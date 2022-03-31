from datetime import date


class Vehicle:

    def __init__(self, color: str, model: str, year: int):
        self.color = color
        self.model = model
        self.year = year   # вносится год выпуска танспортного средства

    def __str__(self):
        return f'I am {self.__class__.__name__} {self.model}'

    @property
    def age(self) -> int:
        """Метод вычисляет возраст транспортного средства"""
        today = date.today()
        return today.year - self.year

    def break_down(self):
        return f'{self.__class__.__name__} can break down'

    def start_move(self):
        return f'{self.__class__.__name__}  can start moving'

    def stop_move(self):
        return f'{self.__class__.__name__} can stop moving'

    def transport_cargo(self):
        return f'i{self.__class__.__name__} can transport cargo (goods)'

    def transport_people(self):
        return f'{self.__class__.__name__} can transport people'


class Train(Vehicle):
    count = 0

    def __init__(self, color, model, year, amount_doors):
        self.amount_doors = amount_doors
        super().__init__(color, model, year)
        Train.add_train()

    @classmethod
    def add_train(cls):
        cls.count += 1

    @classmethod
    def get_count(cls):
        return f'{cls.__name__} amount {cls.count}'

    @staticmethod
    def drive_on_train():
        return 'i can drive on the train'


class Airplane(Vehicle):
    count = 0

    def __init__(self, color, model, year):
        super().__init__(color, model, year)
        Airplane.add_airplane()

    @classmethod
    def add_airplane(cls):
        cls.count += 1

    @classmethod
    def get_count(cls):
        return f'{cls.__name__} amount {cls.count}'

    @classmethod
    def fly(cls):
        return f' {cls.__name__} can fly'


class Car(Vehicle):
    count = 0

    def __init__(self, color, model, year, amount_doors=4):
        self.amount_doors = amount_doors
        super().__init__(color, model, year)
        Car.add_car()

    @classmethod
    def add_car(cls):
        cls.count += 1

    @classmethod
    def get_count(cls):
        return f'{cls.__name__} amount {cls.count}'


class Truck(Car):
    count = 0

    def __init__(self, color, model, year, amount_doors, amount_wheel):
        self.amount_wheel = amount_wheel
        super().__init__(color, model, year, amount_doors)
        Truck.add_truck()

    @classmethod
    def add_truck(cls):
        cls.count += 1

    @classmethod
    def get_count(cls):
        return f'Truck\'s amount {cls.count}'

    def transport_people(self):
        return f'{self.__class__.__name__} cant transport people'


car = Car('red', 'volvo', 1975, 2)
car_1 = Car('black', 'mazda', 2021)
print(car_1.transport_people())
truck = Truck('white', 'cargo', 1999, 4, 8)
air = Airplane('black', 's', 2015)
print(air.fly())
