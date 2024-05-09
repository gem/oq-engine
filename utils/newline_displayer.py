import sys
with open(sys.argv[1], 'rb') as f:
    content = f.read()
    for char_i in content:
        char = chr(char_i)
        if char == '\r':
            sys.stdout.write('[CR]')
        elif char == '\n':
            sys.stdout.write('[LF]\n')
        elif char == '\t':
            sys.stdout.write('[TAB]')
        else:
            sys.stdout.write(char)
