
import uuid
import json
import time

# #############################################################################
# 从队列中取出一条消息
# 1. 将msgid放在channel_running_ids的排序集中，以便能在消息处理超时时回收该消息。
# 2. 将msg体放在channel_running_msgs的字典中，以便能回收该消息。
# #############################################################################
REDMQ_MESSAGE_QUEUE_POP_MSG = """
    local msgs = redis.call("LPOP", KEYS[1], 1)
    if msgs ~= false then
        local data = cjson.decode(msgs[1])
        local msgid = data["id"]
        local timeout = data["timeout"]
        local nowtimes = redis.call('TIME')
        local nowtime = tonumber(nowtimes[1] .. "." .. nowtimes[2])
        data["start_time"] = nowtime
        data["recovery_time"] = nowtime + timeout
        local new_data_value = cjson.encode(data)
        redis.call("zadd", KEYS[2], data["recovery_time"], msgid)
        redis.call("hset", KEYS[3], msgid, new_data_value)
        return new_data_value
    else
        return nil
    end
"""

# #############################################################################
# 从running库中回收指定的1条消息
# #############################################################################
REDMQ_MESSAGE_QUEUE_RECOVER_MSG = """
    local nowtimes = redis.call('TIME')
    local nowtime = tonumber(nowtimes[1] .. "." .. nowtimes[2])
    local data = redis.call("HGET", KEYS[2], ARGV[1])
    local flag1 = false
    if data ~= false then
        data = cjson.decode(data)
        if data["retry"] ~= nil then
            data["retry"] = data["retry"] + 1
        else
            data["retry"] = 1
        end
        data["retry_time"] = nowtime
        local new_data = cjson.encode(data)
        local push_result = redis.call("RPUSH", KEYS[3], new_data)
        if push_result == 1 then
            flag1 = true
        end
    end
    redis.call("ZREM", KEYS[1], ARGV[1])
    redis.call("HDEL", KEYS[2], ARGV[1])
    if flag1 then
        return 1
    else
        return 0
    end
"""

# #############################################################################
# 从running库中回收所有超时消息
# #############################################################################
REDMQ_MESSAGE_QUEUE_RECOVER_MSGS = """
    local nowtimes = redis.call('TIME')
    local nowtime = tonumber(nowtimes[1] .. "." .. nowtimes[2])
    local msgids = redis.call("ZRANGEBYSCORE", KEYS[1], 0, nowtimes[1])
    local counter = 0
    for k, v in ipairs(msgids) do
        local data = redis.call("HGET", KEYS[2], v)
        data = cjson.decode(data)
        if data["retry"] ~= nil then
            data["retry"] = data["retry"] + 1
        else
            data["retry"] = 1
        end
        data["retry_time"] = nowtime
        local new_data = cjson.encode(data)
        redis.call("RPUSH", KEYS[3], new_data)
        redis.call("ZREM", KEYS[1], v)
        redis.call("HDEL", KEYS[2], v)
        counter = counter + 1
    end
    return counter
"""

# #############################################################################
# 确认消息已正确处理，并提交结果
# 1. 保存结果信息
# 2. 从running库中删除消息记录
# #############################################################################
REDMQ_MESSAGE_QUEUE_ACKNOWLEDGE = """
    local result = cjson.decode(ARGV[2])
    local nowtimes = redis.call('TIME')
    local nowtime = tonumber(nowtimes[1] .. "." .. nowtimes[2])
    local data = redis.call("HGET", KEYS[2], ARGV[1])
    if data ~= false then
        data = cjson.decode(data)
    else
        data = {}
        data["id"] = ARGV[1]
        data["meta_broken"] = true
    end
    data["acknowledged_time"] = nowtime
    data["result"] = result
    local new_data = cjson.encode(data)
    local flag1 = redis.call("SET", KEYS[3], new_data)
    local flag2 = redis.call("EXPIRE", KEYS[3], ARGV[3])
    local flag3 = redis.call("ZREM", KEYS[1], ARGV[1])
    local flag4 = redis.call("HDEL", KEYS[2], ARGV[1])
    if flag1 ~= nil and flag1["ok"] == "OK" and flag2 == 1 then
        return 1
    else
        return 0
    end
"""

class MessageQueue(object):

    def __init__(self, 
            conn, 
            channel="default",
            channel_prefix="redmq:message_queue:channels:",
            channel_running_msgs_prefix="redmq:message_queue:running:msgs:",
            channel_running_ids_prefix="redmq:message_queue:running:ids:",
            channel_results_prefix="redmq:message_queue:results:",
            result_timeout=60*60, # keep the result in redis for one hour by default.
            default_timeout=60*5, # msg executing timeout. If a worker fetched a msg, it must handle the msg within the `timeout` seconds.
            ):
        self.conn = conn
        self.channel = channel
        self.channel_key = channel_prefix + channel
        self.channel_running_msgs_key = channel_running_msgs_prefix + channel
        self.channel_running_ids_key = channel_running_ids_prefix + channel
        self.channel_results_prefix = channel_results_prefix
        self.default_timeout = default_timeout
        self.result_timeout = result_timeout

    def push(self, message, timeout=None, high_priority=False):
        if timeout is None:
            timeout = self.default_timeout
        data = {
            "id": str(uuid.uuid4()),
            "create_time": time.time(),
            "timeout": timeout,
            "message": message,
            "retry": 0,
            "retry_time": None,
            "meta_broken": False,
        }
        if high_priority:
            self.conn.lpush(self.channel_key, json.dumps(data))
        else:
            self.conn.rpush(self.channel_key, json.dumps(data))
        return data

    def pop_nowait(self):
        data = self.conn.eval(
            REDMQ_MESSAGE_QUEUE_POP_MSG,
            3,
            self.channel_key,
            self.channel_running_ids_key,
            self.channel_running_msgs_key,
            )
        if data:
            return json.loads(data)
        else:
            return None

    def recover(self, msgid=None):
        if isinstance(msgid, dict):
            msgid = msgid["id"]
        if msgid is None:
            return self.conn.eval(
                REDMQ_MESSAGE_QUEUE_RECOVER_MSGS,
                3,
                self.channel_running_ids_key,
                self.channel_running_msgs_key,
                self.channel_key,
                )
        else:
            return self.conn.eval(
                REDMQ_MESSAGE_QUEUE_RECOVER_MSG,
                3,
                self.channel_running_ids_key,
                self.channel_running_msgs_key,
                self.channel_key,
                msgid,
            )

    def acknowledge(self, msgid, result_data=None, success=None, error_code=None, error_message=None):
        if isinstance(msgid, dict):
            if success is None:
                success = msgid.get("success", True)
            if result_data is None:
                result_data = msgid.get("result_data", None)
            if error_code is None:
                error_code = msgid.get("error_code", 0)
            if error_message is None:
                error_message = msgid.get("error_message", None)
            msgid = msgid["id"]
        if success is None:
            success = True
        if error_code is None:
            error_code = 0
        if error_message is None:
            error_message = "OK"
        result_data = json.dumps({
            "success": success,
            "error_code": error_code,
            "error_message": error_message,
            "result_data": result_data,
        })
        flag = self.conn.eval(
            REDMQ_MESSAGE_QUEUE_ACKNOWLEDGE,
            3,
            self.channel_running_ids_key,
            self.channel_running_msgs_key,
            self.channel_results_prefix + msgid,
            msgid,
            result_data,
            self.result_timeout,
            )
        if flag == 0:
            return False
        else:
            return True

    def get_result_nowait(self, msgid):
        if isinstance(msgid, dict):
            msgid = msgid["id"]
        result_key = self.channel_results_prefix + msgid
        result = self.conn.get(result_key)
        if result:
            return json.loads(result)
        else:
            return None

    def delete_result(self, msgid):
        if isinstance(msgid, dict):
            msgid = msgid["id"]
        result_key = self.channel_results_prefix + msgid
        return self.conn.delete(result_key)

