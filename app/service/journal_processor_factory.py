from app.service.current_protocol.current_protocol_process_task import CurrentProtocolProcessor
from app.service.nature_protocol.nature_protocol_process_task import NatureProtocolProcessor
from app.service.protocol_io.protocol_io_process_task import ProtocolIoProcessor


class JournalProcessorFactory:
    @staticmethod
    def produce(journal_name):
        if journal_name == "protocol_io":
            return ProtocolIoProcessor()
        elif journal_name == "nature_protocol":
            return NatureProtocolProcessor()
        elif journal_name == "current_protocol":
            return CurrentProtocolProcessor()
        else:
            raise ValueError(f"Unknown journal name: {journal_name}")