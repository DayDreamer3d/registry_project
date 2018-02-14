# Software Registry Project #

This tiny sample project act as a registry (not a real one) which displays all the tags and fetches the repositories from the backend. It has a simple api with few of endpoints which to add and get the repositories from the backend.


## Installation ##

It is written in python and deployed using docker containers.

1. We have to switch our docker engine to [swarm mode](https://docs.docker.com/engine/swarm/swarm-tutorial/ "swarm mode").
2. Download [project's compose file](https://github.com/DayDreamer3d/registry_project/blob/master/docker-compose.yml "project's compose file") to deploy the stack of services.
3. Switch to the downlaoded directory and execute `docker stack deploy  --compose-file docker-compose.yml softreg` to build the stack. This will download all the necessary images and run the desired services.

## Usage ##

We can avail the project in two ways. First from UI (WIP) and second directly hitting the api endpoints.
Let's look at them both.

### UI ###

After installation, if you access `<host-ip>` it will bring up the ui which would be blank in the starting but would display all the saved tags. For now, it can only do this much don't get your hopes high with it ;)

### Api ###

Api provides endpionts to GET, POST the data to server (no DELETE only constructive !) but to access any of the end points we need to obtain client-key that's our first step.

#### 1. Obtain the client key ####
Please send a `POST` request to `<host-ip>/api/auth/client-key` to obtain the client key.

Result would look like this:

#### 2. Visit the api home page ####
To know about the collection of resources best way to know is to visit this page. It's not too far and have probably the shortest url whihch is `<host-ip>/api?client-key=<client-key>`, it's output would be.

    {
      "client-key-url": "/api/auth/client-key",
      "repos-url": "/api/repos",
      "tags-url": "/api/tags"
    }


#### 3. Add a repository ####
To add new repos (with tags) we have to send a `POST` request to url `<host-ip>/api/repos?client-key=<client-key>` and a request body containing all fields like

    { {
    "name": "usd_dev:v2",
    "description": "Second version of USD in Docker development.",
    "downloads": 250,
    "uri": "usd_dev.v2",
    "tags": [
       "docker usd"
    ]
    }}

resoult would be the url

### 4. Fetch repositories based on tags ###

To get a repository from a backend we have change the request method to `GET`, add tags as query parameters with the same url `<host-ip>/api/repos?client-key=<client-key>&tag=node%20graph%20qt&tag=%22alembic%20file%20format%22`

    {
      "repo_details": [
        {
          "description": "The base of alembic caches.",
          "downloads": 0,
          "name": "alembic-base",
          "tags": [
            "\"alembic file format\"",
            "\"vfx pipeline\""
          ],
          "uri": "alembic-base.v1"
        },
        {
          "description": "Generic Qt Node editor.",
          "downloads": 0,
          "name": "nodes editor",
          "tags": [
            "node graph qt",
            "\"vfx pipeline\""
          ],
          "uri": "nodes_editor.v1"
        }
      ],
      "repo_urls": {
        "alembic-base": "/api/repos/alembic-base",
        "nodes editor": "/api/repos/nodes%20editor"
      }
    }

Please don't hesitate in raising an issue and have fun !
