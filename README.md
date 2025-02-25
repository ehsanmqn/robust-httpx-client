# ClusterClient

The `ClusterClient` is a Python class designed to manage group creation and deletion across multiple cluster nodes. It uses asynchronous HTTP requests to perform operations on cluster nodes and includes robust retry mechanisms with exponential backoff to handle transient errors (e.g., server error, rate limit exceeded).

## NOTE
The coding challenge has been implemented in two versions:

- **This repository:** Implemented according to principles of the [Eventual Consistency enhanced with Retry Mechanism](#regarding-the-implementation) and includes all coding challenge requirements, such as unit tests, a Dockerfile, and K8s manifests.
- **[Saga version](https://github.com/ehsanmqn/saga-httpx-client):** Utilizes the Saga design pattern.


## Features

- **Group Creation**: Create groups on all cluster nodes and verify their existence.
- **Group Deletion**: Delete groups from all cluster nodes and identify nodes where the deletion failed.
- **Verify Creation**: Verify the existence of a group on a specific host.
- **Retry Mechanism**: Automatically retries operations with exponential backoff in case of failures.
- **Rollback on Failure**: Attempts to rollback group creation if any creation or verification step fails.

## Installation

To use the `ClusterClient`, you need to have `httpx` and `tenacity` installed. You can install these dependencies using pip:

```bash
pip install -r requirements.txt
```

## Usage

### Initialization

Create an instance of the `ClusterClient`:

```python
from cluster_client import ClusterClient

client = ClusterClient()
```

### Configuration

The class accepts a list of host URLs as an input argument. Alternatively, you can provide these URLs through the configuration module or environment variables. Make sure that HOSTS is either defined in the configuration module or set as an environment variable with a list of cluster node URLs.

Provide them as class input:
```python
hosts = [
            'http://localhost:8000',
            'http://localhost:8001',
            'http://localhost:8002',
        ]

client = ClusterClient(hosts=hosts)
```

Define as environment variables:
```bash
export HOSTS="http://node1.example.com,http://node2.example.com,http://node3.example.com"
```

### Creating a Group

To create a group on all cluster nodes:

```python
import asyncio

group_id = "example-group"

async def create_group():
    success = await client.create_group(group_id)
    if success:
        print(f"Group {group_id} created successfully on all hosts.")
    else:
        print(f"Group creation failed.")

asyncio.run(create_group())
```

### Deleting a Group

To delete a group from all cluster nodes:

```python
import asyncio

group_id = "example-group"

async def delete_group():
    undeleted_hosts = await client.delete_group(group_id)
    if not undeleted_hosts:
        print(f"Group {group_id} deleted successfully from all hosts.")
    else:
        print(f"Failed to delete group {group_id} from the following hosts: {undeleted_hosts}")

asyncio.run(delete_group())
```

## Logging

The `ClusterClient` uses Python's standard logging library to log information, warnings, and errors.

## Exception Handling

The class defines two custom exceptions:
- `GroupOperationException`: Raised when group operations fail.
- `RequestErrorException`: Raised for HTTP request errors.

These exceptions are used internally and can be extended for more specific error handling.

## Docker

To build and run Docker image, you would typically use the following commands:

```bash
# Build the Docker image
docker build -t robust-httpx-client .

# Run the Docker container
docker run --network="host" -it --rm robust-httpx-client
```

The image has already been built and pushed to the [Dockerhub repository](https://hub.docker.com/repository/docker/ehsanmgh/robust-httpx-client/general)
## Kubernetes

Kubernetes manifests are available in the `manifest` folder. The `main.py` script is configured to run only once without any triggering options, so using a Pod is sufficient to run the container. Follow these steps to run the Pod:

1. Update the hosts in the `configmap.yaml` file.
2. Apply the configuration using the following commands:

```bash
kubectl apply -f configmap.yaml
kubectl apply -f httpx-client-pod.yaml
```

## Running Tests

To ensure that the `ClusterClient` class functions correctly, there have been provided unit tests and concurrency tests using `pytest`. Follow the instructions below to execute these tests:

### Unit Tests

To run the unit tests for `ClusterClient`, execute the following command:

```bash
# Run unit tests
pytest -s tests/test_client.py 
```

### Concurrency Tests

To run the concurrency tests, which check the behavior of the `ClusterClient` under concurrent scenarios, execute the following command:

```bash
# Run concurrency tests
pytest -s tests/test_concurrency.py
```

These commands will execute the tests and provide detailed output, helping you verify that the `ClusterClient` handles various scenarios and exceptions appropriately, including retries, error handling, and concurrency issues.

## Configuration

The HOSTS list can be configured in the config module to specify the cluster of hosts, or it can be set through environment variables.

```shell
export HOSTS="http://localhost:8000,http://localhost:8001,http://localhost:8002"
```

## Regarding the implementation

ClusterClient is designed to maintain eventual consistency across a cluster of hosts by ensuring that operations (creating or deleting a group) are attempted on each host. If any operation fails, corrective actions are taken to restore the system to a consistent state.

### Eventual Consistency

**Eventual Consistency** means that, given enough time, all nodes in a distributed system will achieve a consistent state. This code aims to maintain eventual consistency across a cluster of hosts by ensuring that operations (creating or deleting a group) are attempted on each host, and if any operation fails, corrective actions are taken to bring the system back to a consistent state.

1. **Consistency During Group Creation:**
   When creating a group (`create_group` method), if the creation fails on any host, a rollback is initiated (`_rollback_creation` method) to delete the group from the hosts where it was successfully created. This ensures that all hosts either have the group created or none of them do, achieving a consistent state.

   After all creation attempts, the there is a creation verification section that verifies if the group was successfully created on each host. This section has implemented to increase consistency across nodes. Although additional GET requests add extra load and can impact system performance, especially under high traffic, they help identify if the creation failed silently or if the POST request was partially successful.
2. **Consistency During Group Deletion:**
   When deleting a group (`delete_group` method), the method ensures that an attempt is made to delete the group from all hosts, regardless of the outcome of each attempt. This ensures that eventually, all hosts will not have the group.
   
   After all deletion attempts, a verification section ensures the group has been successfully deleted from each host. This section is implemented to increase consistency across nodes. Although additional GET requests add extra load and can impact system performance, especially under high traffic, they help identify if the deletion failed silently or if the DELETE request was only partially successful.
### Retry Mechanism

The **Retry Mechanism** involves retrying an operation a specified number of times before giving up, often with an increasing delay between attempts (exponential backoff) to handle transient errors and reduce the load on the system.

1. **Retries on Transient Errors:**
   Both `_create_group_on_host` and `_delete_group_on_host` methods are decorated with `@retry` from the `tenacity` library. This decorator ensures that these methods will retry the operation if a `RequestErrorException` is raised, using an exponential backoff strategy (`wait_exponential`).

2. **Exponential Backoff:**
   The `wait_exponential` parameter specifies that the wait time between retries will grow exponentially, starting with a multiplier of 1 second and capping at 10 seconds. This helps in reducing the likelihood of overwhelming the server with repeated requests in a short time frame.

### Combining Both Techniques

By combining eventual consistency and a retry mechanism, the code ensures that:
- Operations are attempted multiple times to overcome transient failures.
- If an operation cannot be successfully completed on all nodes, compensating actions are taken to maintain a consistent state across the cluster.

### Example Scenario

Consider the following scenario for creating a group:
1. The `create_group` method attempts to create a group on multiple hosts.
2. If the group creation succeeds on some hosts but fails on others, a rollback is initiated to delete the group from the successful hosts.
3. During the group creation on each host, if a transient error occurs (e.g., server error, rate limit exceeded), the operation is retried up to three times with an exponential backoff.

This approach ensures that despite temporary failures and inconsistencies, the system will eventually reach a consistent state where either all hosts have the group or none of them do.