"""
采集Mongodb 慢查询
"""
from service.mongo_collector import MongoProfileCollectorService


def main():
    mongo_collector = MongoProfileCollectorService()
    # while True:
    mongo_collector.run_once()


if __name__ == '__main__':
    """
    python -m scripts.mongo_profiler_collector
    """
    main()
