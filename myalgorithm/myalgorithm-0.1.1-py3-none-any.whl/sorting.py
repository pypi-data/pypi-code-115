from _typeshed import SupportsKeysAndGetItem
from typing import TypeVar


def binary_search(li:list,target:int):
	i=0
	j=len(li)-1
	if li[j]==target:
		return j

	while i<j:
		mid =(i+j)//2
		if list[mid]==target:
			return mid
		elif mid<target:
			i=mid+1
		else:
			j=mid
	return -1
from typing import C




T = TypeVar("T")
def merge_sort(li:list[T]) -> list[T]:
    if len(li) <= 1:
        return li
    first, second = li[:len(li)//2], li[len(li)//2:]
    first_sorted = merge_sort(first)
    second_sorted = merge_sort(second)
    print(first_sorted, second_sorted)
    final_answer = []
    i=j=0
    while (i!=len(first_sorted) or j != len(second_sorted)):
        if (i==len(first_sorted)):
            final_answer.append(second_sorted[j])
            j+=1
        elif (j==len(second_sorted)):
            final_answer.append(first_sorted[i])
            i+=1
        else:
            if first_sorted[i] < second_sorted[j]:
                final_answer.append(first_sorted[i])
                i+=1
            else:
                final_answer.append(second_sorted[j])
                j+=1
    return final_answer

def quick_sort(li:list[T]) -> list[T]:
    if len(li)<=1:
        return li
    i=1
    j=len(li)-1
    pivot=0
    while i<=j:
        if li[i]<=li[pivot]:
            i+=1
        elif li[i]>li[pivot] and li[j]<li[pivot]:
            li[i],li[j]=li[j],li[i]
            i+=1
            j-=1
        elif li[j]>=li[pivot]:
            j-=1
    
    li[j],li[pivot]=li[pivot],li[j]
    

    l2=[li[j]]
    l1=quick_sort(li[:j])
    l3=quick_sort(li[j+1:])
    return l1+l2+l3

def bubble_sort(li:list[T]) -> list[T]:
    for i in range(len(li)):
        
        for j in range(len(li)-1):
            l=j+1
            if li[j]>li[l]:
                li[j],li[l]=li[l],li[j]
            
            
    return li:list[T]
def selection_sort(li:list[T]) ->list[T]:
    for i in range(len(li)):
        index=i
        min=li[i]
        for j in range(i,len(li)):
            if li[j]<min:
                min=li[j]
                index=j
        if min<li[i]:
            li[i],li[index]=li[index],li[i]
    return li:list[T]
def insertion_sort(li):
	for i in range(1,len(li)):
		for j in range(i,0,-1):
			if li[j-1]>li[j]:
				li[j-1],li[j]=li[j],li[j-1]
	return li




