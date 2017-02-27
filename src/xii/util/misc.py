import md5
import itertools

from Crypto.PublicKey import RSA
from concurrent.futures import ThreadPoolExecutor, Future
from functools import partial


def flatten(lists):
    return itertools.chain.from_iterable(lists)

def safe_get(name, structure):
    if name not in structure:
        return None
    return structure[name]


def md5digest(input):
    return md5.new(input).hexdigest()


def generate_rsa_key_pair():
    rsa = RSA.generate(4096)
    pub = rsa.publickey()
    return (rsa.exportKey("PEM"), pub.exportKey("OpenSSH"))


def flatten(to_flatten):
    x = []
    if isinstance(to_flatten, list):
        for i in to_flatten:
            x = x + flatten(i)
        return x
    return [to_flatten]


def in_parallel(worker_count, objects, executor):
    try:
        pool = ThreadPoolExecutor(worker_count)
        futures = map(partial(pool.submit, executor), objects)

        # handle possible errors
        errors = filter(None, map(Future.exception, futures))

        if errors:
            for err in errors:
                raise err
        return map(Future.result, futures)
    finally:
        pool.shutdown(wait=False)


def indented(lx, n):
    if not isinstance(lx, list):
        return (" " * n) + lx
    #FIXME: Make generator after debugging
    x = []
    for l in lx:
        x.append( (" " * n) + l)
    return x
