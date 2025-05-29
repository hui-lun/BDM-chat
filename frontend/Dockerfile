# FROM node:20-alpine as build-stage
# WORKDIR /app
# COPY package*.json ./
# RUN npm install
# COPY . .
# RUN npm run build

# FROM nginx:alpine as production-stage
# COPY --from=build-stage /app/dist /usr/share/nginx/html
# COPY nginx.conf /etc/nginx/conf.d/default.conf
# EXPOSE 80

# CMD ["nginx", "-g", "daemon off;"]

FROM node:20-alpine as build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine as production-stage

# 建立憑證資料夾
RUN mkdir -p /etc/nginx/ssl

# 複製 build 出來的網站檔案
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 複製 Nginx 設定檔與憑證
COPY nginx.conf /etc/nginx/conf.d/default.conf
# COPY ssl/nginx.crt /etc/nginx/ssl/nginx.crt
# COPY ssl/nginx.key /etc/nginx/ssl/nginx.key
COPY ssl /etc/nginx/ssl

EXPOSE 443
CMD ["nginx", "-g", "daemon off;"]
