# How to stop a RabbitMQ publisher missing heartbeats

In response to: https://stackoverflow.com/questions/73111224/connection-to-two-rabbitmq-servers

## Running the project

Since this project depends on RabbitMQ, it's been set up to run two separate
RabbitMQ instances side-by-side, using Docker and Docker Compose. The
instances are called `rabbitmq_upstream` and `rabbitmq_downstream`, for the
consumer to consume from and the publisher to publish to, respectively.

For the RabbitMQ admin UI, `rabbitmq_upstream` exposes port 7001 to `localhost`
and `rabbitmq_downstream` exposes port 9001 to `localhost`. You can log in with
the defaults of `guest` and `guest`.

You should be able to run the project with `docker compose up -d`.

**NOTE**: The consumer
process will fail initially because the RabbitMQ containers take a while to get
going.




## Testing

The easiest way to see what's happening is to open up two terminals:

1. One with `docker compose logs -f` to tail the logs from the two RabbitMQ instances
2. The other with `docker compose run --rm consumer` to start the consumer-publisher process

### The happy path

You'll want to convince yourself that messages are being fowarded correctly,
which you can do by publishing a message to `rabbitmq_upstream`, which you can
do at http://localhost:7001/#/queues/%2F/upstream_queue.

The same message should appear in the consumer logs as well as in `rabbitmq_downstream` at http://localhost:9001.

No messages about missed heartbeats should be appearing in the logs at any given time

![Xnapper-2022-08-01-15 55 37](https://user-images.githubusercontent.com/251402/182153337-2f0ed8d7-c3a9-4fb1-a4b3-59a27a0cf156.png)

### Simulate no heartbeat handling
To simulate the situation where the publisher misses heartbeats, comment out the `while`
loop in `Publisher.run` and uncomment the `pass` to make that method do nothing.
Re-running the consumer with `docker compose run --rm consumer` should produce
a missed heartbeat error in the RabbitMQ logs after about 20 seconds.

```
2022-08-01 12:32:21.442954+00:00 [error] <0.2784.0> missed heartbeats from client, timeout: 10s
```
![Xnapper-2022-08-01-15 57 28](https://user-images.githubusercontent.com/251402/182153539-f699f801-897d-48d2-9dbe-faa87856c684.png)

