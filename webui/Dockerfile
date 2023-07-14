FROM node:19

WORKDIR /usr/webbuild

COPY ./src ./src
COPY ./static ./static
COPY buf.gen.yaml ./
COPY package.json ./
COPY package-lock.json ./
COPY svelte.config.js ./
COPY vite.config.ts ./
COPY tsconfig.json ./

COPY build/protos ../protos

RUN npm install && \
    npm run proto-build && \
    npm run build

RUN cp -r build /usr/webui && \
    cp package.json /usr/webui

WORKDIR /usr/webui

RUN npm install

CMD [ "node", "/usr/webui" ]
