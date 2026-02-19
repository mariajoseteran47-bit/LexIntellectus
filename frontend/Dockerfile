FROM node:18-alpine

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

# Set backend URL for Next.js rewrites at build time
ENV BACKEND_INTERNAL_URL=http://backend:8000

RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "start"]
