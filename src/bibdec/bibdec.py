import bibtexparser
from bibtexparser.bibdatabase import BibDatabase
from functools import wraps
from copy import copy


class PlaceholderArgument():
    pass


def _format_call_from_kwargs(function, kwargs):
    function_name = f"{function.__module__}.{function.__qualname__}"
    kwarg_str = ", ".join(f"{key}" for key in kwargs)
    return f"{function_name}({kwarg_str})"


def _parse_keys(keys):
    if isinstance(keys, str):
        return {keys}
    if isinstance(keys, dict):
        return set.union(*(_parse_keys(k) for k in keys.values()))
    return set(keys)


class Bibliography:
    def __init__(self, bibliography):
        with open(bibliography, "r") as f:
            self.bibliography = bibtexparser.load(f)
        self.citations = {}
        self.wrapped_functions = []
    
    def __len__(self):
        return len(self.bibliography.entries)

    def _check_validity_of_citation(self, keys, cite_function, wrapped_function):
        if keys is None and cite_function is None:
            raise ValueError("Must supply either set of bibtex keys or citation function.")
        if keys is not None and cite_function is not None:
            raise ValueError("Must supply either set of bibtex keys or citation function, not both.")

        if cite_function is not None:
            # Check that citation function has correct format
            ## Only one keyword only argument: __check_validity__

            # Count number of keyword only arguments
            num_kwonly = cite_function.__code__.co_kwonlyargcount
            kwdefaults = cite_function.__kwdefaults__
            if kwdefaults is None:
                kwdefaults = {}
                
            error_message = (
                f"Citation function `{cite_function.__module__}.{cite_function.__qualname__}` "
                 "should have only one keyword-only argument `__check_validity__` with default value `False`."
            )
            if num_kwonly != 1:
                raise ValueError(error_message)

            if '__check_validity__' not in kwdefaults:
                raise ValueError(error_message)

            if kwdefaults.get('__check_validity__', True):
                raise ValueError("Default value of `__check_validity__` should be False.")

            ## Citation function has same number of arguments as function
            argcount = wrapped_function.__code__.co_argcount + wrapped_function.__code__.co_kwonlyargcount
            if cite_function.__code__.co_argcount != argcount:
                cite_function_name = f"{cite_function.__module__}.{cite_function.__qualname__}"
                function_name = f"{wrapped_function.__module__}.{wrapped_function.__qualname__}"
                raise TypeError(
                    f"Citation function, `{cite_function_name}`, should have the same number "
                    f"of arguments as wrapped function, `{function_name}`.")

            ## All possible citation keys are in the bibliography
            args = (PlaceholderArgument() for _ in range(cite_function.__code__.co_argcount))
            for signature, citation_keys in cite_function(*args, __check_validity__=True).items():
                if isinstance(citation_keys, str):
                    citation_keys = {citation_keys}
                for citation_key in citation_keys:
                    if citation_key not in self.bibliography.entries_dict:
                        signature = f"{wrapped_function.__module__}.{wrapped_function.__qualname__}({signature})"
                        raise ValueError(f"{citation_key} not in bibliography, but occurs for {signature}.")
        
        if keys is not None:
            ## All possible citation keys are in the bibliography
            signature = f'{wrapped_function.__module__}.{wrapped_function.__qualname__}()'
            for citation_key in keys:
                if citation_key not in self.bibliography.entries_dict:
                    raise ValueError(f"{citation_key} not in bibliography, but occurs for {signature}.")

    def cites(self, keys=None, cite_function=None):
        def decorator(f):
            nonlocal self, keys, cite_function
            self.wrapped_functions.append(f)
            if isinstance(keys, str):
                keys = {keys}

            self._check_validity_of_citation(keys, cite_function, f)
            if keys is None:
                keys = set()
            cites = {'': set(keys)}

            @wraps(f)
            def wrapped(*args, **kwargs):
                nonlocal cites
                out = f(*args, **kwargs)

                # Get cites
                if cite_function is not None:
                    cites = cite_function(*args, **kwargs)

                # Update citation dictionary
                if len(cites) == 0:
                    return out
                call_name = _format_call_from_kwargs(f, cites)                
                self.citations[call_name] = _parse_keys(cites)
                return out
            return wrapped
        return decorator

    @property
    def active_bibliography(self):
        active_database = BibDatabase()
        if len(self.citations) == 0:
            return ""
        used_keys = set.union(*self.citations.values())
        active_database.entries = [
            entry 
            for key, entry in self.bibliography.entries_dict.items() 
            if key in used_keys
        ]
        return bibtexparser.dumps(active_database)
