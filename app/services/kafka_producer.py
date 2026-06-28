"""Non-blocking Kafka producer with circuit breaker fallback."""
class KafkaProducerService:
    async def send(self, topic: str, payload: dict):
        pass
