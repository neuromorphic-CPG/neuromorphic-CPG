from typing import List, Union, Tuple, Iterator, cast

def zip_lists_or_ints(*args : Union[int,List[int]]) -> Iterator[Tuple[int, ...]]:
	'''Zip together ints and lists of ints, to make functions taking chips, cores and ids more flexible'''
	lengths_of_iterables = [len(cast(list,arg)) for arg in args if hasattr(arg, '__len__')]
	if len(lengths_of_iterables) == 0:
		length = 1
	else:
		length = max(lengths_of_iterables)
	return zip(*[[cast(int,arg)] * length if type(arg) == int else cast(List[int],arg) for arg in args])