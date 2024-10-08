from __future__ import annotations

import base64
import hashlib
import locale
import os
import pathlib
import random
import secrets
import string
from sqlite3 import Connection, Cursor, Row, sqlite_version_info
from typing import TYPE_CHECKING, Any, Generic, TypeVar

import qrcode
from dotenv import load_dotenv
from qrcode.constants import ERROR_CORRECT_H

if TYPE_CHECKING:
    from PIL import Image

load_dotenv()

KT = TypeVar("KT")
VT = TypeVar("VT")

REGION = "en_IN"

SQLITE_OLD = sqlite_version_info < (3, 35, 0)


class IndexedDict(Generic[KT, VT]):
    def __init__(self, *, case_sensitive: bool = False):
        self.__keys: list[KT] = []
        self.__values: list[VT] = []
        self.__actual_dict: dict[KT, VT] = {}
        self.__index_cache: dict[KT, int] = {}
        self.__size = 0

        self.__case_sensitive = case_sensitive

    def _parse_key(self, key: KT) -> Any:
        """Parse the key based on the case sensitivity.

        >>> d = IndexedDict()
        >>> d._parse_key("hello") == "hello"
        True
        """
        if self.__case_sensitive:
            return key

        return key.casefold() if isinstance(key, str) else key

    def __setitem__(self, key: KT, value: VT) -> None:
        """Set the value for the key.

        >>> d = IndexedDict()
        >>> d["hello"] = "world"
        """

        key = self._parse_key(key)

        if key in self.__actual_dict:
            self.__values[self.__index_cache[key]] = value
            self.__actual_dict[key] = value
        else:
            self.__keys.append(key)
            self.__values.append(value)
            self.__actual_dict[key] = value
            self.__index_cache[key] = self.__size
            self.__size += 1

    def __getitem__(self, key: KT) -> VT:
        """Get the value for the key.

        >>> d = IndexedDict()
        >>> d["hello"] = "world"
        >>> d["hello"]
        'world'
        >>> d[0]
        'world'
        """
        key = self._parse_key(key)

        if key in self.__actual_dict:
            return self.__actual_dict[key]

        if isinstance(key, int):
            return self.__values[int(key)]

        error = f"KeyError: {key}"
        raise KeyError(error)

    def __delitem__(self, key: KT) -> None:
        """Delete the key from the dictionary.

        >>> d = IndexedDict()
        >>> d["hello"] = "world"
        >>> del d["hello"]
        """

        key = self._parse_key(key)
        if key in self.__actual_dict:
            index = self.__index_cache[key]
        elif isinstance(key, int):
            index = int(key)
            key = self.__keys[index]
        else:
            error = f"KeyError: {key}"
            raise KeyError(error)

        del self.__keys[index]
        del self.__values[index]
        del self.__actual_dict[key]
        self.__size -= 1
        self.__index_cache = {k: i for i, k in enumerate(self.__keys)}

    def __len__(self) -> int:
        return self.__size

    def __iter__(self):
        return iter(zip(self.__keys, self.__values))

    def __contains__(self, key: KT) -> bool:
        return key in self.__actual_dict

    def __repr__(self) -> str:
        return repr(self.__actual_dict)

    def items(self):
        return self.__actual_dict.items()

    def keys(self):
        return self.__actual_dict.keys()

    def values(self):
        return self.__actual_dict.values()

    def clear(self) -> None:
        self.__keys.clear()
        self.__values.clear()
        self.__actual_dict.clear()
        self.__index_cache.clear()
        self.__size = 0

    def __getattr__(self, key: KT) -> VT:
        if key in self.__actual_dict:
            return self.__actual_dict[key]

        error = f"AttributeError: {key}"
        raise AttributeError(error)


class Password:
    ITERATIONS = int(os.environ.get("ITERATIONS", 1000))
    ALGORITHM = os.environ.get("ALGORITHM", "sha256")

    def __init__(self, password: str, /) -> None:
        self.__password = password
        self.__salt = int(os.getenv("SALT", 0))
        self.__hashed_password = ""

        self.hash_password()

    def __call__(self) -> str:
        return self.__hashed_password

    @property
    def hex(self) -> str:
        return self.__hashed_password

    @property
    def salt(self) -> int:
        return self.__salt

    @salt.setter
    def salt(self, salt: int) -> None:
        self.__salt = salt
        self.hash_password()

    def set_salt(self, max_length: int = 16) -> None:
        self.__salt = int(secrets.token_hex(max_length), 16)

    def hash_password(self, /) -> None:
        self.__hashed_password = hashlib.pbkdf2_hmac(
            Password.ALGORITHM,
            self.__password.encode("utf-8"),
            self.__salt.to_bytes(16, "big"),
            Password.ITERATIONS,
        ).hex()

    def __eq__(self, other: Password | str):
        if isinstance(other, Password):
            return self.__hashed_password == other.hex
        return (
            self.__hashed_password
            == hashlib.pbkdf2_hmac(
                Password.ALGORITHM,
                other.encode("utf-8"),
                self.__salt.to_bytes(16, "big"),
                Password.ITERATIONS,
            ).hex()
        )

    def __repr__(self) -> str:
        return self.__hashed_password

    def __str__(self) -> str:
        return self.__hashed_password

    @staticmethod
    def random(
        length: int = 16,
        /,
        *,
        contain_lower: bool = True,
        contain_upper: bool = True,
        contain_digits: bool = True,
        contain_punctuation: bool = True,
    ) -> str:
        characters = ""
        if contain_lower:
            characters += string.ascii_lowercase
        if contain_upper:
            characters += string.ascii_uppercase
        if contain_digits:
            characters += string.digits
        if contain_punctuation:
            characters += string.punctuation
        return "".join(random.choices(characters, k=length))

    @staticmethod
    def is_strong(password: str, /) -> bool:
        valids: list[bool] = [
            (any(char.islower() for char in password)),
            (any(char.isupper() for char in password)),
            (any(char.isdigit() for char in password)),
            (any(char in string.punctuation for char in password)),
        ]
        return all(valids) and len(password) >= 8


def sqlite_row_factory(cursor: Cursor, row: Row) -> IndexedDict:
    d = IndexedDict()

    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]

    return d


special_letters = {
    "a": ["á", "à", "â", "ä", "ã", "å", "ā"],
    "b": ["b"],
    "c": ["ç", "ć", "č"],
    "d": ["ď", "ð"],
    "e": ["é", "è", "ê", "ë", "ē", "ė", "ę"],
    "f": ["f"],
    "g": ["ğ"],
    "h": ["ħ"],
    "i": ["í", "ì", "î", "ï", "ī"],
    "j": ["j"],
    "k": ["ķ"],
    "l": ["ł"],
    "m": ["m"],
    "n": ["ñ", "ń"],
    "o": ["ó", "ò", "ô", "ö", "õ", "ō"],
    "p": ["p"],
    "q": ["q"],
    "r": ["ř"],
    "s": ["ś", "š"],
    "t": ["ť"],
    "u": ["ú", "ù", "û", "ü", "ū"],
    "v": ["v"],
    "w": ["w"],
    "x": ["x"],
    "y": ["ý", "ÿ"],
    "z": ["ž", "ź", "ż"],
}


def format_to_special(text: str, /) -> str:
    result = []
    text = text.lower()
    for char in text:
        if char in special_letters:
            result.append(random.choice(special_letters[char]))
        else:
            result.append(char)
    return "".join(result)


def get_product_pictures(product_id: int | str) -> list[str]:
    this_path = pathlib.Path(__file__).parent
    path = this_path / "server" / "static" / "product_pictures" / str(product_id)

    if not path.exists():
        return []

    files = []
    for file in path.iterdir():
        path_from_static = file.relative_to(this_path / "server")
        files.append(f"/{str(path_from_static)}")

    return files


size_chart = {
    "XX-SMALL": {"CHEST": "37''", "LENGTH": "26.5''", "CODE": "1"},
    "X-SMALL": {"CHEST": "39''", "LENGTH": "27''", "CODE": "10"},
    "SMALL": {"CHEST": "41''", "LENGTH": "27.5''", "CODE": "100"},
    "MEDIUM": {"CHEST": "43''", "LENGTH": "28''", "CODE": "1000"},
    "LARGE": {"CHEST": "45''", "LENGTH": "29''", "CODE": "10000"},
    "X-LARGE": {"CHEST": "47''", "LENGTH": "30''", "CODE": "100000"},
    "XX-LARGE": {"CHEST": "51''", "LENGTH": "31''", "CODE": "1000000"},
    "XXX-LARGE": {"CHEST": "53''", "LENGTH": "32''", "CODE": "10000000"},
}

size_names = {
    "1": "XX-SMALL",
    "10": "X-SMALL",
    "100": "SMALL",
    "1000": "MEDIUM",
    "10000": "LARGE",
    "100000": "X-LARGE",
    "1000000": "XX-LARGE",
    "10000000": "XXX-LARGE",
}


def format_number(number: int, /) -> str:
    return locale.format_string("%d", number, grouping=True)


def generate_gift_card_code(k: int = 16) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=k))


def binary_adder(a: str, b: str) -> str:
    return bin(int(a, 2) + int(b, 2))[2:]


class FAQEntity:
    def __init__(self, question: str, answer: str, /) -> None:
        self.question = question
        self.answer = answer


class FAQ:
    def __init__(self, /) -> None:
        self.__faqs: list[FAQEntity] = []

    def add(self, question: str, answer: str, /) -> None:
        self.__faqs.append(FAQEntity(question, answer))

    def get(self) -> list[FAQEntity]:
        return self.__faqs

    def __iter__(self):
        return iter(self.__faqs)

    def __len__(self):
        return len(self.__faqs)


with open("src/server/static/faq.json") as f:
    import json

    faq_data = json.load(f)

faq = FAQ()
for faq_entity in faq_data["faq"]:
    faq.add(faq_entity["question"], faq_entity["answer"])

FAQ_DATA = faq


def newsletter_email_add_to_db(conn: Connection, /, *, email: str) -> None:
    cur = conn.cursor()
    query = "INSERT OR IGNORE INTO NEWSLETTERS (EMAIL) VALUES (?)"

    cur.execute(query, (email,))
    conn.commit()


def backup_sqlite_database(conn: Connection, /, *, path: str = "database-bak.sqlite") -> None:
    backup_path_connection = Connection(path)
    with backup_path_connection:
        conn.backup(backup_path_connection)
    backup_path_connection.close()


class OrderQR:
    BASE62_CHARS = string.digits + string.ascii_lowercase + string.ascii_uppercase
    BASE = len(BASE62_CHARS)

    def __init__(self, /, *, order_id: int) -> None:
        self.__order_id = order_id

    def generate_qr_code(self, /) -> Image.Image:
        text = "QR_" + self.num_to_text(self.__order_id)
        text = base64.b64encode(text.encode("utf-8")).decode("utf-8")
        qr = qrcode.QRCode(
            version=40,
            error_correction=ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(text)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        return img

    def num_to_text(self, num: int):
        if num == 0:
            return OrderQR.BASE62_CHARS[0]

        result = []
        while num > 0:
            remainder = num % OrderQR.BASE
            result.append(OrderQR.BASE62_CHARS[remainder])
            num //= OrderQR.BASE

        return "".join(reversed(result))

    def text_to_num(self, text: str):
        num = 0
        for char in text:
            num = num * OrderQR.BASE + OrderQR.BASE62_CHARS.index(char)

        return num
