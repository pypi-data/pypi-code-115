from enum import IntEnum
from typing import List, Tuple
import eval7

RANKS = '23456789TJQKA'
SUITS = 'cdhs'

class HandType(IntEnum):
    STRAIGHTFLUSH = 1
    FOUROFAKIND = 2
    FULLHOUSE = 3
    FLUSH = 4
    STRAIGHT = 5
    THREEOFAKIND = 6
    TWOPAIR = 7
    PAIR = 8
    HIGHCARD = 9
    ERROR = 10

class Range:
    def __init__(self, rangeStr) -> None:
        self.range = eval7.HandRange(rangeStr)

    def is_hand_in_range(self, handCards: Tuple[str]) -> bool:
        evalHand = tuple(map(eval7.Card, sorted(handCards, key=lambda x: RANKS.index(x[0]), reverse=True)))
        rangeHands = [hand[0] for hand in self.range.hands]
        return evalHand in rangeHands

def get_hand_type(cards: List[str]):
    evalCards = list(map(eval7.Card, cards))
    handTypeStr = eval7.handtype(eval7.evaluate(evalCards))
    return hand_str_to_enum(handTypeStr)

def card_num_to_str(card_num: int):
    rank_num = int(card_num / 4)
    suit_num = card_num % 4
    return RANKS[rank_num] + SUITS[suit_num]

def hand_str_to_enum(hand_str: str):
    hand_str_lower = hand_str.lower()
    if hand_str_lower == "high card":
        return HandType(9)
    elif hand_str_lower == "pair":
        return HandType(8)
    elif hand_str_lower == "two pair":
        return HandType(7)
    elif hand_str_lower == "trips":
        return HandType(6)
    elif hand_str_lower == "straight":
        return HandType(5)
    elif hand_str_lower == "flush":
        return HandType(4)
    elif hand_str_lower == "full house":
        return HandType(3)
    elif hand_str_lower == "quads":
        return HandType(2)
    elif hand_str_lower == "straight flush":
        return HandType(1)
    return HandType(10)