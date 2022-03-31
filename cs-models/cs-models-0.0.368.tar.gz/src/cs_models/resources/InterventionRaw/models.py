from sqlalchemy import (
    Column,
    Integer,
    String,
    UniqueConstraint,
)

from ...database import Base


class InterventionRawModel(Base):
    __tablename__ = "interventions_raw"

    id = Column(Integer, primary_key=True)
    intervention_string = Column(String(191), nullable=False)

    __table_args__ = (UniqueConstraint("intervention_string"),)
