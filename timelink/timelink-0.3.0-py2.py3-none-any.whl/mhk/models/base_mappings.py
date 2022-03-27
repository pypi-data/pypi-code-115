from timelink.mhk.models.pom_som_mapper import PomSomMapper, PomClassAttributes

"""
These mappings are needed to boostap a new database.

They are used by DBSystem to initialize a new database.

Mappings as these can be generated from existing MHK databases with:

        pom_classes = session.query(PomSomMapper)\
                                .where(Entity.pom_class  == 'class').all()
        for pom_class in pom_classes:
            print(f"'{pom_class.id}': [")
            print(repr(pom_class),',')
            for cattr in pom_class.class_attributes:
                print(repr(cattr),',')
            print('],')
"""
pom_som_base_mappings = {
    "act": [
        PomSomMapper(
            id="act",
            table_name="acts",
            group_name="historical-act",
            super_class="entity",
        ),
        PomClassAttributes(
            the_class="act",
            name="date",
            colname="the_date",
            colclass="date",
            coltype="varchar",
            colsize="24",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="act",
            name="id",
            colname="id",
            colclass="id",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="1",
        ),
        PomClassAttributes(
            the_class="act",
            name="loc",
            colname="loc",
            colclass="loc",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="act",
            name="obs",
            colname="obs",
            colclass="obs",
            coltype="varchar",
            colsize="1024",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="act",
            name="ref",
            colname="ref",
            colclass="ref",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="act",
            name="type",
            colname="the_type",
            colclass="type",
            coltype="varchar",
            colsize="32",
            colprecision="0",
            pkey="0",
        ),
    ],
    "attribute": [
        PomSomMapper(
            id="attribute",
            table_name="attributes",
            group_name="attribute",
            super_class="entity",
        ),
        PomClassAttributes(
            the_class="attribute",
            name="date",
            colname="the_date",
            colclass="date",
            coltype="varchar",
            colsize="24",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="attribute",
            name="entity",
            colname="entity",
            colclass="entity",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="attribute",
            name="id",
            colname="id",
            colclass="id",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="1",
        ),
        PomClassAttributes(
            the_class="attribute",
            name="obs",
            colname="obs",
            colclass="obs",
            coltype="varchar",
            colsize="1024",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="attribute",
            name="type",
            colname="the_type",
            colclass="type",
            coltype="varchar",
            colsize="32",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="attribute",
            name="value",
            colname="the_value",
            colclass="value",
            coltype="varchar",
            colsize="254",
            colprecision="0",
            pkey="0",
        ),
    ],
    "entity": [
        PomSomMapper(
            id="entity", table_name="entities", group_name="na", super_class="root"
        ),
        PomClassAttributes(
            the_class="entity",
            name="class",
            colname="class",
            colclass="class",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="entity",
            name="groupname",
            colname="groupname",
            colclass="groupname",
            coltype="varchar",
            colsize="32",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="entity",
            name="id",
            colname="id",
            colclass="id",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="1",
        ),
        PomClassAttributes(
            the_class="entity",
            name="inside",
            colname="inside",
            colclass="inside",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="entity",
            name="level",
            colname="the_level",
            colclass="level",
            coltype="numeric",
            colsize="3",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="entity",
            name="line",
            colname="the_line",
            colclass="line",
            coltype="numeric",
            colsize="6",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="entity",
            name="order",
            colname="the_order",
            colclass="order",
            coltype="numeric",
            colsize="6",
            colprecision="0",
            pkey="0",
        ),
    ],
    "geoentity": [
        PomSomMapper(
            id="geoentity",
            table_name="geoentities",
            group_name="geoentity",
            super_class="entity",
        ),
        PomClassAttributes(
            the_class="geoentity",
            name="id",
            colname="id",
            colclass="id",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="1",
        ),
        PomClassAttributes(
            the_class="geoentity",
            name="name",
            colname="name",
            colclass="name",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="geoentity",
            name="obs",
            colname="obs",
            colclass="obs",
            coltype="varchar",
            colsize="1024",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="geoentity",
            name="type",
            colname="the_type",
            colclass="type",
            coltype="varchar",
            colsize="32",
            colprecision="0",
            pkey="0",
        ),
    ],
    "good": [
        PomSomMapper(
            id="good", table_name="goods", group_name="bem", super_class="object"
        ),
        PomClassAttributes(
            the_class="good",
            name="description",
            colname="description",
            colclass="description",
            coltype="varchar",
            colsize="1024",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="good",
            name="id",
            colname="id",
            colclass="id",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="1",
        ),
        PomClassAttributes(
            the_class="good",
            name="loc",
            colname="loc",
            colclass="loc",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="0",
        ),
    ],
    "object": [
        PomSomMapper(
            id="object", table_name="objects", group_name="object", super_class="entity"
        ),
        PomClassAttributes(
            the_class="object",
            name="id",
            colname="id",
            colclass="id",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="1",
        ),
        PomClassAttributes(
            the_class="object",
            name="name",
            colname="name",
            colclass="name",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="object",
            name="obs",
            colname="obs",
            colclass="obs",
            coltype="varchar",
            colsize="1024",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="object",
            name="type",
            colname="the_type",
            colclass="type",
            coltype="varchar",
            colsize="32",
            colprecision="0",
            pkey="0",
        ),
    ],
    "person": [
        PomSomMapper(
            id="person", table_name="persons", group_name="person", super_class="entity"
        ),
        PomClassAttributes(
            the_class="person",
            name="id",
            colname="id",
            colclass="id",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="1",
        ),
        PomClassAttributes(
            the_class="person",
            name="name",
            colname="name",
            colclass="name",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="person",
            name="obs",
            colname="obs",
            colclass="obs",
            coltype="varchar",
            colsize="1024",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="person",
            name="sex",
            colname="sex",
            colclass="sex",
            coltype="char",
            colsize="1",
            colprecision="0",
            pkey="0",
        ),
    ],
    "relation": [
        PomSomMapper(
            id="relation",
            table_name="relations",
            group_name="relation",
            super_class="entity",
        ),
        PomClassAttributes(
            the_class="relation",
            name="date",
            colname="the_date",
            colclass="date",
            coltype="varchar",
            colsize="24",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="relation",
            name="destination",
            colname="destination",
            colclass="destination",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="relation",
            name="id",
            colname="id",
            colclass="id",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="1",
        ),
        PomClassAttributes(
            the_class="relation",
            name="obs",
            colname="obs",
            colclass="obs",
            coltype="varchar",
            colsize="1024",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="relation",
            name="origin",
            colname="origin",
            colclass="origin",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="relation",
            name="type",
            colname="the_type",
            colclass="type",
            coltype="varchar",
            colsize="32",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="relation",
            name="value",
            colname="the_value",
            colclass="value",
            coltype="varchar",
            colsize="254",
            colprecision="0",
            pkey="0",
        ),
    ],
    "rentity": [
        PomSomMapper(
            id="rentity",
            table_name="rentities",
            group_name="rentity",
            super_class="entity",
        ),
        PomClassAttributes(
            the_class="rentity",
            name="description",
            colname="description",
            colclass="name",
            coltype="varchar",
            colsize="128",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="rentity",
            name="id",
            colname="id",
            colclass="id",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="1",
        ),
        PomClassAttributes(
            the_class="rentity",
            name="obs",
            colname="obs",
            colclass="obs",
            coltype="varchar",
            colsize="1024",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="rentity",
            name="status",
            colname="status",
            colclass="status",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="rentity",
            name="the_class",
            colname="the_class",
            colclass="the_class",
            coltype="varchar",
            colsize="32",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="rentity",
            name="user",
            colname="user",
            colclass="user",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="0",
        ),
    ],
    "rgeoentity": [
        PomSomMapper(
            id="rgeoentity",
            table_name="rgeoentities",
            group_name="rgeoentity",
            super_class="rentity",
        ),
        PomClassAttributes(
            the_class="rgeoentity",
            name="id",
            colname="id",
            colclass="id",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="1",
        ),
        PomClassAttributes(
            the_class="rgeoentity",
            name="sname",
            colname="sname",
            colclass="sname",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="0",
        ),
    ],
    "robject": [
        PomSomMapper(
            id="robject",
            table_name="robjects",
            group_name="robject",
            super_class="rentity",
        ),
        PomClassAttributes(
            the_class="robject",
            name="id",
            colname="id",
            colclass="id",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="1",
        ),
        PomClassAttributes(
            the_class="robject",
            name="sname",
            colname="sname",
            colclass="sname",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="robject",
            name="type",
            colname="the_type",
            colclass="type",
            coltype="varchar",
            colsize="32",
            colprecision="0",
            pkey="0",
        ),
    ],
    "rperson": [
        PomSomMapper(
            id="rperson",
            table_name="rpersons",
            group_name="rperson",
            super_class="rentity",
        ),
        PomClassAttributes(
            the_class="rperson",
            name="id",
            colname="id",
            colclass="id",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="1",
        ),
        PomClassAttributes(
            the_class="rperson",
            name="sex",
            colname="sex",
            colclass="sex",
            coltype="char",
            colsize="1",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="rperson",
            name="sname",
            colname="sname",
            colclass="sname",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="0",
        ),
    ],
    "source": [
        PomSomMapper(
            id="source",
            table_name="sources",
            group_name="historical-source",
            super_class="entity",
        ),
        PomClassAttributes(
            the_class="source",
            name="date",
            colname="the_date",
            colclass="date",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="source",
            name="id",
            colname="id",
            colclass="id",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="1",
        ),
        PomClassAttributes(
            the_class="source",
            name="kleiofile",
            colname="kleiofile",
            colclass="kleiofile",
            coltype="varchar",
            colsize="512",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="source",
            name="loc",
            colname="loc",
            colclass="loc",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="source",
            name="obs",
            colname="obs",
            colclass="obs",
            coltype="varchar",
            colsize="1024",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="source",
            name="ref",
            colname="ref",
            colclass="ref",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="source",
            name="type",
            colname="the_type",
            colclass="type",
            coltype="varchar",
            colsize="32",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="source",
            name="value",
            colname="the_value",
            colclass="value",
            coltype="varchar",
            colsize="254",
            colprecision="0",
            pkey="0",
        ),
    ],
}

more_mappings = {
    "acusacoes": [
        PomSomMapper(
            id="acusacoes",
            table_name="acusacoes",
            group_name="acusa",
            super_class="object",
        ),
        PomClassAttributes(
            the_class="acusacoes",
            name="id",
            colname="id",
            colclass="id",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="1",
        ),
        PomClassAttributes(
            the_class="acusacoes",
            name="idcaso",
            colname="idcaso",
            colclass="idcaso",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="acusacoes",
            name="literal",
            colname="literal",
            colclass="literal",
            coltype="varchar",
            colsize="16000",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="acusacoes",
            name="obs",
            colname="obs",
            colclass="obs",
            coltype="varchar",
            colsize="16000",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="acusacoes",
            name="origem",
            colname="origem",
            colclass="origem",
            coltype="varchar",
            colsize="16000",
            colprecision="0",
            pkey="0",
        ),
    ],
    "caso": [
        PomSomMapper(
            id="caso", table_name="casos", group_name="caso", super_class="object"
        ),
        PomClassAttributes(
            the_class="caso",
            name="id",
            colname="id",
            colclass="id",
            coltype="varchar",
            colsize="64",
            colprecision="0",
            pkey="1",
        ),
        PomClassAttributes(
            the_class="caso",
            name="obs",
            colname="obs",
            colclass="obs",
            coltype="varchar",
            colsize="16654",
            colprecision="0",
            pkey="0",
        ),
        PomClassAttributes(
            the_class="caso",
            name="type",
            colname="the_type",
            colclass="the_type",
            coltype="varchar",
            colsize="32",
            colprecision="0",
            pkey="0",
        ),
    ],
}
