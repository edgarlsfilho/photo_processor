## photo-processor

### Description

The aim of the exercise is to orchestrate the generation of thumbnails for a specific set of photos.

### Installation

Prerequisites:  
- Docker  
- Ability to run `make`.

App is bundling Postgres and RabbitMQ instances via Docker, so please stop any local related services to avoid port conflicts. Otherwise you can amend the default port mappings on the docker-compose file.

Start the app:
- `make start`

Create or reset the db schema after booting the app (Has to be called from a separated console):  
- `make db-schema`

Postgres PSQL can be accessed via:
- `make psql`

RabbitMQ management console can be accessed at:  
`http://localhost:15672/`  

Web app can be accessed at:  
`http://localhost:3000/`  

### Features available

#### 1. Endpoint for fetching photos of pending status

- Method: `GET`  
- URL: `/photos/pending`  

Returns photo records in JSON format.

#### 2. Endpoint for triggering the processing of pending photos

- Method: `POST`
- URL: `/photos/process`

Endpoint accepts one or more photo UUIDs as JSON input and send one RabbitMQ message on a queue named `photo-processor` for every photo to be processed.

##### How to make a POST call to the endpoint? 

```
curl --header "Content-Type: application/json" \
  --request POST \
  --data '{"payload": ["785b8531-cf03-4915-9123-3ba6b0a11f51","95b5c6c2-52f7-44c3-8c65-be488b2e44ab"]}' \
  http://localhost:3000/photos/process
```

UUIDs passed to --data parameter come from the result of `/photos/pending` call

#### 3. RabbitMQ consumer

RabbitMQ consumer listening on `photo-proccessor` queue, running on `waldo-app` container alongside the web app. 

