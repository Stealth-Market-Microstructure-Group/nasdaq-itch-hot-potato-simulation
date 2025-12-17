research-factory-pipeline/
│── config/
│   └── config.yaml        # choose source (ITCH, Simulator, Scraper), queue type, paths
│
│── cmd/
│   └── ingestor/          # entrypoint for Go ingestor (main.go)
│   └── consumer/          # entrypoint for Python consumer (future Go consumer too)
│
│── internal/
│   ├── parser/            # ITCH parser logic (Go)
│   │    ├── messages.go   # structs for Add Order, Cancel, etc.
│   │    └── parser.go     # parse binary -> structs
│   │
│   ├── publisher/         # Kafka/RabbitMQ publisher
│   │    └── publisher.go
│   │
│   ├── config/            # Go structs to load config.yaml
│   │    └── loader.go
│   │
│   └── utils/             # helpers (logging, error handling, etc.)
│
│── docker/
│   └── docker-compose.yml # spin up Kafka, Zookeeper (or RabbitMQ if chosen)
│
│── scripts/
│   └── consumer.py        # simple Python consumer (using confluent-kafka or pika)
│
│── data/
│   └── 08302019.NASDAQ_ITCH50   # source ITCH file (PoC only)
│
│── go.mod
│── go.sum
│── README.md
