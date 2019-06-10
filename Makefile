.PHONY: image clean

IMAGE_NAME = actifio:oracle
PYTHON_FILE = $(wildcard Actifio/*.py)
CUR_VERSION = $(shell cat actifio-build-version)

image: 
	docker image build --tag $(IMAGE_NAME) .

clean:
	docker image rm -f $(IMAGE_NAME)

all: image
