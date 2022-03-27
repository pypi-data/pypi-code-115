BINLOG_DUMP_NON_BLOCK = 0x01
BINLOG_THROUGH_GTID = 0x04
MAX_HEARTBEAT = 4294967

# field type
TIMESTAMP2 = 17
DATETIME2 = 18
TIME2 = 19

# binlog
UNKNOWN_EVENT = 0x00
START_EVENT_V3 = 0x01
QUERY_EVENT = 0x02
STOP_EVENT = 0x03
ROTATE_EVENT = 0x04
INTVAR_EVENT = 0x05
LOAD_EVENT = 0x06
SLAVE_EVENT = 0x07
CREATE_FILE_EVENT = 0x08
APPEND_BLOCK_EVENT = 0x09
EXEC_LOAD_EVENT = 0x0A
DELETE_FILE_EVENT = 0x0B
NEW_LOAD_EVENT = 0x0C
RAND_EVENT = 0x0D
USER_VAR_EVENT = 0x0E
FORMAT_DESCRIPTION_EVENT = 0x0F
XID_EVENT = 0x10
BEGIN_LOAD_QUERY_EVENT = 0x11
EXECUTE_LOAD_QUERY_EVENT = 0x12
TABLE_MAP_EVENT = 0x13
PRE_GA_WRITE_ROWS_EVENT = 0x14
PRE_GA_UPDATE_ROWS_EVENT = 0x15
PRE_GA_DELETE_ROWS_EVENT = 0x16
WRITE_ROWS_EVENT_V1 = 0x17
UPDATE_ROWS_EVENT_V1 = 0x18
DELETE_ROWS_EVENT_V1 = 0x19
INCIDENT_EVENT = 0x1A
HEARTBEAT_LOG_EVENT = 0x1B
IGNORABLE_LOG_EVENT = 0x1C
ROWS_QUERY_LOG_EVENT = 0x1D
WRITE_ROWS_EVENT_V2 = 0x1E
UPDATE_ROWS_EVENT_V2 = 0x1F
DELETE_ROWS_EVENT_V2 = 0x20
GTID_LOG_EVENT = 0x21
ANONYMOUS_GTID_LOG_EVENT = 0x22
PREVIOUS_GTIDS_LOG_EVENT = 0x23

# INTVAR types
INTVAR_INVALID_INT_EVENT = 0x00
INTVAR_LAST_INSERT_ID_EVENT = 0x01
INTVAR_INSERT_ID_EVENT = 0x02

UNSIGNED_SHORT_LENGTH = 2
UNSIGNED_INT24_LENGTH = 3
UNSIGNED_INT64_LENGTH = 8

# json type
JSONB_TYPE_SMALL_OBJECT = 0x0
JSONB_TYPE_LARGE_OBJECT = 0x1
JSONB_TYPE_SMALL_ARRAY = 0x2
JSONB_TYPE_LARGE_ARRAY = 0x3
JSONB_TYPE_LITERAL = 0x4
JSONB_TYPE_INT16 = 0x5
JSONB_TYPE_UINT16 = 0x6
JSONB_TYPE_INT32 = 0x7
JSONB_TYPE_UINT32 = 0x8
JSONB_TYPE_INT64 = 0x9
JSONB_TYPE_UINT64 = 0xA
JSONB_TYPE_DOUBLE = 0xB
JSONB_TYPE_STRING = 0xC
JSONB_TYPE_OPAQUE = 0xF

JSONB_LITERAL_NULL = 0x0
JSONB_LITERAL_TRUE = 0x1
JSONB_LITERAL_FALSE = 0x2
