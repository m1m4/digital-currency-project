from Block import Block


# Make the first block of the blockchain
def genesis():
    return Block('void', [], 'mima')


def main():
    b = Block('1', 'abc', 'noam')

    print(str(b))


if __name__ == "__main__":
    main()