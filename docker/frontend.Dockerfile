# Stage 1: build the Vite app
FROM node:20-alpine AS build

WORKDIR /app

COPY system/frontend/package*.json ./
RUN npm ci

COPY system/frontend/ .

# Bake API URL and Mapbox token into the static bundle at build time
# (Vite replaces import.meta.env.VITE_* at build time, not runtime)
ARG VITE_API_URL=http://localhost:8300
ARG VITE_MAPBOX_TOKEN
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_MAPBOX_TOKEN=$VITE_MAPBOX_TOKEN

RUN npm run build

# Stage 2: serve with nginx
FROM nginx:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
