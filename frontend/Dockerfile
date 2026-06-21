FROM node:20-slim AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ARG VITE_API_URL
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_ANON_KEY
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_SUPABASE_URL=$VITE_SUPABASE_URL
ENV VITE_SUPABASE_ANON_KEY=$VITE_SUPABASE_ANON_KEY
RUN npm run build

FROM nginx:alpine
ENV PORT=8080
# Override on Railway: BACKEND_URL=https://your-backend.up.railway.app
ENV BACKEND_URL=http://127.0.0.1:8000
COPY docker-entrypoint.d/40-check-backend-url.sh /docker-entrypoint.d/40-check-backend-url.sh
RUN chmod +x /docker-entrypoint.d/40-check-backend-url.sh
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
CMD ["nginx", "-g", "daemon off;"]
