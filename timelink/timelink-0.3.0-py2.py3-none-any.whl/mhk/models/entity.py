from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship, backref

from timelink.mhk.models.base_class import Base


class Entity(Base):
    __tablename__ = "entities"

    id = Column(String, primary_key=True)
    pom_class = Column(
        "class",
        String,
        ForeignKey("classes.id", use_alter=True, name="fk_entities_class"),
    )
    # TODo add relationship to PomSomMapper = pom_mapper
    inside = Column(String, ForeignKey("entities.id", ondelete="CASCADE"))
    the_order = Column(Integer)
    the_level = Column(Integer)
    the_line = Column(Integer)
    groupname = Column(String)
    updated = Column(DateTime, default=datetime.utcnow)
    indexed = Column(DateTime)

    # These are defined in relation.py
    # rels_in = relationship("Relation", back_populates="dest")
    # rels_out = relationship("Relation", back_populates="org")

    # this based on https://stackoverflow.com/questions/28843254/deleting-from-self-referential-inherited-objects-does-not-cascade-in-sqlalchemy # noqa: E501
    contains = relationship(
        "Entity",
        backref=backref("contained_by", remote_side="Entity.id"),
        cascade="all",
    )

    # see https://docs.sqlalchemy.org/en/14/orm/inheritance.html
    # To handle non mapped pom_class see https://github.com/sqlalchemy/sqlalchemy/issues/5445 # noqa: E501
    #
    #    __mapper_args__ = {
    #       "polymorphic_identity": "entity",
    #    "polymorphic_on": case(
    #        [(type.in_(["parent", "child"]), type)], else_="entity"
    #    ),
    #
    #  This defines what mappings do exist
    # [aclass.__mapper_args__['polymorphic_identity']
    #       for aclass in Entity.__subclasses__()]

    __mapper_args__ = {
        "polymorphic_identity": "entity",
        "polymorphic_on": pom_class,
    }

    @classmethod
    def get_subclasses(cls):
        for subclass in cls.__subclasses__():
            yield from subclass.get_subclasses()
            yield subclass

    @classmethod
    def get_orm_entities_classes(cls):
        """
        Returns the currently defined ORM classes that extend Entity
        (including Entity itself)
        :return: List of ORM classes
        """
        sc = list(Entity.get_subclasses())
        sc.append(Entity)
        return sc

    @classmethod
    def get_som_mapper_ids(cls):
        """
        Returns the ids of SomPomMapper references by orm classes
        :return: List of strings
        """
        return [
            aclass.__mapper_args__["polymorphic_identity"]
            for aclass in Entity.get_orm_entities_classes()
        ]

    @classmethod
    def get_tables_to_orm_as_dict(cls):
        """
        Return a dict with table name as key and ORM class as value
        """
        return {
            ormclass.__mapper__.local_table.name: ormclass
            for ormclass in Entity.get_orm_entities_classes()
        }

    @classmethod
    def get_som_mapper_to_orm_as_dict(cls):
        """
        Return a dict with pom_class id as key and ORM class as value
        """
        sc = Entity.get_orm_entities_classes()
        return {ormclass.__mapper__.polymorphic_identity: ormclass for ormclass in sc}

    @classmethod
    def get_orm_for_table(cls, table: String):
        """
        Entity.get_orm_for_table("acts")

        will return the ORM class handling the "acts" table
        """
        return cls.get_tables_to_orm_as_dict().get(table, None)

    @classmethod
    def get_orm_for_pom_class(cls, pom_class: str):
        """
        Entity.get_orm_for_pom_class("act")

        will return the ORM class corresponding to the pom_class "act"
        """
        return cls.get_som_mapper_to_orm_as_dict().get(pom_class, None)

    @classmethod
    def get_entity(cls, id: str, session=None):
        """
        Get an Entity from the database. The object returned
        will be of the ORM class defined by mappings.
        :param id: id of the entity
        :param session: current session
        :return: an Entity object of the proper class for the mapping
        """
        entity = session.get(Entity, id)
        if entity is not None:
            if entity.pom_class != "entity":
                orm_class = Entity.get_orm_for_pom_class(entity.pom_class)
                object_for_id = session.get(orm_class, id)
                return object_for_id
            else:
                return entity
        else:
            return None

        return entity

    def __repr__(self):
        return (
            f'Entity(id="{self.id}", '
            f'pom_class="{self.pom_class}",'
            f'inside="{self.inside}", '
            f"the_order={self.the_order}, "
            f"the_level={self.the_level}, "
            f"the_line={self.the_line}, "
            f'groupname="{self.groupname}", '
            f"updated={self.updated}, "
            f"indexed={self.indexed},"
            f")"
        )

    def __str__(self):
        return f"{self.groupname}${self.id}/type={self.pom_class}"

    def to_kleio(self, ident="", ident_inc="  "):
        s = f"{ident}{str(self)}"
        for inner in self.contains:
            innerk = inner.to_kleio(ident=ident + ident_inc, ident_inc=ident_inc)
            s = f"{s}\n{innerk}"
        return s
