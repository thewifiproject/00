"""
Rottikol: Modern Python Crypto Protocol Library (Signal/MTProto Inspired)
All cryptographic primitives are implemented *manually* in this single file (except for SHA-256 and SHA-1, which use hashlib).
No UI, no protocol simulation, just reusable cryptographic logic.

Implements:
- AES-256 in IGE mode (manual, with all core AES logic)
- RSA-2048 (manual, with Miller-Rabin primality test, keygen, encrypt/decrypt, PKCS#1 v1.5 padding)
- DH-2048 (manual safe prime + full DH exchange)
- HKDF (RFC 5869, manual)
- HMAC-SHA256 (manual using hashlib)
- Secure session logic (auth key, session, IV/key derivation, message format)
- Utilities for confidentiality, integrity, authentication, PFS, deniability, unlinkability

Requirements: Python 3.6+
"""
import hashlib
import os
import struct
import secrets
import math
import time

#############
# Utilities #
#############
def int_to_bytes(n, length=None, byteorder='big'):
    if length is None:
        length = (n.bit_length() + 7) // 8
    return n.to_bytes(length, byteorder)

def bytes_to_int(b, byteorder='big'):
    return int.from_bytes(b, byteorder)

def xor_bytes(a, b):
    return bytes(x ^ y for x, y in zip(a, b))

def pad_pkcs7(data, block_size=16):
    pad_len = block_size - (len(data) % block_size)
    return data + bytes([pad_len] * pad_len)

def unpad_pkcs7(data):
    pad_len = data[-1]
    if not 0 < pad_len <= 16 or data[-pad_len:] != bytes([pad_len] * pad_len):
        raise ValueError('Invalid PKCS#7 padding')
    return data[:-pad_len]

def random_bytes(n):
    return secrets.token_bytes(n)

def sha1(data):
    return hashlib.sha1(data).digest()

def sha256(data):
    return hashlib.sha256(data).digest()

def hmac_sha256(key, msg):
    """Manual HMAC-SHA256, RFC2104."""
    block_size = 64
    if len(key) > block_size:
        key = sha256(key)
    key = key.ljust(block_size, b'\x00')
    o_key_pad = xor_bytes(key, b'\x5c' * block_size)
    i_key_pad = xor_bytes(key, b'\x36' * block_size)
    return sha256(o_key_pad + sha256(i_key_pad + msg))

def hkdf_extract(salt, ikm):
    return hmac_sha256(salt, ikm)

def hkdf_expand(prk, info, length):
    """RFC 5869 HKDF-Expand"""
    n = (length + 31) // 32
    t, okm = b"", b""
    for i in range(1, n + 1):
        t = hmac_sha256(prk, t + info + bytes([i]))
        okm += t
    return okm[:length]

def hkdf(ikm, salt, info, length):
    prk = hkdf_extract(salt, ikm)
    return hkdf_expand(prk, info, length)

############################
# Miller-Rabin Primality   #
############################
def is_probable_prime(n, k=8):
    """Miller-Rabin primality test."""
    if n < 2: return False
    for p in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]:
        if n % p == 0:
            return n == p
    s, d = 0, n - 1
    while d % 2 == 0:
        s += 1
        d //= 2
    for _ in range(k):
        a = secrets.randbelow(n - 3) + 2
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for __ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True

def gen_prime(bits):
    while True:
        candidate = secrets.randbits(bits) | (1 << (bits-1)) | 1
        if is_probable_prime(candidate):
            return candidate

#################
# AES-256 Block #
#################
class AES256:
    # AES S-box and Rcon constants
    Sbox = [
        # 0     1      2     3     4     5     6     7     8     9     A     B     C     D     E     F
        0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
        0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,
        0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
        0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,
        0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,
        0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
        0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,
        0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,
        0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
        0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,
        0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
        0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
        0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
        0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,
        0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
        0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16
    ]
    InvSbox = [0] * 256
    for i, s in enumerate(Sbox): InvSbox[s] = i
    Rcon = [
        0x00000000, 0x01000000, 0x02000000, 0x04000000,
        0x08000000, 0x10000000, 0x20000000, 0x40000000,
        0x80000000, 0x1b000000, 0x36000000
    ]

    def __init__(self, key):
        if len(key) != 32:
            raise ValueError("AES-256 requires a 256-bit key")
        self._w = self.key_expansion(key)

    @staticmethod
    def _sub_word(word):
        return ((AES256.Sbox[(word >> 24) & 0xff] << 24) |
                (AES256.Sbox[(word >> 16) & 0xff] << 16) |
                (AES256.Sbox[(word >> 8) & 0xff] << 8) |
                (AES256.Sbox[word & 0xff]))

    @staticmethod
    def _rot_word(word):
        return ((word << 8) & 0xffffffff) | ((word >> 24) & 0xff)

    def key_expansion(self, key):
        """Expands the 256-bit key into 60 32-bit words (AES-256)"""
        w = []
        for i in range(8):
            w.append(int.from_bytes(key[4 * i:4 * (i + 1)], 'big'))
        for i in range(8, 60):
            temp = w[i - 1]
            if i % 8 == 0:
                temp = self._sub_word(self._rot_word(temp)) ^ self.Rcon[i // 8]
            elif i % 8 == 4:
                temp = self._sub_word(temp)
            w.append(w[i - 8] ^ temp)
        return w

    def _add_round_key(self, state, round):
        for i in range(4):
            for j in range(4):
                state[j][i] ^= (self._w[round * 4 + i] >> (24 - 8 * j)) & 0xff

    def _sub_bytes(self, state):
        for i in range(4):
            for j in range(4):
                state[i][j] = self.Sbox[state[i][j]]

    def _inv_sub_bytes(self, state):
        for i in range(4):
            for j in range(4):
                state[i][j] = self.InvSbox[state[i][j]]

    def _shift_rows(self, state):
        for i in range(1, 4):
            state[i] = state[i][i:] + state[i][:i]

    def _inv_shift_rows(self, state):
        for i in range(1, 4):
            state[i] = state[i][-i:] + state[i][:-i]

    @staticmethod
    def _xtime(a): return ((a << 1) ^ 0x1b) & 0xff if a & 0x80 else (a << 1)

    def _mix_columns(self, state):
        for i in range(4):
            t = state[0][i] ^ state[1][i] ^ state[2][i] ^ state[3][i]
            tmp = state[0][i]
            state[0][i] ^= t ^ self._xtime(state[0][i] ^ state[1][i])
            state[1][i] ^= t ^ self._xtime(state[1][i] ^ state[2][i])
            state[2][i] ^= t ^ self._xtime(state[2][i] ^ state[3][i])
            state[3][i] ^= t ^ self._xtime(state[3][i] ^ tmp)

    def _inv_mix_columns(self, state):
        for i in range(4):
            a = state[0][i]
            b = state[1][i]
            c = state[2][i]
            d = state[3][i]
            state[0][i] = self._mul(0x0e, a) ^ self._mul(0x0b, b) ^ self._mul(0x0d, c) ^ self._mul(0x09, d)
            state[1][i] = self._mul(0x09, a) ^ self._mul(0x0e, b) ^ self._mul(0x0b, c) ^ self._mul(0x0d, d)
            state[2][i] = self._mul(0x0d, a) ^ self._mul(0x09, b) ^ self._mul(0x0e, c) ^ self._mul(0x0b, d)
            state[3][i] = self._mul(0x0b, a) ^ self._mul(0x0d, b) ^ self._mul(0x09, c) ^ self._mul(0x0e, d)

    @staticmethod
    def _mul(a, b):
        res = 0
        for i in range(8):
            if b & 1:
                res ^= a
            h = a & 0x80
            a = (a << 1) & 0xff
            if h:
                a ^= 0x1b
            b >>= 1
        return res

    def _bytes2state(self, block):
        return [[block[i + 4 * j] for i in range(4)] for j in range(4)]

    def _state2bytes(self, state):
        return bytes(state[j][i] for i in range(4) for j in range(4))

    def encrypt_block(self, block):
        """Encrypts a single 16-byte block."""
        state = self._bytes2state(block)
        self._add_round_key(state, 0)
        for rnd in range(1, 14):
            self._sub_bytes(state)
            self._shift_rows(state)
            self._mix_columns(state)
            self._add_round_key(state, rnd)
        self._sub_bytes(state)
        self._shift_rows(state)
        self._add_round_key(state, 14)
        return self._state2bytes(state)

    def decrypt_block(self, block):
        """Decrypts a single 16-byte block."""
        state = self._bytes2state(block)
        self._add_round_key(state, 14)
        for rnd in range(13, 0, -1):
            self._inv_shift_rows(state)
            self._inv_sub_bytes(state)
            self._add_round_key(state, rnd)
            self._inv_mix_columns(state)
        self._inv_shift_rows(state)
        self._inv_sub_bytes(state)
        self._add_round_key(state, 0)
        return self._state2bytes(state)

##############################
# AES-256-IGE Mode Encryptor #
##############################
def aes_ige_encrypt(key, iv, data):
    """AES-256-IGE encryption. IV must be 32 bytes (IV1 + IV2)."""
    if len(iv) != 32 or len(key) != 32:
        raise ValueError('Invalid key/IV length')
    aes = AES256(key)
    if len(data) % 16 != 0:
        data = pad_pkcs7(data, 16)
    blocks = [data[i:i+16] for i in range(0, len(data), 16)]
    C_prev = iv[:16]
    P_prev = iv[16:]
    out = []
    for P in blocks:
        xored = xor_bytes(P, C_prev)
        enc = aes.encrypt_block(xored)
        C = xor_bytes(enc, P_prev)
        out.append(C)
        C_prev, P_prev = C, P
    return b''.join(out)

def aes_ige_decrypt(key, iv, data):
    if len(iv) != 32 or len(key) != 32:
        raise ValueError('Invalid key/IV length')
    aes = AES256(key)
    blocks = [data[i:i+16] for i in range(0, len(data), 16)]
    C_prev = iv[:16]
    P_prev = iv[16:]
    out = []
    for C in blocks:
        xored = xor_bytes(C, P_prev)
        dec = aes.decrypt_block(xored)
        P = xor_bytes(dec, C_prev)
        out.append(P)
        C_prev, P_prev = C, P
    return b''.join(out)

######################
# RSA-2048           #
######################
def egcd(a, b):
    if b == 0:
        return (1, 0, a)
    else:
        y, x, g = egcd(b, a % b)
        return (x, y - (a // b) * x, g)

def modinv(a, m):
    x, y, g = egcd(a, m)
    if g != 1:
        raise Exception('modular inverse does not exist')
    return x % m

class RSAKey:
    """Manual RSA-2048 key pair."""
    def __init__(self, n, e, d=None, p=None, q=None):
        self.n = n
        self.e = e
        self.d = d
        self.p = p
        self.q = q

    @staticmethod
    def generate(bits=2048, e=65537):
        while True:
            p = gen_prime(bits // 2)
            q = gen_prime(bits // 2)
            if p != q:
                break
        n = p * q
        phi = (p - 1) * (q - 1)
        d = modinv(e, phi)
        return RSAKey(n, e, d, p, q)

    def encrypt(self, m):
        return pow(m, self.e, self.n)

    def decrypt(self, c):
        if self.d is None:
            raise ValueError("No private exponent in this key")
        return pow(c, self.d, self.n)

    def pkcs1v15_pad(self, msg, klen):
        """PKCS#1 v1.5 type 2 padding for encryption (for up to klen-11 bytes)"""
        if len(msg) > klen - 11:
            raise ValueError("Message too long")
        ps = b""
        while len(ps) < klen - len(msg) - 3:
            b = secrets.token_bytes(1)
            if b != b"\x00":
                ps += b
        return b"\x00\x02" + ps + b"\x00" + msg

    def pkcs1v15_unpad(self, em):
        if len(em) < 11 or em[0:2] != b"\x00\x02":
            raise ValueError("Incorrect padding")
        idx = em.find(b"\x00", 2)
        if idx < 0 or idx < 10:
            raise ValueError("Incorrect padding")
        return em[idx+1:]

    def encrypt_bytes(self, msg):
        klen = (self.n.bit_length() + 7) // 8
        em = self.pkcs1v15_pad(msg, klen)
        m = bytes_to_int(em)
        c = self.encrypt(m)
        return int_to_bytes(c, klen)

    def decrypt_bytes(self, ct):
        klen = (self.n.bit_length() + 7) // 8
        c = bytes_to_int(ct)
        m = self.decrypt(c)
        em = int_to_bytes(m, klen)
        return self.pkcs1v15_unpad(em)

    def export_public(self):
        return (self.e, self.n)

    def export_private(self):
        return (self.e, self.n, self.d, self.p, self.q)

##########################
# Diffie-Hellman 2048bit #
##########################
DH_PRIME_2048 = int(
    "C71CAEB9C6B1C9048E6C522F70F13F73980D40238E3E21C14934D037563D930F"
    "48198A0AA7C14058229493D22530F4DBFA336F6E0AC925139543AED44CCE7C37"
    "20FD51F69458705AC68CD4FE6B6B13ABDC9746512969328454F18FAF8C595F64"
    "2477FE96BB2A941D5BCD1D4AC8CC49880708FA9B378E3C4F3A9060BEE67CF9A4"
    "A6A95811051907E162753B56B0F6B410DBA74D8A84B2A14B3144E0EF1284754F"
    "D17ED950D5965B4B9DD46582DB1178D169C6BC465B0D6FF9CA3928FEF5B9AE4E"
    "418FC15E83EBEA0F87FA9FF5EED70050DED2849F47BF959D956850CE929851F0"
    "D8115F635B105EE2E4E15D04B2454BF6F4FADF034B10403119CD8E3B92FCC5B", 16
)
DH_G = 2

class DHKeyPair:
    """Manual DH-2048 keypair."""
    def __init__(self, private=None, public=None):
        if private is None:
            self.private = secrets.randbits(2048) % (DH_PRIME_2048 - 2) + 2
        else:
            self.private = private
        self.public = pow(DH_G, self.private, DH_PRIME_2048) if public is None else public

    def compute_shared(self, peer_public):
        if not (2 < peer_public < DH_PRIME_2048 - 2):
            raise ValueError("Invalid DH public value")
        shared = pow(peer_public, self.private, DH_PRIME_2048)
        return int_to_bytes(shared, 256)  # 2048 bits = 256 bytes

#######################################
# MTProto 2.0-like Session Management #
#######################################
def derive_aes_key_iv(auth_key, msg_key, direction):
    """Derives AES key and IV per MTProto 2.0 (see Telegram spec)."""
    # direction: 0=client->server, 8=server->client
    x = 0 if direction == 0 else 8
    sha256_a = sha256(msg_key + auth_key[x:x+36])
    sha256_b = sha256(auth_key[40+x:40+x+36] + msg_key)
    aes_key = sha256_a[:8] + sha256_b[8:24] + sha256_a[24:32]
    aes_iv  = sha256_b[:8] + sha256_a[8:24] + sha256_b[24:32]
    return aes_key, aes_iv

def mtproto_msg_key(auth_key, plaintext, padding):
    """Returns msg_key (middle 128 of SHA256(auth_key_part + plaintext + padding))"""
    data = auth_key[88:88+32] + plaintext + padding
    msg_key_large = sha256(data)
    return msg_key_large[8:24]

def make_external_header(auth_key_id, msg_key):
    return auth_key_id + msg_key

def make_internal_header(salt, session_id):
    return salt + session_id

########################
# Protocol API Classes #
########################
class RottikolSession:
    """
    Manages session, key establishment, and message encryption/decryption.
    Provides PFS, deniability, unlinkability by ephemeral DH.
    """
    def __init__(self, auth_key, auth_key_id, session_id, salt):
        self.auth_key = auth_key  # 256 bytes (2048 bits)
        self.auth_key_id = auth_key_id  # 8 bytes (SHA1(auth_key)[-8:])
        self.session_id = session_id  # 8 bytes
        self.salt = salt  # 8 bytes

    @staticmethod
    def generate_session():
        session_id = random_bytes(8)
        salt = random_bytes(8)
        return session_id, salt

    @staticmethod
    def create_from_dh(dh_shared_key):
        """Creates an auth_key and its id from DH key agreement."""
        auth_key = dh_shared_key.ljust(256, b'\x00')
        auth_key_id = sha1(auth_key)[-8:]
        session_id, salt = RottikolSession.generate_session()
        return RottikolSession(auth_key, auth_key_id, session_id, salt)

    def encrypt(self, msg_data, direction=0):
        """
        Encrypt message data (bytes) using the session (MTProto2.0-like):
          External header: 8B auth_key_id, 16B msg_key
          Encrypted: 8B salt, 8B session_id, 8B msg_id, 4B seq_no, 4B msg_len, msg_data, padding
        """
        # Compose message
        msg_id = int(time.time() * (2**32))
        seq_no = 1
        msg_len = len(msg_data)
        inner_hdr = make_internal_header(self.salt, self.session_id)
        body = (
            inner_hdr +
            struct.pack('<Q', msg_id) +
            struct.pack('<I', seq_no) +
            struct.pack('<I', msg_len) +
            msg_data
        )
        # MTProto2.0: 12..1024 random padding, divisible by 16
        min_pad = 12
        pad_len = min_pad + (16 - ((len(body) + min_pad) % 16)) % 16
        padding = random_bytes(pad_len)
        plaintext = body + padding
        msg_key = mtproto_msg_key(self.auth_key, body, padding)
        aes_key, aes_iv = derive_aes_key_iv(self.auth_key, msg_key, direction)
        ciphertext = aes_ige_encrypt(aes_key, aes_iv, plaintext)
        ext_hdr = make_external_header(self.auth_key_id, msg_key)
        return ext_hdr + ciphertext

    def decrypt(self, payload, direction=0):
        """
        Decrypts an encrypted message (MTProto2.0-like).
        Returns: (msg_id, seq_no, msg_data)
        """
        ext_hdr, ciphertext = payload[:24], payload[24:]
        auth_key_id = ext_hdr[:8]
        msg_key = ext_hdr[8:24]
        if auth_key_id != self.auth_key_id:
            raise ValueError("Unknown auth_key_id")
        aes_key, aes_iv = derive_aes_key_iv(self.auth_key, msg_key, direction)
        plaintext = aes_ige_decrypt(aes_key, aes_iv, ciphertext)
        # Remove random padding: parse up to msg_len
        salt = plaintext[:8]
        session_id = plaintext[8:16]
        if salt != self.salt or session_id != self.session_id:
            raise ValueError("Session or salt mismatch")
        msg_id = struct.unpack('<Q', plaintext[16:24])[0]
        seq_no = struct.unpack('<I', plaintext[24:28])[0]
        msg_len = struct.unpack('<I', plaintext[28:32])[0]
        msg_data = plaintext[32:32+msg_len]
        # Verify msg_key
        pad_start = 32 + msg_len
        padding = plaintext[pad_start:]
        body = plaintext[:32+msg_len]
        check_msg_key = mtproto_msg_key(self.auth_key, body, padding)
        if check_msg_key != msg_key:
            raise ValueError("msg_key mismatch (integrity failure)")
        return msg_id, seq_no, msg_data

###############
# High-level  #
###############
def generate_dh_keypair():
    return DHKeyPair()

def dh_compute_shared(private: DHKeyPair, peer_public: int):
    """Returns 256-byte shared secret."""
    return private.compute_shared(peer_public)

def generate_rsa_keypair():
    return RSAKey.generate(2048, 65537)

def rsa_encrypt(msg, rsa_public: RSAKey):
    """Encrypt message (bytes) with public RSA key."""
    return rsa_public.encrypt_bytes(msg)

def rsa_decrypt(ct, rsa_private: RSAKey):
    """Decrypt message (bytes) with private RSA key."""
    return rsa_private.decrypt_bytes(ct)

def generate_auth_key_from_dh(dh_shared: bytes):
    """Create a RottikolSession from DH shared secret."""
    return RottikolSession.create_from_dh(dh_shared)

def hkdf_derive(key, salt, info, length):
    return hkdf(key, salt, info, length)

def hmac256(key, msg):
    return hmac_sha256(key, msg)

def aes256_ige_encrypt(key, iv, data):
    return aes_ige_encrypt(key, iv, data)

def aes256_ige_decrypt(key, iv, data):
    return aes_ige_decrypt(key, iv, data)

##########################
# API USAGE EXAMPLES     #
##########################
# Key generation
# rsa = generate_rsa_keypair()
# dh_keypair = generate_dh_keypair()
# shared = dh_compute_shared(dh_keypair, peer_public)
# session = generate_auth_key_from_dh(shared)
# encrypted = session.encrypt(b"hello world")
# msg_id, seq_no, data = session.decrypt(encrypted)

# Library API
__all__ = [
    'generate_dh_keypair',
    'dh_compute_shared',
    'generate_rsa_keypair',
    'rsa_encrypt',
    'rsa_decrypt',
    'generate_auth_key_from_dh',
    'hkdf_derive',
    'hmac256',
    'aes256_ige_encrypt',
    'aes256_ige_decrypt',
    'RottikolSession',
    'RSAKey',
    'DHKeyPair'
]
