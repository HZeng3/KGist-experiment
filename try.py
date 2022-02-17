import sys

def main():
    with open('data/dbpedia.txt', 'r') as f:
        all_data = f.read().split('\n')
    for d in all_data:
        if 'Aristotle' in d and 'Philosopher' in d:
            print(d)
    print("EOF")


if __name__ == '__main__':
    main()