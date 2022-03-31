from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    ForeignKey,
    Float,
)

from ...database import Base


class InterventionRawNewswireModel(Base):
    __tablename__ = "intervention_raw_newswires"

    id = Column(Integer, primary_key=True)
    news_id = Column(
        Integer,
        ForeignKey('newswires.id'),
        nullable=False,
    )
    intervention_raw_id = Column(
        Integer,
        ForeignKey('interventions_raw.id'),
        nullable=False,
    )
    score = Column(
        Float,
        nullable=False,
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        # https://stackoverflow.com/questions/58776476/why-doesnt-freezegun-work-with-sqlalchemy-default-values
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
    )
