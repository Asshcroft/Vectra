from tasks import test_task

def main():
    result = test_task.delay("Celery is working")
    print("Task sent to Redis")
    print(f"Result id: {result.id}")

if __name__ == "__main__":
    main()
