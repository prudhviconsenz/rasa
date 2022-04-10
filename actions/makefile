.PHONY:=default build push current
NAME   := prudhviconsenz/rasa
TAG    := $(shell git log -1 --pretty=%h)

default: build push

build:
	docker build -t $(NAME):latest .

push:
	docker tag $(NAME):current $(NAME):$(TAG)
	docker push $(NAME):current
	docker push $(NAME):$(TAG)
