# Railway/any-container deploy. Build the static site, then serve public/ on $PORT.
# ponytail: python http.server is fine for a low-traffic static open-data site.
#           If traffic grows, swap the CMD for Caddy/nginx or move to Cloudflare Pages.
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN python3 build.py
# shell form so $PORT (set by Railway) expands; http.server binds 0.0.0.0 by default
CMD python3 -m http.server ${PORT:-8080} --directory public
