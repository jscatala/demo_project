# 2. Redis Streams for Event-Driven Architecture

Date: 2025-11-15

## Status

Accepted

## Context

The application requires an event-driven architecture where:
- API writes vote events
- Consumer processes events asynchronously
- High throughput (potentially many concurrent votes)
- Event persistence (don't lose votes if consumer is down)
- Ability to scale consumers horizontally

Need to choose an event streaming/messaging technology that:
- Works well in Kubernetes
- Provides event persistence
- Supports consumer groups (multiple consumers)
- Minimal operational complexity
- Fast read/write performance

## Decision

Use **Redis Streams** as the event log for vote processing.

**Implementation:**
- API writes vote events to Redis Stream: `XADD votes * option cats timestamp 1234567890`
- Consumer reads from stream with consumer group: `XREADGROUP GROUP processors consumer1`
- Stream persists events until acknowledged
- Redis deployed as StatefulSet in K8s (or managed service)

**Flow:**
```
POST /vote → Redis Stream → K8s Job Consumer → PostgreSQL
                ↓
         [Event Log: votes]
         - option: cats
         - timestamp: ...
```

## Consequences

### Positive
- **Event persistence:** Votes retained even if consumer crashes
- **Consumer groups:** Multiple consumers can process in parallel
- **Ordering guarantees:** Events processed in order per partition
- **Already using Redis:** No new infrastructure (needed for temp storage anyway)
- **Simple operations:** Single Redis instance handles streaming + caching
- **Acknowledgment support:** Exactly-once processing possible with XACK
- **Low latency:** In-memory with optional persistence

### Negative
- **Redis expertise needed:** Streams are more complex than Pub/Sub
- **Memory limits:** Stream size limited by Redis memory (requires trimming strategy)
- **Not a full message broker:** Less features than Kafka/RabbitMQ (no native DLQ)

### Neutral
- **Persistence trade-off:** AOF/RDB configuration impacts performance
- **Stream trimming required:** Need strategy to prevent unbounded growth (MAXLEN)

## Alternatives Considered

### Redis Pub/Sub
- **Pros:** Simpler than Streams, built-in broadcast
- **Rejected:** No persistence (messages lost if subscriber down), no acknowledgments

### Apache Kafka
- **Pros:** Industry standard, robust, high throughput, large ecosystem
- **Rejected:** Operational complexity (ZooKeeper/KRaft), overkill for MVP, harder local setup

### RabbitMQ
- **Pros:** Feature-rich, supports multiple patterns, good dead-letter queue
- **Rejected:** Additional infrastructure, more moving parts, slower than Redis

### Database polling
- **Pros:** Simple, no new infrastructure
- **Rejected:** Inefficient, high latency, tight coupling, scales poorly

## References

- [Redis Streams Introduction](https://redis.io/docs/data-types/streams/)
- [Consumer Groups Documentation](https://redis.io/docs/data-types/streams/#consumer-groups)
- ADR-0001: Kubernetes-Native Deployment
