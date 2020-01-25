TAG=hatom

build:
	docker build . --tag=$(TAG)

run:
	docker run --network host $(TAG)
