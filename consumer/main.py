"""
Voting Consumer - Hello World
Event consumer for processing votes from Redis Stream
"""
import time
import sys


def main():
    """Main consumer loop - hello world version"""
    print("Voting Consumer v0.1.0 - Hello World")
    print("Consumer started successfully")
    print("Ready to process vote events (stub)")

    # Keep container alive for testing
    # In real implementation, this will consume from Redis Stream
    try:
        while True:
            print("Consumer running... (waiting for events)")
            time.sleep(30)
    except KeyboardInterrupt:
        print("Consumer shutting down gracefully")
        sys.exit(0)


if __name__ == "__main__":
    main()
