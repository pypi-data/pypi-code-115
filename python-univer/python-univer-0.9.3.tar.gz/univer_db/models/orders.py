from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship

from univer_db.orm import get_base


Base = get_base()


class Order(Base):
    """
    Приказ
    """
    __tablename__ = 'univer_order'
    __table_args__ = {'implicit_returning': False}

    # Идентификатор
    id = Column('order_id', Integer, primary_key=True)

    # Статус
    status = Column(Integer)

    # Тип приказа
    order_type_id = Column(ForeignKey('univer_order_type.order_type_id'))
    order_type = relationship('OrderType')

    # Действие приказа
    order_action_id = Column(ForeignKey('univer_order_action.order_action_id'))
    order_action = relationship('OrderAction')

    # Номер приказа
    number = Column('order_number', String(20))

    # Дата приказа
    date = Column('order_date', DateTime)

    # Данные приказа в XML-формате
    data = Column('order_data', String)

    # Год
    year = Column('order_year', Integer)

    # Семестр
    semester = Column('order_semester', Integer)

    # Одобрен
    approved = Column('order_approved', Integer)

    # Подписан (???)
    signed = Column('order_signed', Integer)

    # Дата и время создания
    date_create = Column('order_date_create', DateTime)

    # Дата и время одобрения
    date_approve = Column('order_date_approve', DateTime)

    # Дата и время окончания
    date_done = Column('order_date_done', DateTime)

    # Когда процесс окончания начался
    done_process_start = Column('order_done_process_start', DateTime)

    # Расположение сгенерированного документа
    document = Column('order_document', String(50))

    # Ступень обучения
    stage_id = Column(ForeignKey('univer_stage.stage_id'))
    stage = relationship('Stage')

    # Форма обучения
    education_form_id = Column(ForeignKey(
        'univer_education_form.education_form_id'))
    education_form = relationship('EducationForm')

    # Тип оплаты
    payment_form_id = Column(ForeignKey(
        'univer_payment_forms.payment_form_id'))
    payment_form = relationship('PaymentForm')

    # Уровень обучения (Только идентификатор, для приказов без уровня образования требуется указать 0)
    edu_level_id = Column(Integer)

    def __repr__(self):
        return '<Order {} (id={} status={} order_type={} stage={} education_form={} payment_form={} edu_level={}'.format(
            self,
            self.id,
            self.status,
            self.order_type_id,
            self.stage_id,
            self.education_form_id,
            self.payment_form_id,
            self.edu_level_id
        )

    def __str__(self):
        return '{} - {}'.format(self.number, self.date)


class OrderType(Base):
    """
    Модель "Типы приказов"
    Статус: Выполняется
    """

    __tablename__ = 'univer_order_type'

    # Идентификатор
    id = Column('order_type_id', Integer, primary_key=True)

    # Статус
    status = Column(Integer)

    # Наименование
    name_ru = Column('order_type_name_ru', String(300))
    name_kz = Column('order_type_name_kz', String(300))
    name_en = Column('order_type_name_en', String(300))

    def __repr__(self):
        return '<OrderType {} (id={} status={})>'.format(self, self.id, self.status)

    def __str__(self):
        return self.name_ru


class OrderAction(Base):
    """
    Действие приказа
    """
    __tablename__ = 'univer_order_action'

    # Идентификатор
    id = Column('order_action_id', Integer, primary_key=True)

    # Наименование
    name_ru = Column('order_action_name_ru', String(500))
    name_kz = Column('order_action_name_kz', String(500))
    name_en = Column('order_action_name_en', String(500))

    # Короткое наименование
    short_name_ru = Column('order_action_short_name_ru', String(200))
    short_name_kz = Column('order_action_short_name_kz', String(200))
    short_name_en = Column('order_action_short_name_en', String(200))

    # ???
    value_ru = Column('order_action_value_ru', String(250))
    value_kz = Column('order_action_value_kz', String(250))
    value_en = Column('order_action_value_en', String(250))

    # Тип приказа
    order_type_id = Column(ForeignKey('univer_order_type.order_type_id'))
    order_type = relationship('OrderType')

    # Статус
    status = Column(Integer)

    def __repr__(self):
        return '<OrderAction {} (id={} order_type={} status={})>'.format(self, self.id, self.order_type_id, self.status)

    def __str__(self):
        return self.name_ru


class OrderStudentLink(Base):
    """
    Студент внутри приказа
    """
    __tablename__ = 'univer_order_student_link'

    # Приказ
    order_id = Column(ForeignKey('univer_order.order_id'), primary_key=True)
    order = relationship('Order')

    # Студент
    student_id = Column(ForeignKey(
        'univer_students.students_id'), primary_key=True)
    student = relationship('Student')

    # Данные внутри приказа в XML-формате
    data = Column('osl_data', String)

    def __repr__(self):
        return '<OrderStudentLink {} (order={} student={})>'.format(self, self.order_id, self.student_id)

    def __str__(self):
        return '{} ({})'.format(self.student, self.order)
