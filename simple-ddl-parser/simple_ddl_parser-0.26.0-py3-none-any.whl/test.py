from simple_ddl_parser import DDLParser

result = DDLParser("""CREATE TABLE myset.mytable (
    id_a character varying,
    id_b character varying,
    id_c character varying,
); """).run()

import pprint
pprint.pprint(result) 
