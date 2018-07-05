all: build

%:
	git pull
	sudo julia make.jl
	python make.py
