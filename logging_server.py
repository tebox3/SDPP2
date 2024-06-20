import logging
from concurrent import futures
import grpc
import logging_pb2
import logging_pb2_grpc

class LoggerService(logging_pb2_grpc.LoggerServiceServicer):
    def __init__(self):
        # Configurar el logger para el servidor
        self.logger = logging.getLogger('central_logger')
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler('central_log.log', mode='a')
        formatter = logging.Formatter('%(asctime)s, %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def Log(self, request, context):
        # Construir el mensaje de log con los campos recibidos
        log_message = f"{request.timestamp}, {request.prefix}, {request.juego}, {request.action}, {request.team_name}, {request.player_name}, {request.roll}"
        self.logger.info(log_message)
        return logging_pb2.LogResponse(status='success')

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    logging_pb2_grpc.add_LoggerServiceServicer_to_server(LoggerService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
