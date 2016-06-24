import random
import subprocess
import string
from tempfile import NamedTemporaryFile

secure_modulo = [2048, 4096]

ciphers = [ 'aes128', 'aes192', 'aes256', 'camellia128', 'camellia192', 'camellia256', 'des', 'des3', 'idea']


def gen_rsa(modulus, cipher='aes256', passlen=32):
    if not cipher in ciphers:
        raise CipherException(cipher)
    if passlen < 32:
        passlen = 32
    passphrase = crypto_string(passlen)
    temp = NamedTemporaryFile()
    proc = subprocess.Popen(['openssl', 'genrsa', '-' + cipher, '-passout', 'pass:'+passphrase, '-out', temp.name, modulus], stdout=subprocess.PIPE)
    (out, err) = proc.communicate()
    if err is not None:
        raise SubprocessException('private')
    proc = subprocess.Popen(['openssl', 'rsa', '-in', temp.name, '-passin', 'pass:'+passphrase, '-outform', 'PEM', '-pubout'], stdout=subprocess.PIPE)
    (out, err) = proc.communicate()
    if err is not None or len(out) < 5:
        raise SubprocessException('public')
    public = out.split('\n')[0:-1]
    with open(temp.name, 'r+b') as f:
        private = [line.strip() for line in f]
    del temp
    rsa = {}
    rsa['public'] = public
    rsa['private'] = private
    rsa['passphrase'] = passphrase
    return rsa


def crypto_string(self, size):
    """
    Securely generate a random string of a specified length
    Can include uppercase or lowercase ASCII characters and/or integers

    Keyword arguments:
    length -- desired size of string

    Returns:
    Random string
    """
    # http://stackoverflow.com/a/23728630/1993468
    return ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(size))


class CipherException(Exception):
    def __init__(self, value):
        self.value = str(value)

    def __repr__(self):
        return repr('CipherExcpetion: ' + self.value + ' is not a valid cipher option.')

class SubprocessException(Exception):
    def __init__(self, value):
        self.value = str(value)

    def __repr__(self):
        return repr('SubprocessException: Error generating ' + self.value + ' RSA key!')