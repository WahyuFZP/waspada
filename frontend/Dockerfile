# Dashboard WASPADA mode produksi (dipakai docker-compose.prod.yml). Di laptop tetap `npm run dev`.
FROM node:24-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# NEXT_PUBLIC_* ditanam ke JavaScript saat build, jadi alamat API publik harus diketahui di sini
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_APK_API_URL
ARG NEXT_PUBLIC_WEB_API_URL
# devDependencies tidak dibuang: `next start` butuh typescript untuk membaca next.config.ts, tanpanya Next mencoba
# memasangnya sendiri saat start (gagal di container read-only)
RUN npm run build

FROM node:24-alpine
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1
COPY --from=build --chown=node:node /app/package.json /app/next.config.ts ./
COPY --from=build --chown=node:node /app/node_modules ./node_modules
COPY --from=build --chown=node:node /app/.next ./.next
USER node
EXPOSE 3000
CMD ["node_modules/.bin/next", "start", "-p", "3000"]
