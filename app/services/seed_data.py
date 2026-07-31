"""System design questions and quiz decks seed data."""

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.interview import Question
from app.models.quiz import QuizDeck, QuizQuestion

logger = logging.getLogger(__name__)

INITIAL_QUESTIONS = [
    {
        "id": "q-whatsapp-01",
        "title": "Design WhatsApp / Real-Time Chat System",
        "difficulty": "Senior",
        "time_limit_minutes": 45,
        "expected_topics": ["Load Balancer", "WebSocket", "Database Sharding", "Redis", "Kafka", "Replication"],
        "description": "Design a highly available, real-time messaging system supporting 1 Billion DAU with 1-on-1 and group chats, end-to-end encryption, and offline message queueing.",
        "requirements": [
            "Low latency message delivery (< 100ms globally)",
            "Sent, Delivered, and Read receipts",
            "Group chats up to 1000 participants",
            "Offline storage and reliable sync on reconnect"
        ],
        "constraints": ["1 Billion DAU", "100 Billion messages/day", "Peak QPS 2 Million/sec"],
        "architectural_tips": ["Use Redis Pub/Sub or Kafka for message fanout", "WebSocket connection gateway clusters", "Cassandra or ScyllaDB for chat history"],
        "evaluation_rubric": {
            "requirements": 20,
            "estimation": 15,
            "architecture": 35,
            "data_modeling": 15,
            "scalability": 15
        }
    },
    {
        "id": "q-uber-02",
        "title": "Design Uber / Ride Sharing Platform",
        "difficulty": "Senior",
        "time_limit_minutes": 45,
        "expected_topics": ["Geospatial Indexing", "QuadTrees", "WebSockets", "Consistent Hashing", "Redis GEO"],
        "description": "Design a real-time ride-matching platform matching drivers and riders based on geospatial proximity, routing, and dynamic pricing.",
        "requirements": [
            "Driver location broadcast every 4 seconds",
            "Rider location search within 3km radius",
            "Dynamic trip matching and ETA calculation"
        ],
        "constraints": ["10 Million active drivers", "Peak 500,000 geospatial queries/sec"],
        "architectural_tips": ["Redis GEO (Geohashing) for low-latency driver index", "QuadTree memory buckets with dynamic tile sharding"],
        "evaluation_rubric": {
            "requirements": 20,
            "estimation": 15,
            "architecture": 35,
            "data_modeling": 15,
            "scalability": 15
        }
    },
    {
        "id": "q-netflix-03",
        "title": "Design Netflix / Video Streaming Platform",
        "difficulty": "Intermediate",
        "time_limit_minutes": 45,
        "expected_topics": ["CDN", "Object Storage", "Video Encoding", "Metadata Database", "Caching"],
        "description": "Design a global on-demand video streaming platform supporting adaptive bitrate streaming (HLS/DASH) across heterogeneous client devices.",
        "requirements": [
            "Video ingestion, transcode pipeline, and multi-resolution packaging",
            "Global low-latency video streaming without buffering",
            "Personalized recommendations and search"
        ],
        "constraints": ["250 Million subscribers", "100 Terabits/sec peak egress bandwidth"],
        "architectural_tips": ["Edge CDN caching for video segments", "Amazon S3 object storage", "Asynchronous transcoding job queue"],
        "evaluation_rubric": {
            "requirements": 20,
            "estimation": 15,
            "architecture": 35,
            "data_modeling": 15,
            "scalability": 15
        }
    },
    {
        "id": "q-tinyurl-04",
        "title": "Design TinyURL / URL Shortener Service",
        "difficulty": "Beginner",
        "time_limit_minutes": 30,
        "expected_topics": ["Hash Function", "Base62 Encoding", "Relational DB vs NoSQL", "Cache Eviction", "Rate Limiting"],
        "description": "Design a high-throughput URL shortening service generating short aliases for long URLs with high read-to-write ratio.",
        "requirements": [
            "Generate short 7-character alias (Base62)",
            "HTTP 301/302 redirect to original URL within 20ms",
            "Custom URL aliases and TTL expiration"
        ],
        "constraints": ["100:1 Read to Write ratio", "100 Million new URLs/month", "500 Million redirects/day"],
        "architectural_tips": ["Base62 encoding of 64-bit auto-incrementing ID", "Redis L1 cache with LRU eviction"],
        "evaluation_rubric": {
            "requirements": 20,
            "estimation": 20,
            "architecture": 30,
            "data_modeling": 15,
            "scalability": 15
        }
    },
    {
        "id": "q-cache-05",
        "title": "Design a Distributed In-Memory Cache (Redis Clone)",
        "difficulty": "Staff",
        "time_limit_minutes": 60,
        "expected_topics": ["Consistent Hashing", "LRU/LFU Eviction", "Replication Protocols", "Gossip Protocol", "Memory Management"],
        "description": "Design a distributed, highly available in-memory caching system supporting sub-millisecond gets/sets, consistent hashing, replication, and node discovery.",
        "requirements": [
            "Get and Set latency < 1ms at p99",
            "Consistent Hashing with virtual nodes",
            "Configurable LRU / LFU cache eviction policies",
            "Master-replica asynchronous replication with automatic failover"
        ],
        "constraints": ["10 Terabytes total cache memory", "10 Million QPS cluster throughput"],
        "architectural_tips": ["Virtual node token ring to balance partitions", "Gossip protocol (SWIM) for cluster node health checks"],
        "evaluation_rubric": {
            "requirements": 15,
            "estimation": 15,
            "architecture": 40,
            "data_modeling": 15,
            "scalability": 15
        }
    },
    {
        "id": "q-ratelimiter-06",
        "title": "Design a Distributed Rate Limiter",
        "difficulty": "Senior",
        "time_limit_minutes": 45,
        "expected_topics": ["Sliding Window Counter", "Token Bucket", "Redis Lua Scripts", "Race Conditions", "Edge Gateway Ingress"],
        "description": "Design a distributed rate limiter protecting backend APIs from DDoS attacks and abusive token consumption across globally distributed edge proxies.",
        "requirements": [
            "Atomic rate limiting per IP / User / API Token",
            "Sub-millisecond verification overhead (< 2ms)",
            "Configurable rules per endpoint (e.g. 100 req/min for free, 1000 for pro)"
        ],
        "constraints": ["1 Million requests/sec ingress", "Low memory footprint"],
        "architectural_tips": ["Redis Sorted Sets with Lua script for atomic sliding window log", "In-memory local caching with periodic sync to reduce Redis hops"],
        "evaluation_rubric": {
            "requirements": 20,
            "estimation": 15,
            "architecture": 35,
            "data_modeling": 15,
            "scalability": 15
        }
    }
]

INITIAL_DECKS = [
    {
        "id": "deck-storage-systems",
        "title": "Storage Engine Internals & Databases",
        "description": "Deep dive into LSM-Trees, SSTables, B-Trees, Write-Ahead Logs (WAL), and distributed replication.",
        "difficulty": "senior",
        "question_count": 5,
        "est_minutes": 10,
        "category": "Storage Engine Architecture",
        "icon_name": "Database",
        "questions": [
            {
                "question": "In LSM-Tree based storage engines (e.g. RocksDB, Cassandra), why are Bloom Filters essential for read performance?",
                "scenario": "A read request queries a point lookup for a non-existent key across multiple SSTables on disk.",
                "topic_tag": "Storage Engine Architecture",
                "is_daily": True,
                "options": [
                    {
                        "id": "lsm-o1",
                        "text": "Bloom Filters quickly identify whether a key definitely does NOT exist in an SSTable, preventing costly random disk I/O.",
                        "is_correct": True,
                        "explanation": "LSM trees write sequentially to immutable SSTables. Without Bloom filters, checking for a non-existent key requires scanning every SSTable level on disk. Bloom filters yield zero false negatives."
                    },
                    {
                        "id": "lsm-o2",
                        "text": "Bloom Filters compress SSTables to reduce disk usage by 90%.",
                        "is_correct": False,
                        "explanation": "Bloom filters are probabilistic set-membership data structures, not data compression algorithms."
                    },
                    {
                        "id": "lsm-o3",
                        "text": "Bloom Filters sort records in ascending order in MemTable.",
                        "is_correct": False,
                        "explanation": "SkipLists or Red-Black Trees are used in MemTables for sorting, not Bloom filters."
                    }
                ]
            }
        ]
    },
    {
        "id": "deck-social-feeds",
        "title": "Distributed Sharding & Partitioning",
        "description": "Master Consistent Hashing, Virtual Nodes, Resharding, and Fan-out caching strategies.",
        "difficulty": "senior",
        "question_count": 5,
        "est_minutes": 12,
        "category": "Distributed Sharding",
        "icon_name": "Share2",
        "questions": [
            {
                "question": "How does Consistent Hashing with Virtual Nodes prevent hot-spot imbalances when adding or removing database shards?",
                "scenario": "A distributed database cluster dynamically scales from 16 to 24 nodes under fluctuating holiday traffic.",
                "topic_tag": "Distributed Sharding",
                "is_daily": False,
                "options": [
                    {
                        "id": "ch-o1",
                        "text": "Virtual nodes map each physical machine to multiple hash ring positions, distributing keys uniformly and remapping only K/N keys during resharding.",
                        "is_correct": True,
                        "explanation": "Consistent hashing maps nodes and keys to a 360-degree ring. Virtual nodes (e.g. 256 per server) prevent non-uniform clustering and ensure rebalancing transfers a balanced 1/N slice to the new node."
                    },
                    {
                        "id": "ch-o2",
                        "text": "Virtual nodes duplicate 100% of all data across every node in the cluster.",
                        "is_correct": False,
                        "explanation": "Virtual nodes are virtual tokens on the hash ring, not full cluster replicas."
                    }
                ]
            }
        ]
    },
    {
        "id": "deck-geo-systems",
        "title": "Geospatial Indexing & High-Scale Tracking",
        "description": "Redis GEO, Geohashes, QuadTrees, and spatial radius search optimizations at 1M QPS.",
        "difficulty": "senior",
        "question_count": 4,
        "est_minutes": 8,
        "category": "Geospatial Architecture",
        "icon_name": "MapPin",
        "questions": [
            {
                "question": "When implementing real-time driver location tracking for ride-sharing at 1M QPS, which indexing strategy balances write throughput and spatial queries?",
                "scenario": "1 Million active drivers send GPS coordinate updates every 4 seconds while riders search for nearby drivers within 3 km.",
                "topic_tag": "Geospatial Architecture",
                "is_daily": False,
                "options": [
                    {
                        "id": "geo-o1",
                        "text": "Store current coordinates in Redis GEO / In-Memory Geohash buckets with short TTL, updating memory in O(1) and performing bounding box radius searches.",
                        "is_correct": True,
                        "explanation": "1M updates every 4s = 250,000 writes/sec. In-memory Redis GEO (sorted sets indexed by 52-bit integer geohashes) delivers sub-millisecond point updates and radius queries."
                    },
                    {
                        "id": "geo-o2",
                        "text": "Write every coordinate update to relational PostgreSQL with PostGIS GIST indexes synchronously.",
                        "is_correct": False,
                        "explanation": "250K synchronous disk writes/sec with B-Tree/GIST index updates causes massive disk write amplification and write lock contention."
                    }
                ]
            }
        ]
    },
    {
        "id": "deck-cap",
        "title": "Distributed Consistency & Event Streaming",
        "description": "Transactional Outbox Pattern, Change Data Capture (CDC), Kafka pipelines, and CAP / PACELC trade-offs.",
        "difficulty": "staff",
        "question_count": 6,
        "est_minutes": 15,
        "category": "Distributed Event Streaming",
        "icon_name": "Zap",
        "questions": [
            {
                "question": "Why is the Transactional Outbox Pattern combined with Change Data Capture (CDC) superior to dual-writing to SQL and Kafka in application code?",
                "scenario": "An order service writes order state to PostgreSQL and publishes an OrderCreated event to Apache Kafka.",
                "topic_tag": "Distributed Event Streaming",
                "is_daily": False,
                "options": [
                    {
                        "id": "outbox-o1",
                        "text": "It guarantees atomicity via local ACID transactions; CDC streams events from the WAL to Kafka, eliminating partial failure and dual-write inconsistency.",
                        "is_correct": True,
                        "explanation": "If the app writes to DB and crashes before Kafka publish, or if Kafka publish succeeds but DB commit rolls back, the system enters an inconsistent state. The Outbox pattern writes state and event within the same DB transaction; Debezium/CDC reads the commit log reliably."
                    },
                    {
                        "id": "outbox-o2",
                        "text": "The Outbox pattern eliminates the need for message brokers like Kafka.",
                        "is_correct": False,
                        "explanation": "The Outbox pattern works in conjunction with Kafka to ensure reliable message dispatch."
                    }
                ]
            }
        ]
    }
]


async def seed_database(db: AsyncSession) -> None:
    """Populate system design questions and quiz decks if empty."""
    # Seed questions
    for q_data in INITIAL_QUESTIONS:
        existing = await db.get(Question, q_data["id"])
        if not existing:
            q = Question(**q_data)
            db.add(q)

    # Seed quiz decks & questions
    for deck_data in INITIAL_DECKS:
        deck_dict = dict(deck_data)
        deck_id = deck_dict["id"]
        existing_deck = await db.get(QuizDeck, deck_id)
        if not existing_deck:
            questions_data = deck_dict.pop("questions", [])
            deck_dict["question_count"] = len(questions_data)
            deck = QuizDeck(**deck_dict)
            db.add(deck)
            await db.flush()

            for q_info in questions_data:
                qq = QuizQuestion(deck_id=deck_id, **q_info)
                db.add(qq)

    await db.commit()
    logger.info("Database seeding completed.")
