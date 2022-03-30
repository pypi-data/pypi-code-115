import random
def randomInt(fromInt,toInt):
    randomTime = list(str(fromInt))
    index = 0
    while toInt != randomTime[index]:
        index = index + 1
        randomTime.append(fromInt - index)
    return int(random.choice(randomTime))
