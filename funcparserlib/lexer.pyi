from typing import Tuple, Optional, Callable, Iterable, Any, Text, Sequence

_Place = Tuple[int, int]
_Spec = Tuple[Text, Tuple[Any, ...]]

class Token:
    type: Text
    value: Text
    start: Optional[_Place]
    end: Optional[_Place]
    name: Text
    def __init__(
        self,
        type: Text,
        value: Text,
        start: Optional[_Place] = ...,
        end: Optional[_Place] = ...,
    ) -> None: ...
    def pformat(self) -> Text: ...

def make_tokenizer(specs: Sequence[_Spec]) -> Callable[[Text], Iterable[Token]]: ...

class LexerError(Exception):
    place: Tuple[int, int]
    msg: Text
    def __init__(self, place: _Place, msg: Text) -> None: ...
