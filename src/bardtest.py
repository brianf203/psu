from bardapi import Bard
import sys
import os

os.environ["_BARD_API_KEY"] = "ZQiodAKRqAHxrofS_0l9-Is1koRvgY0W90Rz2DGSF3-MogukjV_lV5k2AbBFOvA6lmEOZw."

def main():
    print(Bard().get_answer("What does " + sys.argv[1] + " mean in OAI 5G, only reply with one sentence.")['content'])

if __name__ == "__main__":
    main()