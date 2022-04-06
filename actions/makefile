.PHONY:=default build push current
NAME   := simonm3a/chatbot
TAG    := $(shell git log -1 --pretty=%h)

default: build push

build:
	docker build -t $(NAME):current .

push:
	docker tag $(NAME):current $(NAME):$(TAG)
	docker push $(NAME):current
	docker push $(NAME):$(TAG)