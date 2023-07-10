Rivoli


`pip install --editable .`


1. Install mongodb docker container
2. Create records.hash index
  v: 2,
  key: { hash: 1 },
  name: 'hash_1',
  partialFilterExpression: { status: { '$gte': 80 } }
3. Update .env files




### Installation & Execution

# Install docker containers
1. Redis:
  `docker run --name redis -d redis redis-server --save 60 1 --loglevel warning`
2. Mongodb: `

# Webserver
1. Copy `webui/.env.template` to `webui/.env` and modify the configuration variables.
2. Install
2. Create the protobuf definitions with `npm run proto-build`.
3. Run `npm install`
4. Execution: `npm run dev`


# Development Installation Considerations
* Install `redis/redis-stack-server` instead of `redis` provides a web interface.
* Install NPM build tools at `npm build ???`.
*
