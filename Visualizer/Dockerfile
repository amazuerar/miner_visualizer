### STAGE 1: Build ###
FROM node:latest AS build
WORKDIR /app
COPY . .
RUN npm install
RUN npm run build --prod

### STAGE 2: Run ###
FROM nginx:alpine AS run
COPY --from=build /app/dist/visualizer /usr/share/nginx/html
