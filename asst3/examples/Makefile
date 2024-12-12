APP_NAME=tutorial

CC = g++
CFLAGS = -fopenmp -O3 -Wall

OBJS := hello loop sqrt 
all: $(OBJS)
$(APP_NAME): $(OBJS)

%: %.cpp
	$(CC) $(CFLAGS) $^ -o $@

clean:
	rm -vf $(OBJS)

# For a given rule:
# $< = first prerequisite
# $@ = target
# $^ = all prerequisite