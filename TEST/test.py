import re

num = "12.3,54"

if re.match(r'^\d+([.,]?\d+)?$', num):
    print("Y")
else:
    print("N")