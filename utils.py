from typing import List, Union, Tuple, Iterator, cast

def zip_lists_or_ints(*args : Union[int,List[int]]) -> Iterator[Tuple[int, ...]]:
	'''Zip together ints and lists of ints, to make functions taking chips, cores and ids more flexible'''
	length = max((len(cast(list,arg)) for arg in args if hasattr(arg, '__len__')))
	return zip(*[[cast(int,arg)] * length if type(arg) == int else cast(List[int],arg) for arg in args])