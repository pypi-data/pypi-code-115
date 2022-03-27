class Sort:
	def __init__(self) -> None:
		pass
	def binary_search(self,li:list,target:int):
		self.li=li
		self.target=target

		i=0
		j=len(self.li)
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
