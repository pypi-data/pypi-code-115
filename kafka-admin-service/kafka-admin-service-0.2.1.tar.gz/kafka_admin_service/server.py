
from xmlrpcutils.server import SimpleXmlRpcServer
from xmlrpcutils.service import ServiceBase

from .service import KafkaAdminService as KafkaAdminServiceCore

class KafkaAdminService(KafkaAdminServiceCore, ServiceBase):

    def __init__(self, config=None, namespace=None):
        KafkaAdminServiceCore.__init__(self, config)
        ServiceBase.__init__(self, config, namespace)

class KafkaAdminServer(SimpleXmlRpcServer):

    default_listen_port = 8383

    def register_services(self):
        super().register_services()
        self.kafka_admin_service = KafkaAdminService(self.config, namespace="kafka")
        self.kafka_admin_service.register_to(self.server)

application = KafkaAdminServer()
application_ctrl = application.get_controller()

if __name__ == "__main__":
    application_ctrl()
