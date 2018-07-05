all: build

%:
	sudo julia make.jl
	python make.py
