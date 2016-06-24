import random
import subprocess
import string
from tempfile import NamedTemporaryFile

secure_modulo = [2048, 4096]

def gen_rsa(modulus, passlen=32):

    if passlen < 32:
        passlen = 32
    passphrase = crypto_string(passlen)
    temp = NamedTemporaryFile()
    proc = subprocess.Popen(['openssl', 'genrsa', '-des3', '-passout', 'pass:'+passphrase, '-out', temp.name, modulus], stdout=subprocess.PIPE)
    (out, err) = proc.communicate()
    if err is not None:
        raise Exception("Error generating private RSA key!")
    proc = subprocess.Popen(['openssl', 'rsa', '-in', temp.name, '-passin', 'pass:'+passphrase, '-outform', 'PEM', '-pubout'], stdout=subprocess.PIPE)
    (out, err) = proc.communicate()
    if err is not None or len(out) < 5:
        raise Exception("Error generating public RSA key!")
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
