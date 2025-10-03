FROM node:20-alpine AS development-dependencies-env
COPY frontend/package.json frontend/package-lock.json /app/
WORKDIR /app
RUN npm ci

FROM node:20-alpine AS production-dependencies-env
COPY frontend/package.json frontend/package-lock.json /app/
WORKDIR /app
RUN npm ci --omit=dev

FROM node:20-alpine AS build-env
# Copy frontend code (without .env files - they're gitignored)
COPY frontend/ /app/
COPY --from=development-dependencies-env /app/node_modules /app/node_modules
WORKDIR /app
RUN npm run build

FROM node:20-alpine
COPY frontend/package.json frontend/package-lock.json /app/
COPY --from=production-dependencies-env /app/node_modules /app/node_modules
COPY --from=build-env /app/build /app/build
WORKDIR /app
CMD ["npm", "run", "start"]