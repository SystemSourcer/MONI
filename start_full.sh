#!/bin/bash
docker run -it --rm -p 8000:8000 -e TZ=Europe/Berlin -v ./MONI:/workspace moni bash -c 'uvicorn moni.main:app --reload --host 0.0.0.0'