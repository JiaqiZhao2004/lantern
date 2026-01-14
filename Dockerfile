# pull official base image
FROM node:20-alpine

# set working directory
WORKDIR /app

# add `/app/node_modules/.bin` to $PATH
ENV PATH=/app/node_modules/.bin:$PATH
ENV REACT_APP_API_HOST=http://host.docker.internal:8000
# install app dependencies
COPY .npmrc ./
COPY package*.json ./
RUN npm install

# add app
COPY . .

# start app
CMD ["npm", "start"]
